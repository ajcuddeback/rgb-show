import json


def test_layout_endpoint_reports_current(client):
    data = client.get("/api/layout").get_json()
    assert data["numPixels"] == 100 and sum(data["rings"]) == 100


def test_change_wraps_only(client):
    res = client.put("/api/layout", json={"rings": [40, 30, 20, 10]})
    assert res.status_code == 200
    assert res.get_json()["config"]["rings"] == [40, 30, 20, 10]


def test_change_pixel_count_rescales_wraps_and_strand(client, controller):
    client.post("/api/animations/solid/start", json={"params": {"color": [255, 0, 0]}})
    res = client.put("/api/layout", json={"numPixels": 150})
    assert res.status_code == 200
    cfg = res.get_json()["config"]
    assert cfg["numPixels"] == 150 and sum(cfg["rings"]) == 150 and len(cfg["rings"]) == 5
    assert controller.num_pixels == 150 and len(controller.pixels) == 150
    # animation restarted on the new strand
    state = res.get_json()
    assert state["power"] and state["animation"] == "solid"
    assert client.get("/api/frame").get_json()["n"] == 150


def test_layout_validation(client):
    assert client.put("/api/layout", json={"numPixels": 100, "rings": [50, 40]}).status_code == 400
    assert client.put("/api/layout", json={"numPixels": 0}).status_code == 400
    assert client.put("/api/layout", json={"rings": [30, 0, 70]}).status_code == 400
    assert client.put("/api/layout", json={"rings": "nope"}).status_code == 400
    # nothing changed
    assert client.get("/api/layout").get_json()["numPixels"] == 100


def test_layout_persists(client, config):
    client.put("/api/layout", json={"numPixels": 60, "rings": [30, 20, 10]})
    with open(config.state_file) as fh:
        saved = json.load(fh)["layout"]
        assert (saved["numPixels"], saved["rings"], saved["source"], saved["points"]) == (60, [30, 20, 10], "wraps", None)
    from app import create_app
    from config import Config
    cfg2 = Config(num_pixels=100, simulate=True, autostart=False, state_file=config.state_file, presets_file=config.presets_file)
    app2 = create_app(cfg2)
    try:
        lay = app2.test_client().get("/api/layout").get_json()
        assert (lay["numPixels"], lay["rings"], lay["source"]) == (60, [30, 20, 10], "wraps")
        assert len(lay["points"]) == 60
    finally:
        app2.extensions["rgb"]["engine"].shutdown()


def test_webmanifest_mimetype(client, tmp_path):
    import app as appmod
    import os
    path = os.path.join(appmod.TEMPLATES_DIR, "manifest.webmanifest")
    if not os.path.exists(path):
        return
    res = client.get("/manifest.webmanifest")
    assert res.status_code == 200
    assert "manifest+json" in res.headers["Content-Type"]
    assert res.headers["Cache-Control"] == "no-cache"


# ------------------------------------------------------------- 3D points
def _cone_points(n=100, missing=()):
    import math
    pts = []
    for i in range(n):
        h = i / (n - 1)
        a = i * 0.37
        r = 1 - 0.85 * h
        pts.append(None if i in missing else [r * math.cos(a) * 3 + 10, r * math.sin(a) * 3 - 4, h * 7 + 100])
    return pts


def test_layout_from_points_normalizes_and_bands():
    from tree import TreeLayout
    tree = TreeLayout.from_points(_cone_points(missing={3, 4, 50, 99}))
    assert tree.n == 100 and tree.source == "camera"
    assert min(tree.z) == 0 and max(tree.z) == 1
    assert max(tree.radius) <= 1.0001
    assert all(0 <= a < 1 for a in tree.angle)
    assert sum(tree.rings) == 100 and tree.num_rings >= 3
    assert sorted(i for r in range(tree.num_rings) for i in tree.pixels_in_ring(r)) == list(range(100))
    # interpolated pixel 3 sits between 2 and 5
    assert tree.z[2] <= tree.z[3] <= tree.z[5]
    assert tree.top_pixels(1) == [tree.order_by_height[-1]]


def test_put_layout_with_points(client, controller):
    client.post("/api/animations/snow/start")
    res = client.put("/api/layout", json={"numPixels": 100, "points": _cone_points(missing={7})})
    assert res.status_code == 200, res.get_json()
    cfg = res.get_json()["config"]
    assert cfg["source"] == "camera" and len(cfg["points"]) == 100 and sum(cfg["rings"]) == 100
    assert res.get_json()["animation"] == "snow" and res.get_json()["power"]
    # bad shapes
    assert client.put("/api/layout", json={"numPixels": 100, "points": _cone_points(50)}).status_code == 400
    assert client.put("/api/layout", json={"numPixels": 100, "points": [None] * 100}).status_code == 400
    assert client.put("/api/layout", json={"numPixels": 100, "points": [[1, 2]] * 100}).status_code == 400
    # back to wraps clears the map
    res = client.put("/api/layout", json={"numPixels": 100, "rings": [50, 30, 20]})
    assert res.get_json()["config"]["source"] == "wraps"


def test_points_persist(client, config):
    client.put("/api/layout", json={"numPixels": 100, "points": _cone_points()})
    from app import create_app
    from config import Config
    app2 = create_app(Config(num_pixels=100, simulate=True, autostart=False, state_file=config.state_file, presets_file=config.presets_file))
    try:
        lay = app2.test_client().get("/api/layout").get_json()
        assert lay["source"] == "camera" and len(lay["points"]) == 100
    finally:
        app2.extensions["rgb"]["engine"].shutdown()


def test_calibration_flow(client, controller):
    import time
    client.post("/api/animations/twinkle/start")
    client.post("/api/brightness", json={"brightness": 0.2})
    res = client.post("/api/calibration/start", json={"brightness": 0.7})
    assert res.get_json() == {"calibrating": True, "numPixels": 100}
    assert controller.brightness == 0.7
    assert all(sum(p) == 0 for p in controller.get_frame())
    assert client.post("/api/calibration/light", json={"index": 42}).status_code == 200
    frame = controller.get_frame()
    assert frame[42] == (255, 255, 255) and sum(sum(p) for i, p in enumerate(frame) if i != 42) == 0
    assert client.post("/api/calibration/light", json={"index": 500}).status_code == 400
    assert client.post("/api/calibration/light", json={"all": True}).status_code == 200
    assert all(p == (255, 255, 255) for p in controller.get_frame())
    assert client.post("/api/calibration/light", json={"index": None}).status_code == 200
    assert all(sum(p) == 0 for p in controller.get_frame())
    state = client.post("/api/calibration/stop").get_json()
    assert state["power"] and state["animation"] == "twinkle" and abs(state["brightness"] - 0.2) < 1e-9
    assert client.post("/api/calibration/light", json={"index": 1}).status_code == 409

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
    frame = client.get("/api/frame").get_json()["pixels"]
    assert len(frame) == 150


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
        assert json.load(fh)["layout"] == {"numPixels": 60, "rings": [30, 20, 10]}
    from app import create_app
    from config import Config
    cfg2 = Config(num_pixels=100, simulate=True, autostart=False, state_file=config.state_file, presets_file=config.presets_file)
    app2 = create_app(cfg2)
    try:
        lay = app2.test_client().get("/api/layout").get_json()
        assert lay == {"numPixels": 60, "rings": [30, 20, 10], "layout": "tree"}
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

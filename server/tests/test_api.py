import json
import os
import time

from config import Config, scale_rings
from tree import TreeLayout
from neopixel_controller import NeoPixelController


def wait_until(pred, timeout=2.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if pred():
            return True
        time.sleep(0.01)
    return pred()


def test_state_and_config(client):
    res = client.get("/api/state")
    assert res.status_code == 200
    data = res.get_json()
    assert data["power"] is False
    assert data["config"]["numPixels"] == 100
    assert sum(data["config"]["rings"]) == 100
    assert data["config"]["simulated"] is True


def test_list_animations(client):
    data = client.get("/api/animations").get_json()
    names = [a["name"] for a in data["animations"]]
    assert "twinkle" in names and "climb" in names and "solid" in names
    assert len(names) >= 20
    twinkle = next(a for a in data["animations"] if a["name"] == "twinkle")
    assert any(p["type"] == "colors" for p in twinkle["params"])


def test_start_animation_lights_the_tree(client, controller):
    res = client.post("/api/animations/solid/start", json={"params": {"color": "#ff0000"}})
    assert res.status_code == 200
    state = res.get_json()
    assert state["power"] is True and state["animation"] == "solid"
    assert state["params"]["color"] == [255, 0, 0]
    assert wait_until(lambda: controller.get_frame()[0] == (255, 0, 0))


def test_default_params_never_send_black(client, controller):
    # The old UI bug: starting an animation with no color chosen turned the lights off.
    res = client.post("/api/animations/solid/start")
    assert res.status_code == 200
    assert wait_until(lambda: any(sum(px) > 0 for px in controller.get_frame()))


def test_switching_animations_quickly_never_hangs(client, controller):
    t0 = time.monotonic()
    for name in ["twinkle", "climb", "meteor", "solid", "fire", "spiral", "snow", "solid"]:
        res = client.post(f"/api/animations/{name}/start")
        assert res.status_code == 200
    assert time.monotonic() - t0 < 5
    assert wait_until(lambda: client.get("/api/state").get_json()["running"])


def test_live_param_update(client, controller):
    client.post("/api/animations/solid/start", json={"params": {"color": [255, 0, 0]}})
    assert wait_until(lambda: controller.get_frame()[0] == (255, 0, 0))
    res = client.patch("/api/params", json={"params": {"color": [0, 0, 255]}})
    assert res.status_code == 200
    assert res.get_json()["params"]["color"] == [0, 0, 255]
    assert wait_until(lambda: controller.get_frame()[0] == (0, 0, 255))


def test_param_update_without_animation_is_409(client):
    assert client.patch("/api/params", json={"params": {"color": [1, 2, 3]}}).status_code == 409


def test_power_toggle_resumes_last_animation(client, controller, engine):
    client.post("/api/animations/pattern/start", json={"params": {"colors": [[255, 0, 0], [0, 255, 0]]}})
    assert wait_until(lambda: controller.get_frame()[1] == (0, 255, 0))
    off = client.post("/api/power", json={"on": False}).get_json()
    assert off["power"] is False and off["animation"] == "pattern"
    assert controller.get_frame()[1] == (0, 0, 0)
    on = client.post("/api/power", json={"on": True}).get_json()
    assert on["power"] is True and on["animation"] == "pattern"
    assert on["params"]["colors"] == [[255, 0, 0], [0, 255, 0]]
    assert wait_until(lambda: controller.get_frame()[1] == (0, 255, 0))


def test_power_on_with_nothing_to_resume_starts_something(client):
    on = client.post("/api/power", json={"on": True}).get_json()
    assert on["power"] is True and on["animation"]


def test_brightness_and_speed(client):
    s = client.post("/api/brightness", json={"brightness": 0.42}).get_json()
    assert abs(s["brightness"] - 0.42) < 1e-6
    s = client.post("/api/speed", json={"speed": 2.5}).get_json()
    assert s["speed"] == 2.5
    assert client.post("/api/brightness", json={"brightness": "x"}).status_code == 400


def test_frame_endpoint(client):
    client.post("/api/animations/solid/start", json={"params": {"color": [10, 20, 30]}})
    assert wait_until(lambda: client.get("/api/frame").get_json()["hex"][:6] == "0a141e")
    data = client.get("/api/frame").get_json()
    assert data["n"] == 100 and len(data["hex"]) == 600


def test_unknown_animation_404(client):
    res = client.post("/api/animations/nope/start")
    assert res.status_code == 404
    assert "error" in res.get_json()


def test_presets_roundtrip(client, config):
    client.post("/api/animations/spiral/start", json={"params": {"stripes": 4}})
    res = client.post("/api/presets", json={"name": "Candy"})
    assert res.status_code == 201
    preset = res.get_json()
    assert preset["animation"] == "spiral" and preset["params"]["stripes"] == 4
    assert os.path.exists(config.presets_file)

    client.post("/api/animations/solid/start")
    applied = client.post(f"/api/presets/{preset['id']}/apply").get_json()
    assert applied["animation"] == "spiral" and applied["params"]["stripes"] == 4

    assert client.get("/api/presets").get_json()["presets"][0]["name"] == "Candy"
    assert client.delete(f"/api/presets/{preset['id']}").status_code == 200
    assert client.get("/api/presets").get_json()["presets"] == []
    assert client.delete(f"/api/presets/{preset['id']}").status_code == 404


def test_state_persists_and_restores(client, config, app):
    client.post("/api/animations/wave/start", json={"params": {"waves": 2}})
    client.post("/api/speed", json={"speed": 1.5})
    with open(config.state_file) as fh:
        saved = json.load(fh)
    assert saved["animation"] == "wave" and saved["params"]["waves"] == 2 and saved["speed"] == 1.5

    from app import create_app
    cfg2 = Config(num_pixels=100, simulate=True, autostart=True,
                  state_file=config.state_file, presets_file=config.presets_file)
    app2 = create_app(cfg2)
    try:
        st = app2.test_client().get("/api/state").get_json()
        assert st["animation"] == "wave" and st["params"]["waves"] == 2 and st["speed"] == 1.5
        assert st["power"] is True
    finally:
        app2.extensions["rgb"]["engine"].shutdown()


def test_ring_scaling():
    assert sum(scale_rings([30, 20, 15, 10, 10, 10, 5], 100)) == 100
    assert scale_rings([30, 20, 15, 10, 10, 10, 5], 100) == [30, 20, 15, 10, 10, 10, 5]
    assert sum(scale_rings([30, 20, 15, 10, 10, 10, 5], 37)) == 37
    assert sum(scale_rings([30, 20, 15, 10, 10, 10, 5], 3)) == 3


def test_configured_rings_are_normalized_to_pixel_count():
    cfg = Config(num_pixels=100, rings=[40, 30, 20])
    assert sum(cfg.resolved_rings()) == 100
    cfg = Config(num_pixels=50, rings=[40, 30, 20])
    assert sum(cfg.resolved_rings()) == 50


def test_tree_layout_geometry():
    tree = TreeLayout([30, 20, 15, 10, 10, 10, 5])
    assert tree.n == 100 and tree.num_rings == 7
    assert tree.height[0] == 0 and tree.height[-1] == 1
    assert tree.ring_of[29] == 0 and tree.ring_of[30] == 1
    assert list(tree.pixels_in_ring(6)) == list(range(95, 100))
    assert all(0 <= a < 1 for a in tree.angle)


def test_gamma_is_applied_to_hardware_but_not_preview():
    c = NeoPixelController(3, simulate=True, gamma=2.2)
    c.show_frame([(128, 128, 128)] * 3)
    assert c.pixels[0][0] < 128
    assert c.get_frame()[0] == (128, 128, 128)
    c2 = NeoPixelController(3, simulate=True, gamma=1.0)
    c2.show_frame([(128, 128, 128)] * 3)
    assert c2.pixels[0] == (128, 128, 128)


def test_default_layout_is_five_tapering_wraps():
    rings = Config(num_pixels=100).resolved_rings()
    assert rings == [32, 26, 20, 14, 8]
    assert all(a > b for a, b in zip(rings, rings[1:]))
    assert len(Config(num_pixels=50).resolved_rings()) == 5

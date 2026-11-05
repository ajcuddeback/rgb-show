"""Home Assistant bridge logic, exercised against the real Flask app via its test client."""
import json

import pytest

from ha_bridge import Bridge, TreeApi


class FlaskSession:
    """Adapts Flask's test client to the requests-like interface TreeApi expects."""

    def __init__(self, client):
        self.c = client

    def get(self, url, **kw): return self.c.get(url)
    def post(self, url, json=None, **kw): return self.c.post(url, json=json if json is not None else {})
    def patch(self, url, json=None, **kw): return self.c.patch(url, json=json)


@pytest.fixture
def bridge(client):
    published = []
    api = TreeApi("", session=FlaskSession(client))
    b = Bridge(api, lambda topic, payload, retain: published.append((topic, payload, retain)))
    b.refresh_catalog()
    b.published = published
    return b


def test_discovery_payloads(bridge):
    msgs = dict(bridge.discovery_messages())
    light = msgs["homeassistant/light/rgb_show_tree/config"]
    assert light["schema"] == "json" and light["brightness"] and light["effect"]
    assert "Twinkle" in light["effect_list"] and len(light["effect_list"]) >= 30
    assert light["supported_color_modes"] == ["rgb"]
    assert light["device"]["identifiers"] == ["rgb_show_tree"]
    assert "homeassistant/select/rgb_show_tree_preset/config" in msgs
    assert "homeassistant/number/rgb_show_tree_speed/config" in msgs
    assert "homeassistant/button/rgb_show_tree_surprise/config" in msgs
    bridge.publish_discovery()
    topics = [t for t, _, _ in bridge.published]
    assert bridge.availability_topic in topics
    assert all(retain for _, _, retain in bridge.published)


def test_light_on_with_effect_color_brightness(bridge, controller):
    state = bridge.handle_command(bridge.light_command_topic, json.dumps({
        "state": "ON", "effect": "Solid Color", "color": {"r": 0, "g": 0, "b": 255}, "brightness": 128,
    }))
    assert state["power"] and state["animation"] == "solid"
    assert state["params"]["color"] == [0, 0, 255]
    assert abs(state["brightness"] - 128 / 255) < 1e-6
    payloads = bridge.state_payloads(state)
    light = json.loads(payloads[bridge.light_state_topic])
    assert light == {"state": "ON", "brightness": 128, "color_mode": "rgb",
                     "color": {"r": 0, "g": 0, "b": 255}, "effect": "Solid Color"}
    assert payloads[bridge.speed_state_topic] == "1.00"


def test_color_on_multicolor_effect_sets_colors_list(bridge):
    state = bridge.handle_command(bridge.light_command_topic, json.dumps({
        "state": "ON", "effect": "Twinkle", "color": {"r": 255, "g": 0, "b": 0}}))
    assert state["animation"] == "twinkle"
    assert state["params"]["colors"] == [[255, 0, 0]]
    assert state["params"]["background"] != [255, 0, 0]   # background is never treated as "the" color


def test_color_only_live_updates_current_animation(bridge):
    bridge.handle_command(bridge.light_command_topic, json.dumps({"state": "ON", "effect": "Sparkle"}))
    state = bridge.handle_command(bridge.light_command_topic, json.dumps({
        "state": "ON", "color": {"r": 10, "g": 20, "b": 30}}))
    assert state["animation"] == "sparkle" and state["params"]["color"] == [10, 20, 30]


def test_off_then_on_resumes(bridge):
    bridge.handle_command(bridge.light_command_topic, json.dumps({"state": "ON", "effect": "Fireplace"}))
    off = bridge.handle_command(bridge.light_command_topic, json.dumps({"state": "OFF"}))
    assert off["power"] is False
    assert json.loads(bridge.state_payloads(off)[bridge.light_state_topic])["state"] == "OFF"
    on = bridge.handle_command(bridge.light_command_topic, json.dumps({"state": "ON"}))
    assert on["power"] is True and on["animation"] == "fire"


def test_on_with_no_history_lights_something(bridge):
    on = bridge.handle_command(bridge.light_command_topic, json.dumps({"state": "ON"}))
    assert on["power"] is True and on["animation"]


def test_speed_and_surprise(bridge):
    state = bridge.handle_command(bridge.speed_command_topic, "2.5")
    assert state["speed"] == 2.5
    state = bridge.handle_command(bridge.surprise_command_topic, "PRESS")
    assert state["power"] and state["animation"] in [a["name"] for a in bridge.animations]


def test_presets_select(bridge, client):
    client.post("/api/animations/spiral/start", json={"params": {"stripes": 3}})
    created = client.post("/api/presets", json={"name": "Stripes"}).get_json()
    bridge.handle_command(bridge.light_command_topic, json.dumps({"state": "ON", "effect": "Solid Color"}))
    # select discovers the new preset lazily
    state = bridge.handle_command(bridge.preset_command_topic, "Stripes")
    assert state["animation"] == "spiral" and state["params"]["stripes"] == 3
    assert bridge.state_payloads(state)[bridge.preset_state_topic] == "Stripes"
    assert created["name"] in dict(bridge.discovery_messages())["homeassistant/select/rgb_show_tree_preset/config"]["options"]
    assert bridge.handle_command(bridge.preset_command_topic, Bridge.NO_PRESET) is None


def test_bad_payloads_do_not_raise(bridge):
    assert bridge.handle_command(bridge.light_command_topic, "not json") is None
    assert bridge.handle_command(bridge.speed_command_topic, "fast") is None
    assert bridge.handle_command(bridge.light_command_topic, json.dumps({"state": "ON", "effect": "Nope"}))["power"]


def test_publish_state_only_on_change(bridge):
    bridge.publish_state()
    n = len(bridge.published)
    bridge.publish_state()
    assert len(bridge.published) == n
    bridge.handle_command(bridge.speed_command_topic, "3")
    bridge.publish_state()
    assert len(bridge.published) > n

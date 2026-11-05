#!/usr/bin/env python3
# Home Assistant bridge
# Author: Austin Cuddeback (ajcuddeback@gmail.com)
#
# A small standalone service that exposes the tree to Home Assistant through
# MQTT discovery. Nothing to configure on the HA side: once this is running and
# pointed at your broker, HA shows a "Christmas Tree" device with
#
#   light.christmas_tree   on/off, brightness, RGB color, effect list = all animations
#   select.*_preset        apply one of your saved presets
#   number.*_speed         the global speed multiplier
#   button.*_surprise_me   start a random animation
#
# It talks to the rgb-show HTTP API (default http://127.0.0.1:8000) and never
# touches the hardware itself, so it can run anywhere that can reach both.
#
# Configure with environment variables (see deploy/ha.env.example):
#   MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASSWORD, MQTT_TLS
#   RGB_API_URL, HA_DEVICE_NAME, HA_DISCOVERY_PREFIX, MQTT_TOPIC_PREFIX, POLL_SECONDS

import json
import logging
import os
import random
import signal
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

log = logging.getLogger("rgb-show-ha")

VERSION = "2.0"


# --------------------------------------------------------------------------- API
class TreeApi:
    """Thin wrapper over the rgb-show HTTP API. Anything with .get/.post/.patch works."""

    def __init__(self, base_url: str, session=None, timeout: float = 5.0):
        self.base = base_url.rstrip("/")
        self.timeout = timeout
        if session is None:
            import requests
            session = requests.Session()
        self.s = session

    def _req(self, method: str, path: str, body: Optional[dict] = None) -> dict:
        fn = getattr(self.s, method)
        kwargs = {"timeout": self.timeout} if "requests" in type(self.s).__module__ else {}
        res = fn(self.base + path, json=body, **kwargs) if body is not None else fn(self.base + path, **kwargs)
        status = getattr(res, "status_code", 200)
        data = res.json() if callable(getattr(res, "json", None)) else res.get_json()
        if status >= 400:
            raise RuntimeError(f"{method.upper()} {path} -> {status}: {data}")
        return data or {}

    def state(self) -> dict: return self._req("get", "/api/state")
    def animations(self) -> List[dict]: return self._req("get", "/api/animations").get("animations", [])
    def presets(self) -> List[dict]: return self._req("get", "/api/presets").get("presets", [])
    def start(self, name: str, params: Optional[dict] = None) -> dict:
        return self._req("post", f"/api/animations/{name}/start", {"params": params} if params else {})
    def patch_params(self, params: dict) -> dict: return self._req("patch", "/api/params", {"params": params})
    def power(self, on: bool) -> dict: return self._req("post", "/api/power", {"on": on})
    def brightness(self, b: float) -> dict: return self._req("post", "/api/brightness", {"brightness": b})
    def speed(self, s: float) -> dict: return self._req("post", "/api/speed", {"speed": s})
    def apply_preset(self, preset_id: str) -> dict: return self._req("post", f"/api/presets/{preset_id}/apply", {})


# ------------------------------------------------------------------------ Bridge
class Bridge:
    """Pure logic: builds discovery payloads, translates MQTT commands to API calls, builds state."""

    NO_PRESET = "— none —"

    def __init__(self, api: TreeApi, publish: Callable[[str, str, bool], None],
                 device_name: str = "Christmas Tree", node_id: str = "rgb_show_tree",
                 discovery_prefix: str = "homeassistant", topic_prefix: str = "rgb_show/tree",
                 configuration_url: Optional[str] = None):
        self.api = api
        self.publish = publish
        self.device_name = device_name
        self.node_id = node_id
        self.dp = discovery_prefix.rstrip("/")
        self.tp = topic_prefix.rstrip("/")
        self.configuration_url = configuration_url
        self.animations: List[dict] = []
        self.presets: List[dict] = []
        self._last_state_json: Optional[str] = None

    # topics
    @property
    def availability_topic(self): return f"{self.tp}/availability"
    @property
    def light_state_topic(self): return f"{self.tp}/light/state"
    @property
    def light_command_topic(self): return f"{self.tp}/light/set"
    @property
    def preset_state_topic(self): return f"{self.tp}/preset/state"
    @property
    def preset_command_topic(self): return f"{self.tp}/preset/set"
    @property
    def speed_state_topic(self): return f"{self.tp}/speed/state"
    @property
    def speed_command_topic(self): return f"{self.tp}/speed/set"
    @property
    def surprise_command_topic(self): return f"{self.tp}/surprise/press"

    def command_topics(self) -> List[str]:
        return [self.light_command_topic, self.preset_command_topic,
                self.speed_command_topic, self.surprise_command_topic]

    # ------------------------------------------------------------- discovery
    def refresh_catalog(self) -> None:
        self.animations = self.api.animations()
        self.presets = self.api.presets()

    def _device(self) -> dict:
        d = {
            "identifiers": [self.node_id],
            "name": self.device_name,
            "manufacturer": "ajcuddeback",
            "model": "rgb-show",
            "sw_version": VERSION,
        }
        if self.configuration_url:
            d["configuration_url"] = self.configuration_url
        return d

    def discovery_messages(self) -> List[Tuple[str, dict]]:
        base = {"device": self._device(), "availability_topic": self.availability_topic}
        light = {
            **base,
            "name": None,  # inherit device name -> light.christmas_tree
            "unique_id": f"{self.node_id}_light",
            "schema": "json",
            "state_topic": self.light_state_topic,
            "command_topic": self.light_command_topic,
            "brightness": True,
            "brightness_scale": 255,
            "supported_color_modes": ["rgb"],
            "effect": True,
            "effect_list": [a["label"] for a in self.animations],
            "optimistic": False,
            "icon": "mdi:pine-tree",
        }
        preset = {
            **base,
            "name": "Preset",
            "unique_id": f"{self.node_id}_preset",
            "state_topic": self.preset_state_topic,
            "command_topic": self.preset_command_topic,
            "options": [self.NO_PRESET] + [p["name"] for p in self.presets],
            "icon": "mdi:star-outline",
        }
        speed = {
            **base,
            "name": "Speed",
            "unique_id": f"{self.node_id}_speed",
            "state_topic": self.speed_state_topic,
            "command_topic": self.speed_command_topic,
            "min": 0.25, "max": 4, "step": 0.05, "mode": "slider",
            "unit_of_measurement": "x",
            "icon": "mdi:speedometer",
        }
        surprise = {
            **base,
            "name": "Surprise me",
            "unique_id": f"{self.node_id}_surprise",
            "command_topic": self.surprise_command_topic,
            "payload_press": "PRESS",
            "icon": "mdi:shuffle-variant",
        }
        return [
            (f"{self.dp}/light/{self.node_id}/config", light),
            (f"{self.dp}/select/{self.node_id}_preset/config", preset),
            (f"{self.dp}/number/{self.node_id}_speed/config", speed),
            (f"{self.dp}/button/{self.node_id}_surprise/config", surprise),
        ]

    def publish_discovery(self) -> None:
        self.refresh_catalog()
        for topic, payload in self.discovery_messages():
            self.publish(topic, json.dumps(payload), True)
        self.publish(self.availability_topic, "online", True)
        log.info("Published discovery for %d animations, %d presets", len(self.animations), len(self.presets))

    # ----------------------------------------------------------------- state
    def _label(self, name: Optional[str]) -> Optional[str]:
        for a in self.animations:
            if a["name"] == name:
                return a["label"]
        return name

    def _name_for_label(self, label: str) -> Optional[str]:
        for a in self.animations:
            if a["label"].lower() == label.lower() or a["name"] == label:
                return a["name"]
        return None

    def _schema(self, name: Optional[str]) -> List[dict]:
        for a in self.animations:
            if a["name"] == name:
                return a["params"]
        return []

    @staticmethod
    def _primary_color(params: dict, schema: List[dict]) -> Optional[List[int]]:
        for p in schema:
            v = params.get(p["key"])
            if p["type"] == "color" and isinstance(v, list) and len(v) == 3:
                return [int(c) for c in v]
        for p in schema:
            v = params.get(p["key"])
            if p["type"] == "colors" and isinstance(v, list) and v and isinstance(v[0], list):
                return [int(c) for c in v[0]]
        return None

    def state_payloads(self, state: dict) -> Dict[str, str]:
        schema = self._schema(state.get("animation"))
        color = self._primary_color(state.get("params") or {}, schema) or [255, 255, 255]
        light = {
            "state": "ON" if state.get("power") else "OFF",
            "brightness": int(round(float(state.get("brightness", 0)) * 255)),
            "color_mode": "rgb",
            "color": {"r": color[0], "g": color[1], "b": color[2]},
        }
        label = self._label(state.get("animation"))
        if label:
            light["effect"] = label

        preset_name = self.NO_PRESET
        for p in self.presets:
            if p["animation"] == state.get("animation") and p.get("params") == state.get("params"):
                preset_name = p["name"]
                break

        return {
            self.light_state_topic: json.dumps(light),
            self.preset_state_topic: preset_name,
            self.speed_state_topic: f"{float(state.get('speed', 1)):.2f}",
        }

    def publish_state(self, state: Optional[dict] = None, force: bool = False) -> None:
        state = state or self.api.state()
        payloads = self.state_payloads(state)
        blob = json.dumps(payloads, sort_keys=True)
        if force or blob != self._last_state_json:
            self._last_state_json = blob
            for topic, payload in payloads.items():
                self.publish(topic, payload, True)

    # -------------------------------------------------------------- commands
    def handle_command(self, topic: str, payload: str) -> Optional[dict]:
        """Translate an MQTT command into API calls. Returns the resulting state (or None)."""
        payload = (payload or "").strip()
        try:
            if topic == self.light_command_topic:
                return self._handle_light(json.loads(payload or "{}"))
            if topic == self.preset_command_topic:
                return self._handle_preset(payload)
            if topic == self.speed_command_topic:
                return self.api.speed(float(payload))
            if topic == self.surprise_command_topic:
                choice = random.choice([a["name"] for a in self.animations] or ["twinkle"])
                return self.api.start(choice)
        except Exception as exc:  # keep the bridge alive on bad payloads / API hiccups
            log.warning("Command on %s failed: %s", topic, exc)
        return None

    def _handle_light(self, cmd: dict) -> dict:
        state = None
        if cmd.get("state") == "OFF":
            return self.api.power(False)

        if "brightness" in cmd:
            state = self.api.brightness(max(0.0, min(1.0, float(cmd["brightness"]) / 255.0)))

        effect_name = self._name_for_label(cmd["effect"]) if cmd.get("effect") else None
        color = cmd.get("color")
        rgb = [int(color.get("r", 0)), int(color.get("g", 0)), int(color.get("b", 0))] if isinstance(color, dict) else None

        if effect_name:
            params = self._color_params(effect_name, rgb) if rgb else None
            state = self.api.start(effect_name, params)
        elif rgb:
            current = self.api.state()
            name = current.get("animation")
            params = self._color_params(name, rgb) if name else None
            if name and params and current.get("power"):
                state = self.api.patch_params(params)
            elif name and params:
                state = self.api.start(name, {**(current.get("params") or {}), **params})
            else:
                state = self.api.start("solid", {"color": rgb})
        elif cmd.get("state") == "ON":
            current = state or self.api.state()
            if not current.get("power"):
                state = self.api.power(True)
        return state or self.api.state()

    def _color_params(self, name: str, rgb: List[int]) -> Optional[dict]:
        schema = self._schema(name)
        for p in schema:
            if p["type"] == "color" and p["key"] != "background":
                return {p["key"]: rgb}
        for p in schema:
            if p["type"] == "colors":
                return {p["key"]: [rgb]}
        for p in schema:
            if p["type"] == "color":
                return {p["key"]: rgb}
        return None

    def _handle_preset(self, name: str) -> Optional[dict]:
        if name == self.NO_PRESET:
            return None
        for p in self.presets:
            if p["name"] == name:
                return self.api.apply_preset(p["id"])
        self.presets = self.api.presets()  # maybe it was just created
        for p in self.presets:
            if p["name"] == name:
                return self.api.apply_preset(p["id"])
        log.warning("Unknown preset %r", name)
        return None


# ------------------------------------------------------------------------- MQTT
def run_forever() -> None:
    import paho.mqtt.client as mqtt

    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    host = os.environ.get("MQTT_HOST", "homeassistant.local")
    port = int(os.environ.get("MQTT_PORT", "1883"))
    user = os.environ.get("MQTT_USER") or None
    password = os.environ.get("MQTT_PASSWORD") or None
    use_tls = os.environ.get("MQTT_TLS", "0") == "1"
    api_url = os.environ.get("RGB_API_URL", "http://127.0.0.1:8000")
    poll = float(os.environ.get("POLL_SECONDS", "2"))

    api = TreeApi(api_url)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=os.environ.get("MQTT_CLIENT_ID", "rgb-show-ha"))
    if user:
        client.username_pw_set(user, password)
    if use_tls:
        client.tls_set()

    def publish(topic: str, payload: str, retain: bool) -> None:
        client.publish(topic, payload, qos=1, retain=retain)

    bridge = Bridge(
        api, publish,
        device_name=os.environ.get("HA_DEVICE_NAME", "Christmas Tree"),
        node_id=os.environ.get("HA_NODE_ID", "rgb_show_tree"),
        discovery_prefix=os.environ.get("HA_DISCOVERY_PREFIX", "homeassistant"),
        topic_prefix=os.environ.get("MQTT_TOPIC_PREFIX", "rgb_show/tree"),
        configuration_url=os.environ.get("RGB_PUBLIC_URL") or None,
    )
    client.will_set(bridge.availability_topic, "offline", qos=1, retain=True)

    lock = threading.Lock()

    def on_connect(c, userdata, flags, reason_code, properties=None):
        log.info("Connected to MQTT %s:%s (%s)", host, port, reason_code)
        for t in bridge.command_topics():
            c.subscribe(t, qos=1)
        c.subscribe(f"{bridge.dp}/status")   # HA birth message -> republish discovery
        with lock:
            bridge.publish_discovery()
            bridge.publish_state(force=True)

    def on_message(c, userdata, msg):
        payload = msg.payload.decode("utf-8", "replace")
        with lock:
            if msg.topic == f"{bridge.dp}/status":
                if payload.strip().lower() == "online":
                    bridge.publish_discovery()
                    bridge.publish_state(force=True)
                return
            log.info("Command %s %s", msg.topic, payload[:120])
            state = bridge.handle_command(msg.topic, payload)
            try:
                bridge.publish_state(state, force=True)
            except Exception as exc:
                log.warning("State publish failed: %s", exc)

    def on_disconnect(c, userdata, flags, reason_code, properties=None):
        log.warning("MQTT disconnected (%s); reconnecting", reason_code)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())

    # Wait for the tree API to come up (we usually start right after it)
    while not stop.is_set():
        try:
            api.state()
            break
        except Exception as exc:
            log.info("Waiting for rgb-show API at %s (%s)", api_url, exc)
            stop.wait(3)

    client.connect_async(host, port, keepalive=60)
    client.loop_start()
    last_catalog = time.monotonic()
    try:
        while not stop.is_set():
            stop.wait(poll)
            if not client.is_connected():
                continue
            with lock:
                try:
                    # Pick up presets created in the UI
                    if time.monotonic() - last_catalog > 30:
                        last_catalog = time.monotonic()
                        before = [p["id"] for p in bridge.presets]
                        bridge.presets = api.presets()
                        if [p["id"] for p in bridge.presets] != before:
                            bridge.publish_discovery()
                    bridge.publish_state()
                except Exception as exc:
                    log.warning("Poll failed: %s", exc)
    finally:
        publish(bridge.availability_topic, "offline", True)
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    run_forever()

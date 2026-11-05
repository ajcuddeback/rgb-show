#!/usr/bin/env python3
# Flask Server Entry Point
# Author: Austin Cuddeback (ajcuddeback@gmail.com)
#
# Serves the compiled Angular app from ../templates and exposes a small JSON
# API under /api for controlling the lights.
#
# Configuration is via environment variables (see config.py / README):
#   RGB_NUM_PIXELS=100 RGB_PIN=D18 RGB_TREE_RINGS=32,26,20,14,8 ...
# Run with RGB_SIMULATE=1 on a laptop to develop without a Pi.

import atexit
import logging
import mimetypes
import os

from flask import Flask, jsonify, request, send_from_directory, abort
from werkzeug.exceptions import HTTPException

from config import Config
from neopixel_controller import NeoPixelController
from tree import TreeLayout
from engine import AnimationEngine
from presets import PresetStore
from animations import registry

logging.basicConfig(level=os.environ.get("RGB_LOG_LEVEL", "INFO"),
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("rgb-show")

mimetypes.add_type("application/manifest+json", ".webmanifest")

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates")


def create_app(config: Config = None) -> Flask:
    config = config or Config.from_env()
    controller = NeoPixelController(
        num_pixels=config.num_pixels, pin_name=config.pin_name, brightness=config.brightness,
        pixel_order=config.pixel_order, gamma=config.gamma, simulate=config.simulate,
    )
    config.simulate = controller.simulated
    tree = TreeLayout(config.resolved_rings())
    engine = AnimationEngine(controller, tree, config)
    presets = PresetStore(config.presets_file)

    app = Flask(__name__, static_folder=None)
    app.config["JSON_SORT_KEYS"] = False
    app.extensions["rgb"] = {"config": config, "controller": controller, "engine": engine, "presets": presets}

    log.info("rgb-show: %d pixels on %s, rings=%s, simulated=%s",
             config.num_pixels, config.pin_name, tree.rings, controller.simulated)

    # ----------------------------------------------------------- static files
    @app.route("/")
    def root():
        return send_from_directory(TEMPLATES_DIR, "index.html")

    @app.route("/<path:path>", methods=["GET"])
    def static_proxy(path):
        if path.startswith("api/"):
            abort(404)
        full = os.path.join(TEMPLATES_DIR, path)
        if os.path.isfile(full):
            res = send_from_directory(TEMPLATES_DIR, path)
            if path in ("ngsw-worker.js", "ngsw.json", "manifest.webmanifest"):
                res.headers["Cache-Control"] = "no-cache"   # the service worker must always see the latest
            return res
        # Unknown paths fall back to the SPA shell
        return send_from_directory(TEMPLATES_DIR, "index.html")

    # ------------------------------------------------------------------- api
    def body() -> dict:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            abort(400, description="Expected a JSON object body")
        return data

    def full_state() -> dict:
        s = engine.state()
        s["config"] = {**config.public(), **engine.layout()}
        return s

    @app.get("/api/layout")
    def get_layout():
        return jsonify(engine.layout())

    @app.put("/api/layout")
    def set_layout():
        data = body()
        rings = data.get("rings")
        if rings is not None and (not isinstance(rings, list) or not all(isinstance(r, (int, float)) for r in rings)):
            abort(400, description="'rings' must be a list of numbers (lights per wrap, bottom to top)")
        try:
            engine.set_layout(data.get("numPixels"), rings)
        except (ValueError, TypeError) as exc:
            abort(400, description=str(exc))
        return jsonify(full_state())

    @app.get("/api/state")
    def get_state():
        return jsonify(full_state())

    @app.get("/api/animations")
    def list_animations():
        return jsonify({"animations": registry.describe_all()})

    @app.post("/api/animations/<name>/start")
    def start_animation(name):
        if name not in registry.all_animations():
            abort(404, description=f"Unknown animation '{name}'")
        data = request.get_json(silent=True) or {}
        params = data.get("params") if isinstance(data, dict) else None
        if params is not None and not isinstance(params, dict):
            abort(400, description="'params' must be an object")
        if isinstance(data, dict) and "speed" in data:
            engine.set_speed(data["speed"])
        if isinstance(data, dict) and "brightness" in data:
            engine.set_brightness(data["brightness"])
        engine.start(name, params)
        return jsonify(full_state())

    @app.patch("/api/params")
    def update_params():
        data = body()
        params = data.get("params", data)
        if not isinstance(params, dict):
            abort(400, description="'params' must be an object")
        try:
            engine.update_params(params)
        except RuntimeError as exc:
            abort(409, description=str(exc))
        return jsonify(full_state())

    @app.post("/api/power")
    def set_power():
        data = body()
        on = data.get("on")
        if not isinstance(on, bool):
            abort(400, description="'on' must be true or false")
        if on:
            try:
                engine.power_on()
            except RuntimeError:
                # Nothing to resume yet: light something pleasant instead of doing nothing.
                engine.start("twinkle")
        else:
            engine.power_off()
        return jsonify(full_state())

    @app.post("/api/brightness")
    def set_brightness():
        data = body()
        try:
            level = float(data.get("brightness"))
        except (TypeError, ValueError):
            abort(400, description="'brightness' must be a number 0..1")
        engine.set_brightness(level)
        return jsonify(full_state())

    @app.post("/api/speed")
    def set_speed():
        data = body()
        try:
            speed = float(data.get("speed"))
        except (TypeError, ValueError):
            abort(400, description="'speed' must be a number (1 = normal)")
        engine.set_speed(speed)
        return jsonify(full_state())

    @app.get("/api/frame")
    def get_frame():
        # Compact: one hex string ("rrggbb" per pixel) is ~60% smaller than a JSON array of arrays,
        # which matters because the live preview polls this several times a second.
        frame = controller.get_frame()
        return jsonify({"n": len(frame), "hex": "".join("%02x%02x%02x" % c for c in frame),
                        "brightness": controller.brightness})

    # --------------------------------------------------------------- presets
    @app.get("/api/presets")
    def list_presets():
        return jsonify({"presets": presets.list()})

    @app.post("/api/presets")
    def add_preset():
        data = body()
        state = engine.state()
        animation = data.get("animation") or state["animation"]
        if not animation or animation not in registry.all_animations():
            abort(400, description="No animation to save")
        params = data.get("params") if isinstance(data.get("params"), dict) else state["params"]
        params = registry.get(animation).coerce_params(params)
        preset = presets.add(
            name=str(data.get("name") or registry.get(animation).LABEL),
            animation=animation,
            params={k: (list(v) if isinstance(v, tuple) else [list(c) for c in v] if isinstance(v, list) and v and isinstance(v[0], tuple) else v)
                    for k, v in params.items()},
            speed=state["speed"] if data.get("includeSpeed", True) else None,
            brightness=state["brightness"] if data.get("includeBrightness", False) else None,
        )
        return jsonify(preset), 201

    @app.post("/api/presets/<preset_id>/apply")
    def apply_preset(preset_id):
        preset = presets.get(preset_id)
        if not preset:
            abort(404, description="Preset not found")
        if preset.get("speed") is not None:
            engine.set_speed(preset["speed"])
        if preset.get("brightness") is not None:
            engine.set_brightness(preset["brightness"])
        engine.start(preset["animation"], preset.get("params") or {})
        return jsonify(full_state())

    @app.delete("/api/presets/<preset_id>")
    def delete_preset(preset_id):
        if not presets.delete(preset_id):
            abort(404, description="Preset not found")
        return jsonify({"deleted": preset_id})

    # ---------------------------------------------------------------- errors
    @app.errorhandler(HTTPException)
    def handle_http_error(exc):
        return jsonify({"error": exc.description, "status": exc.code}), exc.code

    engine.restore()
    atexit.register(engine.shutdown)
    return app


app = create_app()

if __name__ == "__main__":
    cfg = app.extensions["rgb"]["config"]
    # use_reloader=False: the reloader forks a second process that would open the GPIO pin twice.
    app.run(debug=os.environ.get("RGB_DEBUG", "0") == "1", host=cfg.host, port=cfg.port,
            threaded=True, use_reloader=False)

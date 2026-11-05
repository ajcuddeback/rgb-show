#!/usr/bin/env python3
# Animation engine
# Author: Austin Cuddeback (ajcuddeback@gmail.com)
#
# One place that owns "what is playing right now". Starting a new animation
# stops the previous one cleanly (stop event + bounded join - no more hangs if
# two clicks race), live-updates parameters without restarting, and persists
# the last state so the tree comes back the same way after a reboot.

import json
import logging
import os
import threading
from typing import Any, Dict, Optional

from animations import registry
from animations.base import Animation

log = logging.getLogger(__name__)


class AnimationEngine:
    def __init__(self, controller, tree, config):
        self.controller = controller
        self.tree = tree
        self.config = config
        self._lock = threading.RLock()
        self._animation: Optional[Animation] = None
        self._thread: Optional[threading.Thread] = None
        self.current_name: Optional[str] = None
        self.current_params: Dict[str, Any] = {}
        self.speed: float = 1.0
        self.power: bool = False

    # ------------------------------------------------------------------ state
    def state(self) -> dict:
        with self._lock:
            running = self._animation is not None and self._thread is not None and self._thread.is_alive()
            return {
                "power": self.power and running,
                "animation": self.current_name,
                "params": _jsonable(self.current_params),
                "speed": self.speed,
                "brightness": self.controller.brightness,
                "running": running,
            }

    # --------------------------------------------------------------- controls
    def start(self, name: str, params: Optional[Dict[str, Any]] = None, persist: bool = True) -> dict:
        cls = registry.get(name)  # KeyError for unknown animations
        with self._lock:
            # Reuse the current params when restarting the same animation with no explicit params
            if params is None and self.current_name == name:
                params = self.current_params
            self._stop_current()
            animation = cls(self.controller, self.tree, params or {}, speed=self.speed, fps=self.config.fps)
            thread = threading.Thread(target=animation.run_animation, name=f"anim-{name}", daemon=True)
            self._animation, self._thread = animation, thread
            self.current_name, self.current_params = name, dict(animation.params)
            self.power = True
            thread.start()
        if persist:
            self.save()
        return self.state()

    def update_params(self, params: Dict[str, Any]) -> dict:
        with self._lock:
            if self._animation is None or self.current_name is None:
                raise RuntimeError("No animation is running")
            self.current_params = self._animation.update_params(params)
        self.save()
        return self.state()

    def set_speed(self, speed: float) -> dict:
        with self._lock:
            self.speed = max(0.05, min(10.0, float(speed)))
            if self._animation is not None:
                self._animation.set_speed(self.speed)
        self.save()
        return self.state()

    def set_brightness(self, brightness: float) -> dict:
        self.controller.change_brightness(brightness)
        self.save()
        return self.state()

    def power_off(self) -> dict:
        with self._lock:
            self._stop_current()
            self.power = False
        self.save()
        return self.state()

    def power_on(self) -> dict:
        with self._lock:
            if self.current_name is None:
                raise RuntimeError("No animation to resume")
            return self.start(self.current_name, self.current_params)

    def shutdown(self) -> None:
        with self._lock:
            self._stop_current()

    # ---------------------------------------------------------------- internal
    def _stop_current(self) -> None:
        animation, thread = self._animation, self._thread
        self._animation, self._thread = None, None
        if animation is not None:
            animation.stop()
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=2.0)
            if thread.is_alive():
                log.warning("Animation thread did not stop within 2s; continuing anyway")
        self.controller.turn_off_all_lights()

    # ------------------------------------------------------------ persistence
    def save(self) -> None:
        path = self.config.state_file
        if not path:
            return
        data = {
            "animation": self.current_name,
            "params": _jsonable(self.current_params),
            "speed": self.speed,
            "brightness": self.controller.brightness,
            "power": self.power,
        }
        try:
            tmp = path + ".tmp"
            with open(tmp, "w") as fh:
                json.dump(data, fh)
            os.replace(tmp, path)
        except OSError as exc:
            log.warning("Could not save state to %s: %s", path, exc)

    def restore(self) -> None:
        path = self.config.state_file
        if not path or not os.path.exists(path):
            return
        try:
            with open(path) as fh:
                data = json.load(fh)
        except (OSError, ValueError) as exc:
            log.warning("Could not read state file %s: %s", path, exc)
            return
        try:
            if "brightness" in data:
                self.controller.change_brightness(float(data["brightness"]))
            if "speed" in data:
                self.speed = max(0.05, min(10.0, float(data["speed"])))
            name = data.get("animation")
            if name and name in registry.all_animations():
                self.current_name = name
                self.current_params = registry.get(name).coerce_params(data.get("params") or {})
                if data.get("power") and self.config.autostart:
                    self.start(name, self.current_params, persist=False)
        except Exception:
            log.exception("Failed to restore previous state")


def _jsonable(params: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k, v in params.items():
        if isinstance(v, tuple):
            out[k] = list(v)
        elif isinstance(v, list):
            out[k] = [list(x) if isinstance(x, tuple) else x for x in v]
        else:
            out[k] = v
    return out

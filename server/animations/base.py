#!/usr/bin/env python3
# Animation base class
# Author: Austin Cuddeback (ajcuddeback@gmail.com)
#
# Every animation is a small class that:
#   * declares PARAMS  - the knobs the UI renders (colors, sliders, selects)
#   * implements render(t) - fills self.frame for animation time `t` (seconds)
#
# The base class owns the frame loop, timing, speed scaling, the stop event
# (so stop() is instant and race-free) and live parameter updates.

import threading
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from .colors import Color, to_color, to_colors


@dataclass
class Param:
    key: str
    type: str                      # 'color' | 'colors' | 'number' | 'select' | 'boolean'
    label: str
    default: Any
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    options: Optional[List[Dict[str, str]]] = None   # for select: [{value, label}]
    min_items: int = 1             # for colors
    max_items: int = 8             # for colors
    help: str = ""

    def schema(self) -> dict:
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}

    def coerce(self, value: Any) -> Any:
        if value is None:
            return self.default
        if self.type == "color":
            return to_color(value)
        if self.type == "colors":
            colors = to_colors(value)[: self.max_items]
            if len(colors) < self.min_items:
                colors = list(colors) + list(to_colors(self.default))[len(colors): self.min_items]
            return colors or to_colors(self.default)
        if self.type == "number":
            try:
                v = float(value)
            except (TypeError, ValueError):
                return self.default
            if self.min is not None:
                v = max(self.min, v)
            if self.max is not None:
                v = min(self.max, v)
            return v
        if self.type == "boolean":
            if isinstance(value, str):
                return value.lower() in ("1", "true", "yes", "on")
            return bool(value)
        if self.type == "select":
            allowed = [o["value"] for o in (self.options or [])]
            return value if value in allowed else self.default
        return value


def select_options(*pairs) -> List[Dict[str, str]]:
    return [{"value": v, "label": l} for v, l in pairs]


class Animation:
    """Base class. Subclasses set NAME/LABEL/DESCRIPTION/CATEGORY/PARAMS and implement render()."""

    NAME = ""                  # url-safe id, defaults to class name lowercased
    LABEL = ""
    DESCRIPTION = ""
    CATEGORY = "Motion"        # Static | Motion | Sparkle | Nature | Showpiece
    PARAMS: List[Param] = []
    FPS: Optional[int] = None  # override global frame cap (static effects can go low)
    PREVIEW: List[Color] = []  # a few colors for the UI card chip

    def __init__(self, controller, tree, params: Dict[str, Any], speed: float = 1.0, fps: int = 30):
        self.controller = controller
        self.tree = tree
        self.n = controller.num_pixels
        self.frame: List[Color] = [(0, 0, 0)] * self.n
        self.speed = max(0.05, float(speed))
        self.fps = self.FPS or fps
        self._stop = threading.Event()
        self._param_lock = threading.Lock()
        self.params: Dict[str, Any] = self.coerce_params(params)
        self.t = 0.0            # speed-scaled animation time in seconds
        self.setup()

    # ----------------------------------------------------------------- params
    @classmethod
    def name(cls) -> str:
        return cls.NAME or cls.__name__.lower()

    @classmethod
    def defaults(cls) -> Dict[str, Any]:
        return {p.key: p.coerce(p.default) for p in cls.PARAMS}

    @classmethod
    def coerce_params(cls, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        params = params or {}
        out = {}
        for p in cls.PARAMS:
            out[p.key] = p.coerce(params.get(p.key, p.default))
        return out

    @classmethod
    def describe(cls) -> dict:
        return {
            "name": cls.name(),
            "label": cls.LABEL or cls.__name__,
            "description": cls.DESCRIPTION,
            "category": cls.CATEGORY,
            "params": [p.schema() for p in cls.PARAMS],
            "preview": [list(c) for c in cls.PREVIEW],
        }

    def update_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(self.params)
        merged.update(params or {})
        with self._param_lock:
            self.params = self.coerce_params(merged)
            self.on_params_changed()
        return dict(self.params)

    def set_speed(self, speed: float) -> None:
        self.speed = max(0.05, float(speed))

    def p(self, key: str) -> Any:
        return self.params[key]

    # -------------------------------------------------------------- lifecycle
    def setup(self) -> None:
        """Optional one-time init after params are available."""

    def on_params_changed(self) -> None:
        """Optional hook when params are live-updated."""

    def render(self, t: float) -> None:
        raise NotImplementedError

    def run_animation(self) -> None:
        interval = 1.0 / float(self.fps)
        last = time.monotonic()
        try:
            while not self._stop.is_set():
                now = time.monotonic()
                dt = min(now - last, 0.25)   # don't "catch up" after a stall
                last = now
                self.t += dt * self.speed
                with self._param_lock:
                    self.render(self.t)
                self.controller.show_frame(self.frame)
                # Sleep the remainder of the frame but wake instantly on stop()
                elapsed = time.monotonic() - now
                self._stop.wait(max(0.0, interval - elapsed))
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Animation %s crashed", self.name())

    def stop(self) -> None:
        self._stop.set()

    @property
    def stopped(self) -> bool:
        return self._stop.is_set()

    # ---------------------------------------------------------------- helpers
    def fill(self, color: Color) -> None:
        self.frame = [color] * self.n

    def clear(self) -> None:
        self.fill((0, 0, 0))

    def fade_all(self, factor: float) -> None:
        f = self.frame
        for i in range(self.n):
            r, g, b = f[i]
            f[i] = (int(r * factor), int(g * factor), int(b * factor))

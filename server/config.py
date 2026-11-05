#!/usr/bin/env python3
# Runtime configuration
# Author: Austin Cuddeback (ajcuddeback@gmail.com)
#
# Everything that used to be hard-coded (pixel count, GPIO pin, tree layout)
# is read from environment variables here so the same code runs on any
# strand / tree without edits. See README "Configuration".

import os
from dataclasses import dataclass, field
from typing import List, Optional


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_rings(name: str) -> Optional[List[int]]:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    try:
        rings = [int(x) for x in raw.replace(";", ",").split(",") if x.strip()]
    except ValueError:
        return None
    return [r for r in rings if r > 0] or None


# Default tree shape: 5 wraps tapering from 32 lights on the bottom wrap to 8 at the top.
# Scaled to whatever RGB_NUM_PIXELS is; override exactly with RGB_TREE_RINGS.
DEFAULT_RING_PROPORTIONS = [32, 26, 20, 14, 8]


@dataclass
class Config:
    num_pixels: int = 100
    pin_name: str = "D18"
    brightness: float = 0.1            # 0.0 - 1.0 startup brightness
    pixel_order: str = "RGB"           # RGB / GRB / RGBW ... (WS2811 strands are usually RGB)
    gamma: float = 1.0                 # 1.0 = raw colors (matches the original behavior); try 2.2 for smoother fades
    fps: int = 30                      # frame rate cap for animations
    layout: str = "tree"               # "tree" (spiral wrapped cone) or "strand" (straight line)
    rings: Optional[List[int]] = None  # pixels per wrap, bottom -> top. None = auto from proportions
    simulate: bool = False             # force the in-memory pixel simulator
    autostart: bool = True             # resume the last running animation on boot
    state_file: str = "state.json"
    presets_file: str = "presets.json"
    host: str = "0.0.0.0"
    port: int = 5000
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> "Config":
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.environ.get("RGB_DATA_DIR", base_dir)
        return cls(
            num_pixels=max(1, _env_int("RGB_NUM_PIXELS", 100)),
            pin_name=os.environ.get("RGB_PIN", "D18"),
            brightness=min(1.0, max(0.0, _env_float("RGB_BRIGHTNESS", 0.1))),
            pixel_order=os.environ.get("RGB_PIXEL_ORDER", "RGB").upper(),
            gamma=max(1.0, _env_float("RGB_GAMMA", 1.0)),
            fps=max(5, min(120, _env_int("RGB_FPS", 30))),
            layout=os.environ.get("RGB_LAYOUT", "tree").lower(),
            rings=_env_rings("RGB_TREE_RINGS"),
            simulate=_env_bool("RGB_SIMULATE", False),
            autostart=_env_bool("RGB_AUTOSTART", True),
            state_file=os.path.join(data_dir, os.environ.get("RGB_STATE_FILE", "state.json")),
            presets_file=os.path.join(data_dir, os.environ.get("RGB_PRESETS_FILE", "presets.json")),
            host=os.environ.get("RGB_HOST", "0.0.0.0"),
            port=_env_int("RGB_PORT", 5000),
        )

    def resolved_rings(self) -> List[int]:
        """Pixels per wrap from bottom to top, always summing to num_pixels."""
        if self.layout == "strand":
            return [self.num_pixels]

        if self.rings:
            rings = list(self.rings)
        else:
            rings = scale_rings(DEFAULT_RING_PROPORTIONS, self.num_pixels)

        total = sum(rings)
        if total < self.num_pixels:
            rings[-1] += self.num_pixels - total
        elif total > self.num_pixels:
            trimmed, remaining = [], self.num_pixels
            for r in rings:
                if remaining <= 0:
                    break
                take = min(r, remaining)
                trimmed.append(take)
                remaining -= take
            rings = trimmed
        return rings

    def public(self) -> dict:
        return {
            "numPixels": self.num_pixels,
            "pin": self.pin_name,
            "pixelOrder": self.pixel_order,
            "gamma": self.gamma,
            "fps": self.fps,
            "layout": self.layout,
            "rings": self.resolved_rings(),
            "simulated": self.simulate,
        }


def scale_rings(proportions: List[int], total: int) -> List[int]:
    """Scale a ring proportion list to exactly `total` pixels (largest remainder)."""
    if total <= 0:
        return []
    if total < len(proportions):
        # Too few pixels for every ring: collapse to as many rings as pixels.
        return [1] * total
    weight = sum(proportions)
    raw = [p * total / weight for p in proportions]
    rings = [max(1, int(x)) for x in raw]
    remainder = total - sum(rings)
    order = sorted(range(len(raw)), key=lambda i: raw[i] - int(raw[i]), reverse=True)
    i = 0
    while remainder != 0 and order:
        idx = order[i % len(order)]
        if remainder > 0:
            rings[idx] += 1
            remainder -= 1
        elif rings[idx] > 1:
            rings[idx] -= 1
            remainder += 1
        i += 1
    return rings

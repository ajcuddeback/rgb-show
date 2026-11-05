#!/usr/bin/env python3
# Color math helpers shared by animations

import colorsys
import random
from typing import List, Sequence, Tuple

Color = Tuple[int, int, int]

BLACK: Color = (0, 0, 0)
WHITE: Color = (255, 255, 255)
WARM_WHITE: Color = (255, 160, 70)
RED: Color = (255, 0, 0)
GREEN: Color = (0, 255, 0)
BLUE: Color = (0, 0, 255)
GOLD: Color = (255, 170, 0)

XMAS: List[Color] = [RED, GREEN]
XMAS_CLASSIC: List[Color] = [RED, GREEN, (245, 0, 245), (255, 255, 0), (0, 120, 255)]
CANDY_CANE: List[Color] = [RED, WHITE]
WINTER: List[Color] = [(0, 90, 255), (120, 200, 255), WHITE]
AURORA: List[Color] = [(0, 255, 120), (0, 160, 255), (140, 0, 255), (0, 255, 200)]
FIRE: List[Color] = [(0, 0, 0), (120, 0, 0), (255, 60, 0), (255, 170, 0), (255, 255, 160)]


def clamp8(v: float) -> int:
    v = int(v)
    return 0 if v < 0 else 255 if v > 255 else v


def to_color(value) -> Color:
    """Coerce lists / hex strings / tuples into an (r, g, b) tuple."""
    if isinstance(value, str):
        s = value.lstrip("#")
        if len(s) == 3:
            s = "".join(ch * 2 for ch in s)
        if len(s) >= 6:
            return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
        return BLACK
    try:
        r, g, b = list(value)[:3]
        return (clamp8(r), clamp8(g), clamp8(b))
    except (TypeError, ValueError):
        return BLACK


def to_colors(value) -> List[Color]:
    if value is None:
        return []
    if isinstance(value, str) or (isinstance(value, (list, tuple)) and value and isinstance(value[0], (int, float))):
        return [to_color(value)]
    return [to_color(v) for v in value]


def scale(color: Color, factor: float) -> Color:
    factor = 0.0 if factor < 0 else 1.0 if factor > 1 else factor
    return (clamp8(color[0] * factor), clamp8(color[1] * factor), clamp8(color[2] * factor))


def lerp(a: Color, b: Color, t: float) -> Color:
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    return (
        clamp8(a[0] + (b[0] - a[0]) * t),
        clamp8(a[1] + (b[1] - a[1]) * t),
        clamp8(a[2] + (b[2] - a[2]) * t),
    )


def add(a: Color, b: Color) -> Color:
    return (clamp8(a[0] + b[0]), clamp8(a[1] + b[1]), clamp8(a[2] + b[2]))


def maximum(a: Color, b: Color) -> Color:
    return (max(a[0], b[0]), max(a[1], b[1]), max(a[2], b[2]))


def hsv(h: float, s: float = 1.0, v: float = 1.0) -> Color:
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (clamp8(r * 255), clamp8(g * 255), clamp8(b * 255))


def gradient(palette: Sequence[Color], t: float, wrap: bool = True) -> Color:
    """Sample a smooth gradient through `palette` at position t in [0,1)."""
    if not palette:
        return BLACK
    if len(palette) == 1:
        return palette[0]
    if wrap:
        t = t % 1.0
        pos = t * len(palette)
        i = int(pos)
        return lerp(palette[i % len(palette)], palette[(i + 1) % len(palette)], pos - i)
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    pos = t * (len(palette) - 1)
    i = min(int(pos), len(palette) - 2)
    return lerp(palette[i], palette[i + 1], pos - i)


def random_color(palette: Sequence[Color]) -> Color:
    return random.choice(list(palette)) if palette else WHITE


def dim_floor(color: Color, floor: float) -> Color:
    """Never fully black: keep at least `floor` of the color."""
    return lerp(BLACK, color, floor) if floor > 0 else BLACK

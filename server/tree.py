#!/usr/bin/env python3
# Tree geometry
# Author: Austin Cuddeback (ajcuddeback@gmail.com)
#
# Every pixel gets a position on the tree, used by animations so that effects
# like "snow falling", "spiral" or "rings climbing" follow the real shape:
#
#   x, y     horizontal position, normalized so the widest point is radius 1
#            (front of the tree is -y; the camera mapping defines "front")
#   z        0.0 (bottom) .. 1.0 (top)
#   height   alias of z
#   angle    0.0 .. 1.0 fraction of a turn around the trunk
#   ring     index of the height band the pixel belongs to (bottom -> top)
#
# Two ways to build it:
#   TreeLayout(rings)             assume the strand spirals up a cone with the
#                                 given number of lights per wrap
#   TreeLayout.from_points(pts)   real 3D positions from the camera mapping

import math
from typing import List, Optional, Sequence

Point = Optional[Sequence[float]]


class TreeLayout:
    def __init__(self, rings: Sequence[int]):
        rings = [int(r) for r in rings if int(r) > 0]
        if not rings:
            raise ValueError("TreeLayout needs at least one ring")
        n = sum(rings)
        num_rings = len(rings)
        x: List[float] = []
        y: List[float] = []
        z: List[float] = []
        for r, size in enumerate(rings):
            for k in range(size):
                frac = k / size
                h = frac if num_rings == 1 else (r + frac) / num_rings
                z.append(h)
        top = max(z) or 1.0
        z = [v / top for v in z]
        idx = 0
        for r, size in enumerate(rings):
            for k in range(size):
                a = (k / size) * 2 * math.pi
                radius = 1.0 - 0.9 * z[idx]          # cone: wide at the bottom
                x.append(radius * math.cos(a))
                y.append(radius * math.sin(a))
                idx += 1
        self._init_from_xyz(x, y, z, bands=num_rings, source="wraps", rings=rings)

    # ------------------------------------------------------------ constructors
    @classmethod
    def from_points(cls, points: Sequence[Point], bands: Optional[int] = None) -> "TreeLayout":
        """Build from measured positions. Unknown pixels (None) are interpolated from their wire neighbors."""
        pts = [list(map(float, p)) if p is not None and len(p) == 3 else None for p in points]
        n = len(pts)
        if n == 0:
            raise ValueError("No points")
        if all(p is None for p in pts):
            raise ValueError("No pixel has a known position")
        pts = _interpolate_missing(pts)

        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        zs = [p[2] for p in pts]
        zmin, zmax = min(zs), max(zs)
        zspan = (zmax - zmin) or 1.0
        z = [(v - zmin) / zspan for v in zs]
        cx, cy = _median(xs), _median(ys)
        rad = max(math.hypot(px - cx, py - cy) for px, py in zip(xs, ys)) or 1.0
        x = [(px - cx) / rad for px in xs]
        y = [(py - cy) / rad for py in ys]

        obj = cls.__new__(cls)
        obj._init_from_xyz(x, y, z, bands=bands or max(3, min(12, round(math.sqrt(n) / 1.6))), source="camera", rings=None)
        return obj

    def _init_from_xyz(self, x, y, z, bands: int, source: str, rings: Optional[List[int]]):
        self.n = len(z)
        self.source = source
        self.x, self.y, self.z = list(x), list(y), list(z)
        self.height = self.z
        self.angle = [(math.atan2(yy, xx) / (2 * math.pi)) % 1.0 for xx, yy in zip(x, y)]
        self.radius = [math.hypot(xx, yy) for xx, yy in zip(x, y)]
        # Height bands ("wraps"). For the cone layout these are the real wraps.
        self.num_rings = max(1, int(bands))
        if rings is not None:
            ring_of: List[int] = []
            for r, size in enumerate(rings):
                ring_of.extend([r] * size)
            self.ring_of = ring_of
        else:
            self.ring_of = [min(self.num_rings - 1, int(h * self.num_rings)) for h in self.z]
        self._rings_members = [[] for _ in range(self.num_rings)]
        for i, r in enumerate(self.ring_of):
            self._rings_members[r].append(i)
        self.rings = [len(m) for m in self._rings_members]
        self.order_by_height = sorted(range(self.n), key=lambda i: self.z[i])

    # ---------------------------------------------------------------- queries
    def pixels_in_ring(self, ring: int) -> List[int]:
        return self._rings_members[ring]

    def top_pixels(self, k: int) -> List[int]:
        """The k highest pixels on the tree."""
        return self.order_by_height[-max(0, min(self.n, int(k))):] if k > 0 else []

    def points(self) -> List[List[float]]:
        return [[round(a, 4), round(b, 4), round(c, 4)] for a, b, c in zip(self.x, self.y, self.z)]

    def describe(self) -> dict:
        return {"rings": self.rings, "numRings": self.num_rings, "numPixels": self.n, "source": self.source}


def angular_distance(a: float, b: float) -> float:
    """Shortest distance between two angles given as turns (0..1): result in 0..0.5."""
    d = abs((a - b) % 1.0)
    return min(d, 1.0 - d)


def _median(vals: Sequence[float]) -> float:
    s = sorted(vals)
    m = len(s) // 2
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2


def _interpolate_missing(pts: List[Optional[List[float]]]) -> List[List[float]]:
    """Fill None entries by linear interpolation between the nearest known neighbors along the wire."""
    n = len(pts)
    known = [i for i, p in enumerate(pts) if p is not None]
    out: List[List[float]] = []
    for i in range(n):
        if pts[i] is not None:
            out.append(list(pts[i]))
            continue
        prev = max((k for k in known if k < i), default=None)
        nxt = min((k for k in known if k > i), default=None)
        if prev is None:
            out.append(list(pts[nxt]))
        elif nxt is None:
            out.append(list(pts[prev]))
        else:
            t = (i - prev) / (nxt - prev)
            out.append([pts[prev][d] + (pts[nxt][d] - pts[prev][d]) * t for d in range(3)])
    return out

#!/usr/bin/env python3
# Tree geometry
# Author: Austin Cuddeback (ajcuddeback@gmail.com)
#
# A light strand wrapped around a Christmas tree is a spiral on a cone. Given
# the number of pixels per wrap (bottom -> top) this precomputes, for every
# pixel, where it sits on the tree:
#
#   height  0.0 (bottom) .. 1.0 (top)
#   angle   0.0 .. 1.0 fraction of a turn around the trunk
#   ring    index of the wrap the pixel is on
#
# Animations use these so effects like "spiral", "snow falling down" or
# "rings climbing up" look right on the actual tree instead of just running
# down the wire.

import math
from typing import List, Sequence


class TreeLayout:
    def __init__(self, rings: Sequence[int]):
        rings = [int(r) for r in rings if int(r) > 0]
        if not rings:
            raise ValueError("TreeLayout needs at least one ring")
        self.rings: List[int] = rings
        self.num_rings = len(rings)
        self.n = sum(rings)

        self.ring_of: List[int] = []
        self.height: List[float] = []
        self.angle: List[float] = []
        self.ring_start: List[int] = []
        self.ring_end: List[int] = []  # exclusive

        idx = 0
        for r, size in enumerate(rings):
            self.ring_start.append(idx)
            self.ring_end.append(idx + size)
            for k in range(size):
                frac = k / size
                self.ring_of.append(r)
                # Continuous spiral: height rises smoothly across each wrap.
                self.height.append((r + frac) / self.num_rings)
                self.angle.append(frac)
                idx += 1

        # Normalize so the very top pixel is ~1.0
        top = max(self.height) if self.height else 1.0
        if top > 0:
            self.height = [h / top for h in self.height]

        # Cartesian-ish coordinates on the unrolled cone, handy for 2D effects.
        self.x: List[float] = [math.cos(a * 2 * math.pi) for a in self.angle]
        self.y: List[float] = [math.sin(a * 2 * math.pi) for a in self.angle]

    def pixels_in_ring(self, ring: int) -> range:
        return range(self.ring_start[ring], self.ring_end[ring])

    def describe(self) -> dict:
        return {"rings": self.rings, "numRings": self.num_rings, "numPixels": self.n}

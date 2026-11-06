#!/usr/bin/env python3
# Spatial effects: these use each light's real 3D position (best after mapping
# the tree with the camera, but they also work on the estimated cone layout).

import math
import random

from ..base import Animation, Param, select_options
from ..colors import BLACK, WHITE, GOLD, lerp, scale, maximum


class Sweep(Animation):
    LABEL = "Sweep"
    DESCRIPTION = "A glowing plane of light passes through the whole tree - up, across, or spinning."
    CATEGORY = "Showpiece"
    PARAMS = [
        Param("colors", "colors", "Colors", [(255, 0, 60), (255, 170, 0), (0, 200, 255)]),
        Param("background", "color", "Background", (4, 0, 12)),
        Param("axis", "select", "Direction", "spin",
              options=select_options(("up", "Bottom to top"), ("side", "Side to side"),
                                     ("front", "Front to back"), ("spin", "Spinning"), ("tilt", "Tilted spin"))),
        Param("thickness", "number", "Thickness", 0.18, min=0.05, max=0.6, step=0.01),
        Param("duration", "number", "Seconds per pass", 2.5, min=0.5, max=10, step=0.1),
    ]
    PREVIEW = [(255, 0, 60), (255, 170, 0), (0, 200, 255)]

    def render(self, t):
        colors = self.p("colors")
        bg = self.p("background")
        axis = self.p("axis")
        thick = self.p("thickness")
        dur = self.p("duration")
        tree = self.tree
        frame = self.frame
        phase = t / dur
        c = colors[int(phase) % len(colors)]
        frac = phase - int(phase)
        if axis in ("spin", "tilt"):
            ang = frac * 2 * math.pi
            nx, ny = math.cos(ang), math.sin(ang)
            for i in range(self.n):
                d = tree.x[i] * nx + tree.y[i] * ny
                if axis == "tilt":
                    d += (tree.z[i] - 0.5) * 0.8
                level = max(0.0, 1 - abs(d) / thick)
                frame[i] = lerp(bg, c, level * level) if level > 0 else bg
            return
        if axis == "up":
            pos = -thick + frac * (1 + 2 * thick)
            coord = tree.z
        elif axis == "side":
            pos = -1 - thick + frac * (2 + 2 * thick)
            coord = tree.x
        else:
            pos = -1 - thick + frac * (2 + 2 * thick)
            coord = tree.y
        for i in range(self.n):
            level = max(0.0, 1 - abs(coord[i] - pos) / thick)
            frame[i] = lerp(bg, c, level * level) if level > 0 else bg


class Pulse(Animation):
    LABEL = "Pulse"
    DESCRIPTION = "Spheres of light expand outward from the heart of the tree."
    CATEGORY = "Showpiece"
    PARAMS = [
        Param("colors", "colors", "Colors", [(255, 255, 255), (255, 0, 80), (0, 180, 255)]),
        Param("background", "color", "Background", BLACK),
        Param("origin", "select", "From", "center",
              options=select_options(("center", "Center"), ("top", "Top"), ("bottom", "Bottom"), ("random", "Random spots"))),
        Param("duration", "number", "Seconds per pulse", 2, min=0.5, max=8, step=0.1),
        Param("thickness", "number", "Ring thickness", 0.16, min=0.05, max=0.5, step=0.01),
    ]
    PREVIEW = [(255, 255, 255), (255, 0, 80), (0, 180, 255)]

    def setup(self):
        self._cycle = -1
        self._origin = (0.0, 0.0, 0.5)

    def render(self, t):
        colors = self.p("colors")
        bg = self.p("background")
        dur = self.p("duration")
        thick = self.p("thickness")
        tree = self.tree
        phase = t / dur
        cycle = int(phase)
        if cycle != self._cycle:
            self._cycle = cycle
            o = self.p("origin")
            if o == "top":
                self._origin = (0.0, 0.0, 1.0)
            elif o == "bottom":
                self._origin = (0.0, 0.0, 0.0)
            elif o == "random":
                i = random.randrange(self.n)
                self._origin = (tree.x[i], tree.y[i], tree.z[i])
            else:
                self._origin = (0.0, 0.0, 0.5)
        frac = phase - cycle
        radius = frac * 1.8
        fade = 1 - frac * 0.6
        c = colors[cycle % len(colors)]
        ox, oy, oz = self._origin
        frame = self.frame
        for i in range(self.n):
            d = math.sqrt((tree.x[i] - ox) ** 2 + (tree.y[i] - oy) ** 2 + ((tree.z[i] - oz) * 2.0) ** 2)
            level = max(0.0, 1 - abs(d - radius) / thick) * fade
            frame[i] = lerp(bg, c, level * level) if level > 0 else bg


class Orbit(Animation):
    LABEL = "Orbit"
    DESCRIPTION = "Bright comets circle the tree at different heights, trailing light behind them."
    CATEGORY = "Showpiece"
    PARAMS = [
        Param("colors", "colors", "Comet colors", [GOLD, (120, 200, 255), (255, 80, 200)]),
        Param("background", "color", "Background", (0, 0, 10)),
        Param("count", "number", "Comets", 3, min=1, max=8, step=1),
        Param("duration", "number", "Seconds per lap", 3, min=0.5, max=12, step=0.1),
        Param("tail", "number", "Tail length", 0.3, min=0.05, max=0.5, step=0.01, help="As a fraction of a lap."),
        Param("bob", "number", "Bobbing", 0.15, min=0, max=0.5, step=0.01),
    ]
    PREVIEW = [GOLD, (120, 200, 255), (255, 80, 200)]

    def render(self, t):
        colors = self.p("colors")
        bg = self.p("background")
        count = int(self.p("count"))
        dur = self.p("duration")
        tail = self.p("tail")
        bob = self.p("bob")
        tree = self.tree
        frame = self.frame
        for i in range(self.n):
            frame[i] = bg
        for k in range(count):
            direction = 1 if k % 2 == 0 else -1
            speed = 1 / (dur * (1 + 0.15 * k))
            a = (t * speed * direction + k / count) % 1.0
            h = 0.15 + 0.7 * ((k + 0.5) / count) + bob * math.sin(t * 1.3 + k)
            c = colors[k % len(colors)]
            for i in range(self.n):
                dh = abs(tree.z[i] - h)
                if dh > 0.09:
                    continue
                behind = ((a - tree.angle[i]) * direction) % 1.0
                if behind > tail:
                    continue
                level = (1 - behind / tail) ** 2 * (1 - dh / 0.09)
                frame[i] = maximum(frame[i], scale(c, level))

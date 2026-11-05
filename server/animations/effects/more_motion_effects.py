#!/usr/bin/env python3
# More motion effects: heartbeat, scanner, ripple, sunset.

import math

from ..base import Animation, Param, select_options
from ..colors import BLACK, WHITE, gradient, scale, lerp


class Heartbeat(Animation):
    LABEL = "Heartbeat"
    DESCRIPTION = "Lub-dub. Two quick pulses, a rest, repeat."
    CATEGORY = "Motion"
    PARAMS = [
        Param("color", "color", "Color", (255, 0, 30)),
        Param("bpm", "number", "Beats per minute", 60, min=30, max=160, step=1),
        Param("floor", "number", "Resting glow", 0.08, min=0, max=0.5, step=0.02),
    ]
    PREVIEW = [(255, 0, 30), (90, 0, 10)]

    def render(self, t):
        color = self.p("color")
        floor = self.p("floor")
        beat = (t * self.p("bpm") / 60) % 1
        # first pulse at 0, second (smaller) at 0.25
        lub = math.exp(-((beat - 0.02) ** 2) / 0.004)
        dub = 0.65 * math.exp(-((beat - 0.26) ** 2) / 0.003)
        level = floor + (1 - floor) * min(1.0, lub + dub)
        self.fill(scale(color, level))


class Scanner(Animation):
    LABEL = "Scanner"
    DESCRIPTION = "A bright eye sweeps back and forth with a glowing trail."
    CATEGORY = "Motion"
    PARAMS = [
        Param("color", "color", "Color", (255, 0, 0)),
        Param("width", "number", "Eye width", 6, min=2, max=20, step=1),
        Param("duration", "number", "Seconds per sweep", 2, min=0.5, max=8, step=0.1),
        Param("axis", "select", "Sweep", "strand",
              options=select_options(("strand", "Along the wire"), ("height", "Up and down the tree"))),
        Param("glow", "number", "Background glow", 0.03, min=0, max=0.3, step=0.01),
    ]
    PREVIEW = [(255, 0, 0), (60, 0, 0)]

    def render(self, t):
        color = self.p("color")
        width = self.p("width") / max(1, self.n)
        phase = (t / self.p("duration")) % 2
        center = phase if phase <= 1 else 2 - phase       # 0 -> 1 -> 0
        glow = self.p("glow")
        pos = self.tree.height if self.p("axis") == "height" else [i / max(1, self.n - 1) for i in range(self.n)]
        frame = self.frame
        for i in range(self.n):
            d = abs(pos[i] - center) / width
            level = max(glow, math.exp(-d * d * 2.5))
            frame[i] = scale(color, level)


class Ripple(Animation):
    LABEL = "Ripple"
    DESCRIPTION = "Rings of color rise from the bottom of the tree like ripples in a pond."
    CATEGORY = "Motion"
    PARAMS = [
        Param("colors", "colors", "Ring colors", [(0, 120, 255), (0, 255, 200), (255, 255, 255)]),
        Param("background", "color", "Background", (0, 0, 25)),
        Param("rings", "number", "Rings on tree", 2, min=1, max=5, step=1),
        Param("thickness", "number", "Ring thickness", 0.08, min=0.02, max=0.3, step=0.01),
        Param("tempo", "number", "Speed", 0.35, min=0.05, max=1.5, step=0.05),
        Param("direction", "select", "Direction", "up",
              options=select_options(("up", "Rising"), ("down", "Falling"))),
    ]
    PREVIEW = [(0, 120, 255), (0, 255, 200), (255, 255, 255)]

    def render(self, t):
        colors = self.p("colors")
        bg = self.p("background")
        rings = int(self.p("rings"))
        thick = self.p("thickness")
        shift = t * self.p("tempo") * (1 if self.p("direction") == "up" else -1)
        tree = self.tree
        frame = self.frame
        for i in range(self.n):
            v = tree.height[i] * rings - shift
            k = math.floor(v)
            frac = v - k
            d = min(frac, 1 - frac)       # distance to nearest ring line
            level = max(0.0, 1 - d / thick)
            frame[i] = lerp(bg, colors[k % len(colors)], level * level)


class Sunset(Animation):
    LABEL = "Sunset"
    DESCRIPTION = "A slow, warm sky: gold at the bottom fading to violet at the top, drifting over minutes."
    CATEGORY = "Motion"
    PARAMS = [
        Param("colors", "colors", "Sky (bottom → top)", [(255, 120, 0), (255, 40, 60), (120, 0, 140), (10, 0, 50)], min_items=2),
        Param("duration", "number", "Minutes per cycle", 2, min=0.25, max=30, step=0.25),
        Param("shimmer", "number", "Shimmer", 0.15, min=0, max=0.6, step=0.05),
    ]
    PREVIEW = [(255, 120, 0), (255, 40, 60), (120, 0, 140), (10, 0, 50)]

    def render(self, t):
        colors = self.p("colors")
        cycle = (t / (self.p("duration") * 60)) % 1
        # breathe the gradient up and down the tree over the cycle
        offset = 0.5 - 0.5 * math.cos(cycle * 2 * math.pi)
        shimmer = self.p("shimmer")
        tree = self.tree
        frame = self.frame
        for i in range(self.n):
            pos = max(0.0, min(1.0, tree.height[i] * 0.8 + offset * 0.4 - 0.1))
            c = gradient(colors, pos, wrap=False)
            if shimmer:
                c = scale(c, 1 - shimmer * (0.5 + 0.5 * math.sin(t * 1.3 + i * 0.7)))
            frame[i] = c

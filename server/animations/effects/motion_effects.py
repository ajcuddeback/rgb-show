#!/usr/bin/env python3
# Motion effects: patterns that move, climb, chase and breathe.

import math
import random

from ..base import Animation, Param, select_options
from ..colors import (XMAS, XMAS_CLASSIC, CANDY_CANE, WINTER, BLACK, WHITE, GOLD,
                      gradient, lerp, scale, hsv)


DIRECTION_OPTIONS = select_options(("up", "Up the tree"), ("down", "Down the tree"))


class March(Animation):
    LABEL = "Marching Colors"
    DESCRIPTION = "A repeating pattern that steps along the strand on every beat."
    CATEGORY = "Motion"
    PARAMS = [
        Param("colors", "colors", "Colors", XMAS_CLASSIC),
        Param("block", "number", "Lights per color", 1, min=1, max=10, step=1),
        Param("tempo", "number", "Steps per second", 3, min=0.5, max=15, step=0.5),
        Param("direction", "select", "Direction", "up", options=DIRECTION_OPTIONS),
    ]
    PREVIEW = XMAS_CLASSIC

    def render(self, t):
        colors = self.p("colors")
        block = max(1, int(self.p("block")))
        step = int(t * self.p("tempo"))
        if self.p("direction") == "down":
            step = -step
        self.frame = [colors[((i // block) + step) % len(colors)] for i in range(self.n)]


class Chase(Animation):
    LABEL = "Theater Chase"
    DESCRIPTION = "Classic marquee lights running around the tree."
    CATEGORY = "Motion"
    PARAMS = [
        Param("colors", "colors", "Colors", [GOLD, WHITE]),
        Param("gap", "number", "Spacing", 3, min=2, max=8, step=1),
        Param("tempo", "number", "Steps per second", 8, min=1, max=30, step=1),
        Param("glow", "number", "Background glow", 0.08, min=0, max=0.5, step=0.02,
              help="How much the unlit lights stay dimly on."),
        Param("direction", "select", "Direction", "up", options=DIRECTION_OPTIONS),
    ]
    PREVIEW = [GOLD, WHITE]

    def render(self, t):
        colors = self.p("colors")
        gap = max(2, int(self.p("gap")))
        glow = self.p("glow")
        step = int(t * self.p("tempo"))
        if self.p("direction") == "down":
            step = -step
        frame = self.frame
        for i in range(self.n):
            k = i + step
            color = colors[(k // gap) % len(colors)]
            frame[i] = color if k % gap == 0 else scale(color, glow)


class Climb(Animation):
    LABEL = "Ring Climb"
    DESCRIPTION = "Each color climbs the tree one wrap at a time, pushing the last color up and off the top."
    CATEGORY = "Motion"
    PARAMS = [
        Param("colors", "colors", "Colors", XMAS),
        Param("tempo", "number", "Wraps per second", 2.5, min=0.25, max=10, step=0.25),
        Param("hold", "number", "Hold at top (s)", 0.6, min=0, max=5, step=0.1),
        Param("mode", "select", "Style", "fill",
              options=select_options(("fill", "Fill up"), ("sweep", "Single wrap sweep"))),
    ]
    PREVIEW = XMAS

    def render(self, t):
        colors = self.p("colors")
        tree = self.tree
        rings = tree.num_rings
        tempo = self.p("tempo")
        per_color = rings / tempo + self.p("hold")
        cycle = per_color * len(colors)
        local = t % cycle
        c = int(local // per_color)
        progress = min(rings, (local - c * per_color) * tempo)   # wraps lit, fractional
        color = colors[c % len(colors)]
        prev = colors[(c - 1) % len(colors)]
        sweep = self.p("mode") == "sweep"
        lit_ring = int(progress)
        frac = progress - lit_ring
        frame = self.frame
        for i in range(self.n):
            r = tree.ring_of[i]
            if r < lit_ring:
                frame[i] = BLACK if sweep else color
            elif r == lit_ring and tree.angle[i] < frac:
                frame[i] = color
            else:
                frame[i] = BLACK if sweep else prev
        if sweep and lit_ring < rings:
            for i in tree.pixels_in_ring(lit_ring):
                if tree.angle[i] < frac:
                    frame[i] = color
                else:
                    frame[i] = scale(color, 0.15)


class Wave(Animation):
    LABEL = "Gradient Wave"
    DESCRIPTION = "A silky gradient that rolls up the tree."
    CATEGORY = "Motion"
    PARAMS = [
        Param("colors", "colors", "Colors", [(255, 0, 0), (0, 160, 0), (255, 215, 0)], min_items=2),
        Param("waves", "number", "Waves on tree", 1, min=0.25, max=4, step=0.25),
        Param("tempo", "number", "Speed", 0.25, min=0.02, max=1.5, step=0.02),
        Param("direction", "select", "Direction", "up", options=DIRECTION_OPTIONS),
        Param("axis", "select", "Travel along", "height",
              options=select_options(("height", "Bottom → top"), ("strand", "Along the wire"))),
    ]
    PREVIEW = [(255, 0, 0), (0, 160, 0), (255, 215, 0)]

    def render(self, t):
        colors = self.p("colors")
        waves = self.p("waves")
        shift = t * self.p("tempo") * (1 if self.p("direction") == "down" else -1)
        pos = self.tree.height if self.p("axis") == "height" else [i / self.n for i in range(self.n)]
        self.frame = [gradient(colors, pos[i] * waves + shift) for i in range(self.n)]


class Spiral(Animation):
    LABEL = "Candy Cane Spiral"
    DESCRIPTION = "Stripes that wind around the tree and slowly rotate."
    CATEGORY = "Motion"
    PARAMS = [
        Param("colors", "colors", "Colors", CANDY_CANE),
        Param("stripes", "number", "Stripes around", 2, min=1, max=6, step=1),
        Param("twist", "number", "Twist", 1.5, min=0, max=6, step=0.5, help="How many times the stripes wrap going up."),
        Param("tempo", "number", "Rotation speed", 0.3, min=0.02, max=2, step=0.02),
        Param("soft", "boolean", "Soft edges", False),
        Param("direction", "select", "Direction", "up", options=DIRECTION_OPTIONS),
    ]
    PREVIEW = CANDY_CANE

    def render(self, t):
        colors = self.p("colors")
        stripes = self.p("stripes")
        twist = self.p("twist")
        shift = t * self.p("tempo") * (1 if self.p("direction") == "up" else -1)
        soft = self.p("soft")
        tree = self.tree
        frame = self.frame
        count = len(colors)
        for i in range(self.n):
            v = tree.angle[i] * stripes + tree.height[i] * twist + shift
            if soft:
                frame[i] = gradient(colors, v)
            else:
                frame[i] = colors[int(v * count) % count]


class Wipe(Animation):
    LABEL = "Color Wipe"
    DESCRIPTION = "Each color paints over the last, sweeping across the tree."
    CATEGORY = "Motion"
    PARAMS = [
        Param("colors", "colors", "Colors", [(255, 0, 0), (0, 255, 0), (0, 80, 255), (255, 255, 255)], min_items=2),
        Param("duration", "number", "Seconds per wipe", 2, min=0.3, max=10, step=0.1),
        Param("axis", "select", "Wipe", "up",
              options=select_options(("up", "Bottom → top"), ("down", "Top → bottom"), ("strand", "Along the wire"))),
    ]
    PREVIEW = [(255, 0, 0), (0, 255, 0), (0, 80, 255), (255, 255, 255)]

    def render(self, t):
        colors = self.p("colors")
        duration = self.p("duration")
        pos = t / duration
        c = int(pos) % len(colors)
        frac = pos - int(pos)
        color, prev = colors[c], colors[c - 1]
        axis = self.p("axis")
        tree = self.tree
        frame = self.frame
        for i in range(self.n):
            if axis == "strand":
                p = i / self.n
            elif axis == "down":
                p = 1.0 - tree.height[i]
            else:
                p = tree.height[i]
            frame[i] = color if p <= frac else prev


class Breathe(Animation):
    LABEL = "Breathe"
    DESCRIPTION = "The whole tree gently fades through your colors."
    CATEGORY = "Motion"
    PARAMS = [
        Param("colors", "colors", "Colors", [(255, 0, 0), (0, 200, 0), (255, 255, 255)]),
        Param("duration", "number", "Seconds per breath", 4, min=1, max=15, step=0.5),
        Param("floor", "number", "Minimum glow", 0.05, min=0, max=0.6, step=0.05),
    ]
    PREVIEW = [(255, 0, 0), (0, 200, 0), (255, 255, 255)]

    def render(self, t):
        colors = self.p("colors")
        duration = self.p("duration")
        floor = self.p("floor")
        pos = t / duration
        c = int(pos) % len(colors)
        phase = pos - int(pos)
        level = (1 - math.cos(phase * 2 * math.pi)) / 2      # 0 -> 1 -> 0
        level = floor + (1 - floor) * level
        self.fill(scale(colors[c], level))


class FillDrain(Animation):
    NAME = "filldrain"
    LABEL = "Random Fill"
    DESCRIPTION = "Lights pop on in random order until the tree is full, then the next color takes over."
    CATEGORY = "Motion"
    PARAMS = [
        Param("colors", "colors", "Colors", [(255, 0, 0), (0, 255, 0), (255, 255, 255), (0, 90, 255)]),
        Param("duration", "number", "Seconds per fill", 3, min=0.5, max=15, step=0.5),
        Param("mode", "select", "Style", "over",
              options=select_options(("over", "Fill over the last color"), ("drain", "Fill, then drain to dark"))),
    ]
    PREVIEW = [(255, 0, 0), (0, 255, 0), (255, 255, 255), (0, 90, 255)]

    def setup(self):
        self._cycle = -1
        self._order = list(range(self.n))

    def render(self, t):
        colors = self.p("colors")
        duration = self.p("duration")
        drain = self.p("mode") == "drain"
        phases = 2 if drain else 1
        pos = t / duration
        cycle = int(pos)
        if cycle != self._cycle:
            self._cycle = cycle
            random.shuffle(self._order)
        frac = pos - cycle
        c = (cycle // phases) % len(colors)
        color = colors[c]
        frame = self.frame
        if drain and cycle % 2 == 1:
            # draining: pixels turn off in the shuffled order
            k = int(frac * self.n)
            for j, i in enumerate(self._order):
                frame[i] = BLACK if j < k else color
        else:
            prev = BLACK if drain else colors[c - 1]
            k = int(frac * self.n)
            for j, i in enumerate(self._order):
                frame[i] = color if j < k else prev


class Rainbow(Animation):
    LABEL = "Rainbow"
    DESCRIPTION = "Every color of the spectrum flowing over the tree."
    CATEGORY = "Motion"
    PARAMS = [
        Param("mode", "select", "Layout", "spiral",
              options=select_options(("spiral", "Spiral"), ("height", "Bottom → top"),
                                     ("strand", "Along the wire"), ("whole", "Whole tree, one color"))),
        Param("density", "number", "Rainbows on tree", 1, min=0.25, max=4, step=0.25),
        Param("tempo", "number", "Speed", 0.15, min=0.02, max=1, step=0.01),
        Param("saturation", "number", "Saturation", 1, min=0.3, max=1, step=0.05),
    ]
    PREVIEW = [hsv(h / 6) for h in range(6)]

    def render(self, t):
        mode = self.p("mode")
        density = self.p("density")
        sat = self.p("saturation")
        base = t * self.p("tempo")
        tree = self.tree
        frame = self.frame
        for i in range(self.n):
            if mode == "whole":
                pos = 0
            elif mode == "height":
                pos = tree.height[i]
            elif mode == "strand":
                pos = i / self.n
            else:
                pos = tree.height[i] * 0.6 + tree.angle[i] * 0.4
            frame[i] = hsv(base + pos * density, sat, 1.0)

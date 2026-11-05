#!/usr/bin/env python3
# More showpieces: ornaments and a rotating beacon.

import math
import random

from ..base import Animation, Param, select_options
from ..colors import BLACK, WHITE, GOLD, gradient, lerp, scale, maximum


class Ornaments(Animation):
    LABEL = "Ornaments"
    DESCRIPTION = "A softly glowing green tree dotted with glinting colored baubles and a star on top."
    CATEGORY = "Showpiece"
    PARAMS = [
        Param("tree", "color", "Tree color", (0, 70, 10)),
        Param("colors", "colors", "Ornament colors", [(255, 0, 0), (255, 170, 0), (0, 80, 255), (255, 0, 200)]),
        Param("density", "number", "Ornaments", 0.3, min=0.05, max=0.8, step=0.05),
        Param("star", "boolean", "Star on top", True),
        Param("tempo", "number", "Glint speed", 1, min=0.2, max=3, step=0.1),
    ]
    PREVIEW = [(0, 70, 10), (255, 0, 0), (255, 170, 0), (0, 80, 255)]

    def setup(self):
        self._reseed()

    def on_params_changed(self):
        self._reseed()

    def _reseed(self):
        rnd = random.Random(2024)
        colors = self.p("colors")
        density = self.p("density")
        self._orn = [rnd.choice(colors) if rnd.random() < density else None for _ in range(self.n)]
        self._phase = [rnd.uniform(0, 6.28) for _ in range(self.n)]
        self._freq = [rnd.uniform(0.5, 1.5) for _ in range(self.n)]

    def render(self, t):
        tree = self.p("tree")
        tempo = self.p("tempo")
        star = self.p("star")
        top = self.tree.ring_start[-1] if star else self.n
        frame = self.frame
        for i in range(self.n):
            if i >= top:
                frame[i] = scale(GOLD, 0.7 + 0.3 * math.sin(t * 3 + self._phase[i]))
                continue
            orn = self._orn[i]
            if orn is None:
                frame[i] = scale(tree, 0.85 + 0.15 * math.sin(t * 0.5 * tempo + self._phase[i]))
            else:
                glint = max(0.0, math.sin(t * self._freq[i] * tempo + self._phase[i])) ** 8
                frame[i] = lerp(orn, WHITE, glint * 0.8)


class Beacon(Animation):
    LABEL = "Beacon"
    DESCRIPTION = "A lighthouse beam sweeps around the tree, leaving a glowing trail."
    CATEGORY = "Showpiece"
    PARAMS = [
        Param("color", "color", "Beam color", (255, 230, 150)),
        Param("background", "color", "Background", (0, 0, 20)),
        Param("beams", "number", "Beams", 1, min=1, max=4, step=1),
        Param("width", "number", "Beam width", 0.12, min=0.03, max=0.4, step=0.01),
        Param("duration", "number", "Seconds per turn", 3, min=0.5, max=12, step=0.1),
        Param("twist", "number", "Twist", 0.5, min=0, max=3, step=0.1, help="Tilt the beam into a spiral going up."),
        Param("direction", "select", "Direction", "cw",
              options=select_options(("cw", "Clockwise"), ("ccw", "Counter-clockwise"))),
    ]
    PREVIEW = [(255, 230, 150), (0, 0, 20)]

    def render(self, t):
        color = self.p("color")
        bg = self.p("background")
        beams = int(self.p("beams"))
        width = self.p("width")
        twist = self.p("twist")
        turn = (t / self.p("duration")) * (1 if self.p("direction") == "cw" else -1)
        tree = self.tree
        frame = self.frame
        for i in range(self.n):
            a = (tree.angle[i] + tree.height[i] * twist - turn) * beams
            d = abs(a - round(a)) / beams          # angular distance to nearest beam
            level = math.exp(-(d / width) ** 2 * 3)
            frame[i] = lerp(bg, color, level)

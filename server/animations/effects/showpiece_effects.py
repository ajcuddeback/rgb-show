#!/usr/bin/env python3
# Showpiece effects: tree-aware set pieces.

import math
import random

from ..base import Animation, Param
from ..colors import WHITE, GOLD, gradient, lerp, scale


class TreeStar(Animation):
    NAME = "treestar"
    LABEL = "Tree Top Star"
    DESCRIPTION = "A gradient-lit tree with a brilliant pulsing star on the top wrap and a soft shimmer below."
    CATEGORY = "Showpiece"
    PARAMS = [
        Param("colors", "colors", "Tree colors (bottom → top)", [(0, 90, 0), (0, 200, 40)], min_items=1),
        Param("star", "color", "Star color", (255, 230, 140)),
        Param("star_size", "number", "Star lights", 5, min=1, max=20, step=1),
        Param("tempo", "number", "Pulse speed", 0.6, min=0.1, max=3, step=0.05),
        Param("shimmer", "number", "Shimmer", 0.3, min=0, max=1, step=0.05),
    ]
    PREVIEW = [(0, 90, 0), (0, 200, 40), (255, 230, 140)]

    def setup(self):
        rnd = random.Random(3)
        self._ph = [rnd.uniform(0, 6.28) for _ in range(self.n)]
        self._fq = [rnd.uniform(0.8, 2.5) for _ in range(self.n)]

    def render(self, t):
        colors = self.p("colors")
        star = self.p("star")
        star_size = int(self.p("star_size"))
        tempo = self.p("tempo")
        shimmer = self.p("shimmer")
        tree = self.tree
        frame = self.frame
        pulse = 0.65 + 0.35 * math.sin(t * tempo * 2 * math.pi)
        star_set = set(tree.top_pixels(star_size))
        for i in range(self.n):
            if i in star_set:
                # Twinkly star: pulse plus a little per-pixel glitter
                glitter = 0.85 + 0.15 * math.sin(t * 7 + self._ph[i])
                frame[i] = scale(star, min(1.0, pulse * glitter + 0.1))
            else:
                body = gradient(colors, tree.height[i], wrap=False)
                wobble = 1 - shimmer * (0.5 + 0.5 * math.sin(t * self._fq[i] + self._ph[i]))
                frame[i] = scale(body, 0.55 + 0.45 * wobble)

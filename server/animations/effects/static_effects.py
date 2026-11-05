#!/usr/bin/env python3
# Static effects: no motion, low frame rate. These replace the old
# singlecolor / multicolors / staticxmas animations.

from ..base import Animation, Param, select_options
from ..colors import XMAS_CLASSIC, WARM_WHITE, gradient


class Solid(Animation):
    LABEL = "Solid Color"
    DESCRIPTION = "Every light the same color."
    CATEGORY = "Static"
    FPS = 5
    PARAMS = [Param("color", "color", "Color", WARM_WHITE)]
    PREVIEW = [WARM_WHITE]

    def render(self, t):
        self.fill(self.p("color"))


class Pattern(Animation):
    LABEL = "Repeating Pattern"
    DESCRIPTION = "Your colors repeated down the strand, like a classic multicolor set."
    CATEGORY = "Static"
    FPS = 5
    PARAMS = [
        Param("colors", "colors", "Colors", XMAS_CLASSIC),
        Param("block", "number", "Lights per color", 1, min=1, max=10, step=1),
    ]
    PREVIEW = XMAS_CLASSIC

    def render(self, t):
        colors = self.p("colors")
        block = max(1, int(self.p("block")))
        self.frame = [colors[(i // block) % len(colors)] for i in range(self.n)]


class Gradient(Animation):
    LABEL = "Gradient"
    DESCRIPTION = "A smooth blend between your colors from the bottom of the tree to the top."
    CATEGORY = "Static"
    FPS = 5
    PARAMS = [
        Param("colors", "colors", "Colors", [(255, 0, 0), (255, 170, 0), (255, 255, 255)], min_items=2),
        Param("axis", "select", "Blend along", "height",
              options=select_options(("height", "Bottom → top"), ("strand", "Along the wire"), ("angle", "Around the tree"))),
    ]
    PREVIEW = [(255, 0, 0), (255, 170, 0), (255, 255, 255)]

    def render(self, t):
        colors = self.p("colors")
        axis = self.p("axis")
        tree = self.tree
        if axis == "angle":
            self.frame = [gradient(colors, tree.angle[i], wrap=True) for i in range(self.n)]
        elif axis == "strand":
            self.frame = [gradient(colors, i / max(1, self.n - 1), wrap=False) for i in range(self.n)]
        else:
            self.frame = [gradient(colors, tree.height[i], wrap=False) for i in range(self.n)]

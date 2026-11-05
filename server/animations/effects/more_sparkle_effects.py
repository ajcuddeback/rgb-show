#!/usr/bin/env python3
# More sparkle effects: confetti and rainbow comets.

import random

from ..base import Animation, Param, select_options
from ..colors import BLACK, WHITE, XMAS_CLASSIC, lerp, scale, maximum, random_color, hsv


class Confetti(Animation):
    LABEL = "Confetti"
    DESCRIPTION = "Bursts of color pop on all over the tree and fade away."
    CATEGORY = "Sparkle"
    PARAMS = [
        Param("colors", "colors", "Colors", XMAS_CLASSIC),
        Param("background", "color", "Background", BLACK),
        Param("rate", "number", "Pops per second", 25, min=2, max=120, step=1),
        Param("fade", "number", "Fade time (s)", 1.2, min=0.2, max=5, step=0.1),
    ]
    PREVIEW = XMAS_CLASSIC

    def setup(self):
        self._born = [-99.0] * self.n
        self._color = [BLACK] * self.n
        self._carry = 0.0

    def render(self, t):
        colors = self.p("colors")
        bg = self.p("background")
        fade = self.p("fade")
        self._carry += self.p("rate") / self.fps
        while self._carry >= 1:
            self._carry -= 1
            i = random.randrange(self.n)
            self._born[i] = t
            self._color[i] = random_color(colors)
        frame = self.frame
        for i in range(self.n):
            age = t - self._born[i]
            level = max(0.0, 1 - age / fade) if age >= 0 else 0.0
            frame[i] = lerp(bg, self._color[i], level * level) if level > 0 else bg


class RainbowComet(Animation):
    NAME = "rainbowcomet"
    LABEL = "Rainbow Comet"
    DESCRIPTION = "A white-hot comet with a tail that trails through every color."
    CATEGORY = "Sparkle"
    PARAMS = [
        Param("tail", "number", "Tail length", 25, min=5, max=60, step=1),
        Param("duration", "number", "Seconds per lap", 3, min=0.5, max=10, step=0.1),
        Param("bounce", "boolean", "Bounce instead of loop", False),
        Param("background", "color", "Background", BLACK),
    ]
    PREVIEW = [WHITE, hsv(0.0), hsv(0.17), hsv(0.33), hsv(0.6), hsv(0.8)]

    def render(self, t):
        tail = self.p("tail")
        bg = self.p("background")
        n = self.n
        phase = t / self.p("duration")
        if self.p("bounce"):
            p = phase % 2
            pos = (p if p <= 1 else 2 - p) * (n - 1)
            direction = 1 if p <= 1 else -1
        else:
            pos = (phase % 1) * (n + tail) - tail / 2
            direction = 1
        frame = self.frame
        for i in range(n):
            behind = (pos - i) * direction
            if 0 <= behind <= tail:
                level = (1 - behind / tail) ** 1.5
                hue = (behind / tail) * 0.85 + t * 0.1
                c = lerp(hsv(hue), WHITE, max(0.0, 1 - behind * 1.5))
                frame[i] = lerp(bg, c, level)
            else:
                frame[i] = bg

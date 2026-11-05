#!/usr/bin/env python3
# Nature effects: snow, fire, candles, aurora and plasma.

import math
import random

from ..base import Animation, Param, select_options
from ..colors import (WHITE, BLACK, WARM_WHITE, AURORA, FIRE, gradient, lerp, scale, maximum, hsv)


class Snow(Animation):
    LABEL = "Snowfall"
    DESCRIPTION = "Snowflakes drift down the tree over a quiet winter background."
    CATEGORY = "Nature"
    PARAMS = [
        Param("background", "color", "Background", (0, 10, 40)),
        Param("flake", "color", "Snowflake color", WHITE),
        Param("count", "number", "Snowflakes", 10, min=1, max=30, step=1),
        Param("tempo", "number", "Fall speed", 1, min=0.2, max=3, step=0.1),
        Param("pile", "boolean", "Snow piles up at the bottom", True),
    ]
    PREVIEW = [(0, 10, 40), WHITE]

    def setup(self):
        self._flakes = []

    def _spawn(self, t):
        return {"t0": t + random.uniform(0, 2.5), "v": random.uniform(8, 22), "len": random.uniform(2, 4)}

    def render(self, t):
        bg = self.p("background")
        fc = self.p("flake")
        count = int(self.p("count"))
        tempo = self.p("tempo")
        n = self.n
        tree = self.tree

        while len(self._flakes) < count:
            self._flakes.append(self._spawn(t))
        self._flakes = self._flakes[:count]

        frame = self.frame
        for i in range(n):
            frame[i] = bg

        if self.p("pile"):
            # a soft snowdrift on the bottom wrap
            for i in tree.pixels_in_ring(0):
                frame[i] = lerp(bg, fc, 0.35)

        for idx, f in enumerate(self._flakes):
            age = t - f["t0"]
            if age < 0:
                continue
            head = (n - 1) - age * f["v"] * tempo      # falls toward index 0 = bottom
            if head < -f["len"]:
                self._flakes[idx] = self._spawn(t)
                continue
            lo, hi = int(max(0, head)), int(min(n - 1, head + f["len"]))
            for i in range(lo, hi + 1):
                above = i - head
                level = max(0.0, 1 - above / f["len"])
                frame[i] = maximum(frame[i], lerp(bg, fc, level))


class Fire(Animation):
    LABEL = "Fireplace"
    DESCRIPTION = "Flickering flames, hottest at the bottom and licking up toward the top."
    CATEGORY = "Nature"
    PARAMS = [
        Param("palette", "select", "Flame color", "ember",
              options=select_options(("ember", "Classic fire"), ("blue", "Blue gas flame"),
                                     ("green", "Green fire"), ("purple", "Purple fire"), ("ice", "Ice"))),
        Param("intensity", "number", "Flame height", 0.75, min=0.2, max=1, step=0.05),
        Param("tempo", "number", "Flicker speed", 1, min=0.3, max=3, step=0.1),
    ]
    PREVIEW = [(120, 0, 0), (255, 60, 0), (255, 170, 0), (255, 255, 160)]

    PALETTES = {
        "ember": FIRE,
        "blue": [BLACK, (0, 0, 90), (0, 60, 255), (120, 200, 255), WHITE],
        "green": [BLACK, (0, 60, 0), (0, 200, 40), (160, 255, 60), (240, 255, 200)],
        "purple": [BLACK, (50, 0, 80), (160, 0, 255), (255, 80, 200), (255, 220, 255)],
        "ice": [BLACK, (0, 30, 60), (0, 120, 200), (150, 220, 255), WHITE],
    }

    def setup(self):
        rnd = random.Random(42)
        self._f1 = [rnd.uniform(1.5, 3.5) for _ in range(self.n)]
        self._f2 = [rnd.uniform(4, 9) for _ in range(self.n)]
        self._ph1 = [rnd.uniform(0, 6.28) for _ in range(self.n)]
        self._ph2 = [rnd.uniform(0, 6.28) for _ in range(self.n)]

    def render(self, t):
        palette = self.PALETTES.get(self.p("palette"), FIRE)
        intensity = self.p("intensity")
        tt = t * self.p("tempo")
        tree = self.tree
        frame = self.frame
        for i in range(self.n):
            flicker = 0.6 + 0.25 * math.sin(tt * self._f1[i] + self._ph1[i]) + 0.15 * math.sin(tt * self._f2[i] + self._ph2[i])
            heat = (1.15 - tree.height[i]) * intensity * flicker + random.uniform(-0.05, 0.05)
            frame[i] = gradient(palette, max(0.0, min(0.999, heat)), wrap=False)


class Candle(Animation):
    LABEL = "Candlelight"
    DESCRIPTION = "Warm, gently flickering candle glow."
    CATEGORY = "Nature"
    PARAMS = [
        Param("color", "color", "Color", WARM_WHITE),
        Param("flicker", "number", "Flicker", 0.35, min=0.05, max=0.9, step=0.05),
        Param("tempo", "number", "Flicker speed", 1, min=0.3, max=3, step=0.1),
    ]
    PREVIEW = [WARM_WHITE]

    def setup(self):
        rnd = random.Random(7)
        self._f1 = [rnd.uniform(0.8, 2.0) for _ in range(self.n)]
        self._f2 = [rnd.uniform(3, 6) for _ in range(self.n)]
        self._ph = [rnd.uniform(0, 6.28) for _ in range(self.n)]

    def render(self, t):
        color = self.p("color")
        flicker = self.p("flicker")
        tt = t * self.p("tempo")
        frame = self.frame
        for i in range(self.n):
            wobble = 0.5 + 0.35 * math.sin(tt * self._f1[i] + self._ph[i]) + 0.15 * math.sin(tt * self._f2[i])
            level = 1 - flicker * wobble + random.uniform(-0.03, 0.03)
            frame[i] = scale(color, max(0.1, min(1.0, level)))


class Aurora(Animation):
    LABEL = "Northern Lights"
    DESCRIPTION = "Slow curtains of green, teal and violet drifting around the tree."
    CATEGORY = "Nature"
    PARAMS = [
        Param("colors", "colors", "Colors", AURORA, min_items=2),
        Param("tempo", "number", "Drift speed", 0.5, min=0.1, max=2, step=0.05),
        Param("curtains", "number", "Curtains", 2, min=1, max=5, step=0.5),
    ]
    PREVIEW = AURORA

    def render(self, t):
        colors = self.p("colors")
        tt = t * self.p("tempo")
        k = self.p("curtains")
        tree = self.tree
        frame = self.frame
        for i in range(self.n):
            a, h = tree.angle[i], tree.height[i]
            v = 0.5 + 0.5 * math.sin(a * 6.283 * k + tt + math.sin(h * 3 + tt * 0.7))
            glow = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(h * 4.5 - tt * 1.3 + a * 6.283))
            frame[i] = scale(gradient(colors, v), glow)


class Plasma(Animation):
    LABEL = "Plasma"
    DESCRIPTION = "Hypnotic, lava-lamp swirls of color across the whole tree."
    CATEGORY = "Nature"
    PARAMS = [
        Param("colors", "colors", "Colors", [(255, 0, 90), (255, 140, 0), (0, 200, 255), (120, 0, 255)], min_items=2),
        Param("scale", "number", "Pattern size", 2, min=0.5, max=5, step=0.25),
        Param("tempo", "number", "Speed", 0.6, min=0.1, max=3, step=0.1),
    ]
    PREVIEW = [(255, 0, 90), (255, 140, 0), (0, 200, 255), (120, 0, 255)]

    def render(self, t):
        colors = self.p("colors")
        s = self.p("scale")
        tt = t * self.p("tempo")
        tree = self.tree
        frame = self.frame
        for i in range(self.n):
            x, y, h = tree.x[i], tree.y[i], tree.height[i]
            v = (math.sin(x * s + tt) + math.sin(y * s - tt * 0.7)
                 + math.sin((x + y) * s * 0.5 + tt * 0.3) + math.sin(h * s * 2 + tt))
            frame[i] = gradient(colors, (v + 4) / 8)

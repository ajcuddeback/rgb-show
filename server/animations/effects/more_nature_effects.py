#!/usr/bin/env python3
# More nature effects: fireflies, icicles, starry night.

import math
import random

from ..base import Animation, Param
from ..colors import BLACK, WHITE, lerp, scale, maximum
from tree import angular_distance


class Fireflies(Animation):
    LABEL = "Fireflies"
    DESCRIPTION = "Soft yellow-green glows blink on, drift a little, and fade into the dark."
    CATEGORY = "Nature"
    PARAMS = [
        Param("color", "color", "Glow color", (200, 255, 60)),
        Param("background", "color", "Background", (0, 4, 0)),
        Param("count", "number", "Fireflies", 12, min=1, max=40, step=1),
        Param("tempo", "number", "Blink speed", 1, min=0.3, max=3, step=0.1),
    ]
    PREVIEW = [(200, 255, 60), (0, 4, 0)]

    def setup(self):
        self._flies = []

    def _spawn(self, t):
        return {"t0": t + random.uniform(0, 3), "pos": random.uniform(0, self.n - 1),
                "drift": random.uniform(-1.5, 1.5), "life": random.uniform(2, 5)}

    def render(self, t):
        color = self.p("color")
        bg = self.p("background")
        count = int(self.p("count"))
        tempo = self.p("tempo")
        while len(self._flies) < count:
            self._flies.append(self._spawn(t))
        self._flies = self._flies[:count]
        frame = self.frame
        for i in range(self.n):
            frame[i] = bg
        for idx, f in enumerate(self._flies):
            age = (t - f["t0"]) * tempo
            if age < 0:
                continue
            if age > f["life"]:
                self._flies[idx] = self._spawn(t)
                continue
            phase = age / f["life"]
            level = math.sin(phase * math.pi) ** 2 * (0.75 + 0.25 * math.sin(age * 9))
            pos = f["pos"] + f["drift"] * age
            lo = int(pos)
            frac = pos - lo
            for j, w in ((lo, 1 - frac), (lo + 1, frac)):
                if 0 <= j < self.n:
                    frame[j] = maximum(frame[j], lerp(bg, color, level * w))


class Icicles(Animation):
    LABEL = "Icicles"
    DESCRIPTION = "Cold white drips run straight down the tree over a frosty blue glow."
    CATEGORY = "Nature"
    PARAMS = [
        Param("background", "color", "Frost color", (0, 25, 60)),
        Param("drip", "color", "Drip color", (200, 240, 255)),
        Param("count", "number", "Drips", 8, min=1, max=25, step=1),
        Param("length", "number", "Drip length", 0.18, min=0.05, max=0.5, step=0.01),
        Param("tempo", "number", "Speed", 1, min=0.2, max=3, step=0.1),
    ]
    PREVIEW = [(200, 240, 255), (0, 25, 60)]

    def setup(self):
        self._drips = []

    def _spawn(self, t):
        return {"t0": t + random.uniform(0, 2), "angle": random.random(), "start": random.uniform(0.45, 1.0),
                "dist": random.uniform(0.2, 0.6), "v": random.uniform(0.15, 0.4)}

    def render(self, t):
        bg = self.p("background")
        dc = self.p("drip")
        count = int(self.p("count"))
        length = self.p("length")
        tempo = self.p("tempo")
        tree = self.tree
        n = self.n
        while len(self._drips) < count:
            self._drips.append(self._spawn(t))
        self._drips = self._drips[:count]
        frame = self.frame
        for i in range(n):
            frame[i] = scale(bg, 0.8 + 0.2 * math.sin(t * 0.7 + i * 0.3))
        for idx, d in enumerate(self._drips):
            age = t - d["t0"]
            if age < 0:
                continue
            travelled = age * d["v"] * tempo
            if travelled > d["dist"] + length:
                self._drips[idx] = self._spawn(t)
                continue
            head = d["start"] - travelled
            melt = max(0.0, 1 - max(0.0, travelled - d["dist"]) / length)
            for i in range(n):
                above = tree.z[i] - head
                if above < 0 or above > length:
                    continue
                reach = 0.06 / max(0.25, tree.radius[i])
                ad = angular_distance(tree.angle[i], d["angle"])
                if ad > reach:
                    continue
                level = (1 - above / length) * (1 - ad / reach) * melt
                frame[i] = maximum(frame[i], lerp(bg, dc, level))


class StarryNight(Animation):
    NAME = "starrynight"
    LABEL = "Starry Night"
    DESCRIPTION = "A deep midnight sky with twinkling stars and the occasional shooting star."
    CATEGORY = "Nature"
    PARAMS = [
        Param("sky", "color", "Sky color", (2, 0, 24)),
        Param("star", "color", "Star color", (255, 245, 220)),
        Param("density", "number", "Stars", 0.18, min=0.02, max=0.6, step=0.02),
        Param("shooting", "number", "Shooting stars per minute", 6, min=0, max=30, step=1),
    ]
    PREVIEW = [(2, 0, 24), (255, 245, 220)]

    def setup(self):
        rnd = random.Random(11)
        self._phase = [rnd.uniform(0, 6.28) for _ in range(self.n)]
        self._freq = [rnd.uniform(0.3, 1.4) for _ in range(self.n)]
        self._is_star = [rnd.random() for _ in range(self.n)]
        self._next_shoot = 2.0
        self._shoot = None

    def render(self, t):
        sky = self.p("sky")
        star = self.p("star")
        density = self.p("density")
        frame = self.frame
        for i in range(self.n):
            if self._is_star[i] < density:
                tw = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * self._freq[i] * 2 + self._phase[i])) ** 3
                frame[i] = lerp(sky, star, tw)
            else:
                frame[i] = sky
        per_min = self.p("shooting")
        if self._shoot is None and per_min > 0 and t >= self._next_shoot:
            self._shoot = {"t0": t, "start": random.randint(int(self.n * 0.5), self.n - 1), "v": random.uniform(40, 80)}
            self._next_shoot = t + random.expovariate(per_min / 60.0)
        if self._shoot is not None:
            s = self._shoot
            head = s["start"] - (t - s["t0"]) * s["v"]
            if head < -12:
                self._shoot = None
            else:
                for k in range(12):
                    i = int(head) + k
                    if 0 <= i < self.n:
                        frame[i] = maximum(frame[i], scale(WHITE, (1 - k / 12) ** 2))

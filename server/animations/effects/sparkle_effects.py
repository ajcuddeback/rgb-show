#!/usr/bin/env python3
# Sparkle effects: twinkles, glints, meteors and fireworks.

import math
import random

from ..base import Animation, Param, select_options
from ..colors import (XMAS, WHITE, BLACK, GOLD, WARM_WHITE, lerp, scale, maximum, random_color)
from tree import angular_distance


class Twinkle(Animation):
    LABEL = "Twinkle"
    DESCRIPTION = "Lights softly fade in and out at random, like a tree full of stars."
    CATEGORY = "Sparkle"
    PARAMS = [
        Param("colors", "colors", "Twinkle colors", [WARM_WHITE, WHITE, GOLD]),
        Param("background", "color", "Background", (6, 0, 20)),
        Param("density", "number", "Density", 0.35, min=0.05, max=1, step=0.05),
        Param("tempo", "number", "Twinkle speed", 1, min=0.2, max=4, step=0.1),
    ]
    PREVIEW = [WARM_WHITE, WHITE, GOLD]

    def setup(self):
        self._start = [-10.0] * self.n
        self._dur = [1.0] * self.n
        self._color = [WHITE] * self.n
        self._next = [random.uniform(0, 3) for _ in range(self.n)]

    def render(self, t):
        colors = self.p("colors")
        bg = self.p("background")
        density = self.p("density")
        tempo = self.p("tempo")
        frame = self.frame
        for i in range(self.n):
            end = self._start[i] + self._dur[i]
            if t >= end:
                if t >= self._next[i]:
                    dur = random.uniform(0.8, 2.2) / tempo
                    self._start[i], self._dur[i] = t, dur
                    self._color[i] = random_color(colors)
                    # Longer waits for lower density; keeps roughly `density` of lights active.
                    self._next[i] = t + dur + random.uniform(0.2, 1.2) * dur * (1 / density - 1)
                    end = t + dur
                else:
                    frame[i] = bg
                    continue
            phase = (t - self._start[i]) / self._dur[i]
            level = math.sin(phase * math.pi) ** 1.6
            frame[i] = lerp(bg, self._color[i], level)


class Sparkle(Animation):
    LABEL = "Sparkle"
    DESCRIPTION = "A solid color with quick bright glints dancing over it."
    CATEGORY = "Sparkle"
    PARAMS = [
        Param("color", "color", "Base color", (160, 0, 0)),
        Param("glint", "color", "Glint color", WHITE),
        Param("density", "number", "Glints", 0.08, min=0.01, max=0.5, step=0.01),
        Param("tempo", "number", "Glint speed", 1, min=0.3, max=3, step=0.1),
    ]
    PREVIEW = [(160, 0, 0), WHITE]

    def setup(self):
        self._until = [0.0] * self.n
        self._len = [0.1] * self.n

    def render(self, t):
        base = self.p("color")
        glint = self.p("glint")
        density = self.p("density")
        tempo = self.p("tempo")
        per_frame = density * tempo / self.fps * 4
        frame = self.frame
        for i in range(self.n):
            if t < self._until[i]:
                remaining = (self._until[i] - t) / self._len[i]
                frame[i] = lerp(base, glint, remaining)
            else:
                if random.random() < per_frame:
                    self._len[i] = random.uniform(0.08, 0.3) / tempo
                    self._until[i] = t + self._len[i]
                    frame[i] = glint
                else:
                    frame[i] = base


class Meteor(Animation):
    LABEL = "Meteor Shower"
    DESCRIPTION = "Shooting stars streak along the strand with glowing tails."
    CATEGORY = "Sparkle"
    PARAMS = [
        Param("colors", "colors", "Meteor colors", [WHITE, (120, 200, 255), GOLD]),
        Param("background", "color", "Background", BLACK),
        Param("count", "number", "Meteors", 3, min=1, max=8, step=1),
        Param("tail", "number", "Tail length", 14, min=3, max=40, step=1),
        Param("tempo", "number", "Speed", 1, min=0.2, max=4, step=0.1),
        Param("direction", "select", "Direction", "up",
              options=select_options(("up", "Up the tree"), ("down", "Down the tree"), ("both", "Both ways"))),
    ]
    PREVIEW = [WHITE, (120, 200, 255), GOLD]

    def setup(self):
        self._meteors = []

    def _spawn(self, t, direction, colors):
        d = direction if direction != "both" else random.choice(["up", "down"])
        return {
            "t0": t + random.uniform(0, 1.5),
            "v": random.uniform(25, 60),
            "dir": 1 if d == "up" else -1,
            "color": random_color(colors),
        }

    def render(self, t):
        colors = self.p("colors")
        bg = self.p("background")
        count = int(self.p("count"))
        tail = max(1.0, self.p("tail"))
        tempo = self.p("tempo")
        direction = self.p("direction")
        n = self.n

        while len(self._meteors) < count:
            self._meteors.append(self._spawn(t, direction, colors))
        if len(self._meteors) > count:
            self._meteors = self._meteors[:count]

        frame = self.frame
        for i in range(n):
            frame[i] = bg

        for idx, m in enumerate(self._meteors):
            age = t - m["t0"]
            if age < 0:
                continue
            dist = age * m["v"] * tempo
            if dist > n + tail:
                self._meteors[idx] = self._spawn(t, direction, colors)
                continue
            head = dist if m["dir"] > 0 else n - 1 - dist
            color = m["color"]
            lo = int(max(0, min(head, head - m["dir"] * tail)))
            hi = int(min(n - 1, max(head, head - m["dir"] * tail)))
            for i in range(lo, hi + 1):
                behind = (head - i) * m["dir"]
                if 0 <= behind <= tail:
                    level = (1 - behind / tail) ** 2
                    frame[i] = maximum(frame[i], scale(color, level))


class Fireworks(Animation):
    LABEL = "Fireworks"
    DESCRIPTION = "Rockets climb one side of the tree and burst into expanding spheres of color."
    CATEGORY = "Showpiece"
    PARAMS = [
        Param("colors", "colors", "Burst colors", [(255, 40, 40), (60, 255, 80), (80, 120, 255), GOLD, WHITE]),
        Param("rate", "number", "Launches per second", 0.7, min=0.1, max=3, step=0.1),
        Param("size", "number", "Burst size", 0.7, min=0.15, max=1.4, step=0.05),
        Param("background", "color", "Background", BLACK),
    ]
    PREVIEW = [(255, 40, 40), (60, 255, 80), (80, 120, 255), GOLD]

    LAUNCH = 0.9   # seconds for the rocket to climb
    LIFE = 1.6     # seconds the burst lasts

    def setup(self):
        self._shells = []
        self._next_launch = 0.5

    def render(self, t):
        colors = self.p("colors")
        rate = self.p("rate")
        size = self.p("size")
        bg = self.p("background")
        tree = self.tree
        n = self.n

        if t >= self._next_launch:
            self._shells.append({"t0": t, "angle": random.random(), "top": random.uniform(0.45, 0.95),
                                 "color": random_color(colors)})
            self._next_launch = t + random.expovariate(rate) if rate > 0 else t + 9999
            self._shells = self._shells[-10:]

        frame = self.frame
        for i in range(n):
            frame[i] = bg

        alive = []
        for s_ in self._shells:
            age = t - s_["t0"]
            if age < self.LAUNCH:
                # rocket: a bright spark rising up one side of the tree
                h = s_["top"] * (age / self.LAUNCH) ** 0.8
                for i in range(n):
                    dh = h - tree.z[i]
                    if dh < 0 or dh > 0.08:
                        continue
                    ad = angular_distance(tree.angle[i], s_["angle"])
                    reach = 0.05 / max(0.25, tree.radius[i])
                    if ad < reach:
                        frame[i] = maximum(frame[i], scale(WHITE, (1 - dh / 0.08) * (1 - ad / reach)))
                alive.append(s_)
            elif age < self.LAUNCH + self.LIFE:
                burst = (age - self.LAUNCH) / self.LIFE
                radius = size * (1 - (1 - burst) ** 2)
                fade = (1 - burst) ** 1.5
                ca = s_["angle"] * 2 * math.pi
                cr = 1 - 0.9 * s_["top"]
                cx, cy, cz = cr * math.cos(ca), cr * math.sin(ca), s_["top"]
                for i in range(n):
                    d = math.sqrt((tree.x[i] - cx) ** 2 + (tree.y[i] - cy) ** 2 + ((tree.z[i] - cz) * 2.2) ** 2)
                    if d > radius + 0.16:
                        continue
                    shell = max(0.0, 1 - abs(d - radius) / 0.16)
                    inner = max(0.0, 1 - d / max(0.05, radius)) * 0.4
                    level = (shell + inner) * fade
                    if level > 0:
                        frame[i] = maximum(frame[i], scale(s_["color"], min(1.0, level)))
                alive.append(s_)
        self._shells = alive

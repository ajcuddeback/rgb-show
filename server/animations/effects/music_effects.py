#!/usr/bin/env python3
# Music-reactive effects. They read self.af, refreshed every frame by the base
# class from the audio engine:
#   level / bass / mid / treble  0..1 (auto-gained)
#   beat (bool this frame), beat_env (1 on the beat, decaying), bpm, phase, active
# With audio off they fall back to a gentle idle look instead of a dark tree.

import math
import random

from ..base import Animation, Param, select_options
from ..colors import BLACK, WHITE, GOLD, gradient, lerp, scale, maximum, hsv


class VuMeter(Animation):
    NAME = "vumeter"
    LABEL = "VU Meter"
    DESCRIPTION = "The bass fills the tree from the bottom; a peak marker rides the top."
    CATEGORY = "Music"
    PARAMS = [
        Param("colors", "colors", "Gradient (bottom → top)", [(0, 200, 80), (255, 200, 0), (255, 30, 30)], min_items=2),
        Param("band", "select", "Follow", "bass", options=select_options(("bass", "Bass"), ("level", "Overall loudness"), ("mid", "Mids"))),
        Param("background", "color", "Background", (2, 2, 8)),
        Param("peak", "boolean", "Peak marker", True),
    ]
    PREVIEW = [(0, 200, 80), (255, 200, 0), (255, 30, 30)]

    def setup(self):
        self._peak = 0.0

    def render(self, t):
        colors = self.p("colors")
        bg = self.p("background")
        v = float(self.af.get(self.p("band"), 0.0))
        if not self.af.get("active"):
            v = 0.15 + 0.1 * math.sin(t * 1.5)          # idle breathing so the tree isn't dark
        self._peak = max(v, self._peak - 0.012)
        tree = self.tree
        frame = self.frame
        for i in range(self.n):
            z = tree.z[i]
            if z <= v:
                frame[i] = gradient(colors, z, wrap=False)
            elif self.p("peak") and abs(z - self._peak) < 0.03:
                frame[i] = WHITE
            else:
                frame[i] = bg


class BeatPulse(Animation):
    NAME = "beatpulse"
    LABEL = "Beat Pulse"
    DESCRIPTION = "Every beat fires a sphere of light out from the heart of the tree."
    CATEGORY = "Music"
    PARAMS = [
        Param("colors", "colors", "Pulse colors", [WHITE, (255, 0, 90), (0, 180, 255), GOLD]),
        Param("background", "color", "Background", (6, 0, 14)),
        Param("speed", "number", "Expansion speed", 1.6, min=0.5, max=4, step=0.1),
        Param("thickness", "number", "Shell thickness", 0.22, min=0.08, max=0.5, step=0.01),
        Param("glow", "boolean", "Glow with loudness", True),
    ]
    PREVIEW = [WHITE, (255, 0, 90), (0, 180, 255), GOLD]

    def setup(self):
        self._pulses = []
        self._ci = 0
        self._last_t = 0.0
        self._idle_next = 0.0

    def render(self, t):
        colors = self.p("colors")
        bg = self.p("background")
        speed = self.p("speed")
        thick = self.p("thickness")
        dt = max(0.0, t - self._last_t)
        self._last_t = t
        active = self.af.get("active")
        fire = bool(self.af.get("beat")) if active else t >= self._idle_next
        if fire:
            if not active:
                self._idle_next = t + 1.0
            self._pulses.append({"r": 0.0, "color": colors[self._ci % len(colors)]})
            self._ci += 1
            self._pulses = self._pulses[-6:]
        for p_ in self._pulses:
            p_["r"] += dt * speed
        self._pulses = [p_ for p_ in self._pulses if p_["r"] < 2.2]
        level = float(self.af.get("level", 0.0)) if (active and self.p("glow")) else 0.0
        base = lerp(bg, scale(colors[0], 0.35), level)
        tree = self.tree
        frame = self.frame
        for i in range(self.n):
            frame[i] = base
        for p_ in self._pulses:
            fade = max(0.0, 1 - p_["r"] / 2.2)
            for i in range(self.n):
                d = math.sqrt(tree.x[i] ** 2 + tree.y[i] ** 2 + ((tree.z[i] - 0.5) * 2.0) ** 2)
                lv = max(0.0, 1 - abs(d - p_["r"]) / thick) * fade
                if lv > 0:
                    frame[i] = maximum(frame[i], scale(p_["color"], lv))


class Spectrum(Animation):
    LABEL = "Spectrum"
    DESCRIPTION = "Bass lights the bottom, mids the middle, treble the top - each in its own color."
    CATEGORY = "Music"
    PARAMS = [
        Param("bass_color", "color", "Bass", (255, 0, 60)),
        Param("mid_color", "color", "Mids", (0, 220, 120)),
        Param("treble_color", "color", "Treble", (120, 160, 255)),
        Param("floor", "number", "Minimum glow", 0.06, min=0, max=0.4, step=0.02),
        Param("sharp", "boolean", "Hard zone edges", False),
    ]
    PREVIEW = [(255, 0, 60), (0, 220, 120), (120, 160, 255)]

    def render(self, t):
        floor = self.p("floor")
        active = self.af.get("active")
        if active:
            vals = [float(self.af.get("bass", 0)), float(self.af.get("mid", 0)), float(self.af.get("treble", 0))]
        else:
            vals = [0.5 + 0.4 * math.sin(t * 1.2 + k) for k in range(3)]
        cols = [self.p("bass_color"), self.p("mid_color"), self.p("treble_color")]
        sharp = self.p("sharp")
        tree = self.tree
        frame = self.frame
        for i in range(self.n):
            z = tree.z[i] * 3                       # 0..3 across the three zones
            k = min(2, int(z))
            if sharp:
                c, v = cols[k], vals[k]
            else:
                f = z - k
                k2 = min(2, k + 1)
                c = lerp(cols[k], cols[k2], f) if f > 0.5 else lerp(cols[max(0, k - 1)], cols[k], f + 0.5) if k > 0 else cols[0]
                v = vals[k] * (1 - abs(f - 0.5)) + (vals[k2] if f > 0.5 else vals[max(0, k - 1)]) * abs(f - 0.5)
            frame[i] = scale(c, floor + (1 - floor) * v)


class EnergyGlow(Animation):
    NAME = "energyglow"
    LABEL = "Energy Glow"
    DESCRIPTION = "The whole tree breathes with the music: warm when it's mellow, bright and cool when it's loud, flashing on hits."
    CATEGORY = "Music"
    PARAMS = [
        Param("colors", "colors", "Quiet → loud", [(120, 0, 60), (255, 80, 0), (255, 220, 120), (200, 240, 255)], min_items=2),
        Param("flash", "number", "Flash on beats", 0.5, min=0, max=1, step=0.05),
        Param("floor", "number", "Minimum glow", 0.12, min=0, max=0.5, step=0.02),
    ]
    PREVIEW = [(120, 0, 60), (255, 80, 0), (255, 220, 120), (200, 240, 255)]

    def render(self, t):
        colors = self.p("colors")
        floor = self.p("floor")
        active = self.af.get("active")
        level = float(self.af.get("level", 0)) if active else 0.4 + 0.3 * math.sin(t * 0.8)
        env = float(self.af.get("beat_env", 0)) if active else 0.0
        c = gradient(colors, level, wrap=False)
        c = lerp(c, WHITE, env * self.p("flash") * 0.6)
        tree = self.tree
        frame = self.frame
        for i in range(self.n):
            # a little vertical texture so it isn't a flat wash
            v = floor + (1 - floor) * min(1.0, level * (0.85 + 0.3 * tree.z[i]))
            frame[i] = scale(c, v)


class BeatChase(Animation):
    NAME = "beatchase"
    LABEL = "Beat Chase"
    DESCRIPTION = "A classic chase that steps forward on every beat of the song."
    CATEGORY = "Music"
    PARAMS = [
        Param("colors", "colors", "Colors", [(255, 0, 0), (0, 255, 0), (255, 255, 255)]),
        Param("block", "number", "Lights per color", 3, min=1, max=10, step=1),
        Param("direction", "select", "Direction", "up", options=select_options(("up", "Up the tree"), ("down", "Down the tree"))),
    ]
    PREVIEW = [(255, 0, 0), (0, 255, 0), (255, 255, 255)]

    def setup(self):
        self._step = 0
        self._idle_next = 0.0

    def render(self, t):
        colors = self.p("colors")
        block = max(1, int(self.p("block")))
        active = self.af.get("active")
        if active:
            if self.af.get("beat"):
                self._step += 1
        elif t >= self._idle_next:
            self._idle_next = t + 0.5
            self._step += 1
        step = self._step if self.p("direction") == "up" else -self._step
        env = float(self.af.get("beat_env", 0.0)) if active else 0.3
        order = self.tree.order_by_height
        frame = self.frame
        for rank, i in enumerate(order):
            c = colors[((rank // block) + step) % len(colors)]
            frame[i] = scale(c, 0.6 + 0.4 * env)

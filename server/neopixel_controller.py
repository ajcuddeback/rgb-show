#!/usr/bin/env python3
# NeoPixel Controller
# Author: Austin Cuddeback (ajcuddeback@gmail.com)
#
# Owns the physical (or simulated) pixel strand. Animations never touch the
# hardware directly: they produce a frame (a list of RGB tuples) and hand it to
# `show_frame`, which applies gamma correction and pushes it out under a lock
# so brightness changes and animation frames never interleave.

import logging
import threading
from typing import List, Optional, Sequence, Tuple

Color = Tuple[int, int, int]

log = logging.getLogger(__name__)


class SimulatedPixels:
    """Drop-in stand-in for neopixel.NeoPixel for development and tests."""

    def __init__(self, n: int, brightness: float = 1.0):
        self.n = n
        self.brightness = brightness
        self._buf: List[Color] = [(0, 0, 0)] * n
        self.show_count = 0

    def __len__(self):
        return self.n

    def __getitem__(self, i):
        return self._buf[i]

    def __setitem__(self, i, value):
        self._buf[i] = tuple(int(c) for c in value[:3])

    def fill(self, color):
        self._buf = [tuple(int(c) for c in color[:3])] * self.n

    def show(self):
        self.show_count += 1

    def deinit(self):
        pass


def _build_gamma_table(gamma: float) -> List[int]:
    if gamma <= 1.0:
        return list(range(256))
    return [int(round(255 * ((i / 255.0) ** gamma))) for i in range(256)]


class NeoPixelController:
    def __init__(self, num_pixels: int, pin_name: str = "D18", brightness: float = 0.1,
                 pixel_order: str = "RGB", gamma: float = 1.0, simulate: bool = False):
        self.num_pixels = num_pixels
        self.pin_name = pin_name
        self.brightness = brightness
        self.gamma = gamma
        self._gamma_table = _build_gamma_table(gamma)
        self._lock = threading.RLock()
        self.simulated = False
        # The last frame handed to show_frame, *before* gamma. Used for the live
        # preview in the UI so what the browser draws matches the intended colors.
        self.last_frame: List[Color] = [(0, 0, 0)] * num_pixels
        self.pixels = self._open_pixels(pin_name, pixel_order, simulate)

    # ------------------------------------------------------------------ setup
    def _open_pixels(self, pin_name: str, pixel_order: str, simulate: bool):
        if not simulate:
            try:
                import board  # type: ignore
                import neopixel  # type: ignore

                pin = getattr(board, pin_name)
                order = getattr(neopixel, pixel_order, neopixel.RGB)
                log.info("Opening %d NeoPixels on %s (%s)", self.num_pixels, pin_name, pixel_order)
                return neopixel.NeoPixel(pin, self.num_pixels, brightness=self.brightness,
                                         auto_write=False, pixel_order=order)
            except Exception as exc:  # ImportError, NotImplementedError off-Pi, permission errors...
                log.warning("NeoPixel hardware unavailable (%s). Falling back to the simulator.", exc)
        self.simulated = True
        return SimulatedPixels(self.num_pixels, self.brightness)

    # --------------------------------------------------------------- commands
    def show_frame(self, frame: Sequence[Color]) -> None:
        """Push a full frame of pre-gamma RGB tuples to the strand."""
        table = self._gamma_table
        with self._lock:
            px = self.pixels
            n = min(len(frame), self.num_pixels)
            for i in range(n):
                r, g, b = frame[i]
                px[i] = (table[_clamp(r)], table[_clamp(g)], table[_clamp(b)])
            self.last_frame = [tuple(c) for c in frame[:n]]
            px.show()

    def turn_off_all_lights(self) -> None:
        with self._lock:
            self.pixels.fill((0, 0, 0))
            self.pixels.show()
            self.last_frame = [(0, 0, 0)] * self.num_pixels

    def change_brightness(self, brightness: float) -> float:
        brightness = max(0.0, min(1.0, float(brightness)))
        with self._lock:
            self.brightness = brightness
            self.pixels.brightness = brightness
            self.pixels.show()
        return brightness

    def get_frame(self) -> List[Color]:
        with self._lock:
            return list(self.last_frame)


def _clamp(v) -> int:
    v = int(v)
    return 0 if v < 0 else 255 if v > 255 else v

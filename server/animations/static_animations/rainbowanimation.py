#!/usr/bin/env python3
# Simple Rainbow Animation
# Author: Austin Cuddeback (ajcuddeback@gmail.com)
#
# Uses the Adafruit animation library
# Displays a simple rainbow animation

from adafruit_led_animation.animation.rainbow import Rainbow
from .StaticAbstractAnimation import StaticAbstractAnimation

class rainbowanimation(StaticAbstractAnimation):
    def run_animation(self):
        self.is_running = True
        rainbow = Rainbow(self.controller.pixels, speed=self.speed, period=2)
        while True:
            rainbow.animate()
            if not self.check_if_is_running():
                break
#!/usr/bin/env python3
# Simple Sparkle Animation
# Author: Austin Cuddeback (ajcuddeback@gmail.com)
#
# Uses the Adafruit animation library
# Displays a simple sparkle animation based on the color passed from the params

from adafruit_led_animation.animation.sparklepulse import SparklePulse
from adafruit_led_animation.sequence import AnimationSequence
from .SingleColorAbstractAnimation import SingleColorAbstractAnimation

class sparkleanimation(SingleColorAbstractAnimation):
    def run_animation(self):
        self.is_running = True
        sparkle_pulse = SparklePulse(self.controller.pixels, speed=self.speed, period=3, color=self.color)

        animations = AnimationSequence(
            sparkle_pulse,
            auto_clear=True,
        )

        while True:
            animations.animate()
            if not self.check_if_is_running():
                break
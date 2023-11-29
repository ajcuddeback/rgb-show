#!/usr/bin/env python3
# Simple Rainbow Animation
# Author: Austin Cuddeback (ajcuddeback@gmail.com)
#
# Uses the Adafruit animation library
# Displays a simple rainbow animation

from adafruit_led_animation.animation.rainbow import Rainbow

class rainbowanimation:
    def __init__(self, neo_pixel_controller, color):
        self.controller = neo_pixel_controller
        self.color = color
        self.is_running = False

    def run_animation(self):
        self.is_running = True
        rainbow = Rainbow(self.controller.pixels, speed=0.1, period=2)
        while True:
            rainbow.animate()
            if not self.check_if_is_running():
                break

    def check_if_is_running(self):
        return self.is_running
    
    def stop(self):
        self.is_running = False
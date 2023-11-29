#!/usr/bin/env python3
# Simple Rainbow Animation
# Author: Austin Cuddeback (ajcuddeback@gmail.com)
#
# Uses the Adafruit animation library
# Displays a simple rainbow animation

from adafruit_led_animation.animation.rainbow import Rainbow
from abc import ABC, abstractmethod


class AbstractAnimation(ABC):
    def __init__(self, neo_pixel_controller, color):
        self.controller = neo_pixel_controller
        self.color = color
        self.is_running = False

    @abstractmethod
    def run_animation(self):
        """
        Method to start and run the animation.
        Should contain a `while True` loop with the animation implementation in it.
        The while True loop needs to contain an if check_if_is_running conditional that should return from the loop.
        """
        pass

    def check_if_is_running(self):
        """
        Method to check if the animation is still running.
        """
        return self.is_running

    def stop(self):
        """
        Method to stop the animation.
        """
        self.is_running = False

class rainbowanimation(AbstractAnimation):
    def run_animation(self):
        self.is_running = True
        rainbow = Rainbow(self.controller.pixels, speed=0.1, period=2)
        while True:
            rainbow.animate()
            if not self.check_if_is_running():
                break
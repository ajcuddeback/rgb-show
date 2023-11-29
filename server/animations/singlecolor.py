#!/usr/bin/env python3
# Single Color Animation
# Author: Austin Cuddeback (ajcuddeback@gmail.com)
#
# Simply lights all lights to the same color based on the color param

import time
from .AbstractAnimation import  AbstractAnimation

class singlecolor(AbstractAnimation):
    def __init__(self, neo_pixel_controller, color):
        super().__init__(neo_pixel_controller, color)
        self.max_runs = 1
        self.runs = 0
    
    def run_animation(self):
        self.is_running = True
        while True:
            if self.runs < self.max_runs:
                self.single_color()
                self.runs += 1
            time.sleep(0.1)
            if not self.check_if_is_running():
                break

    def single_color(self):
        self.controller.pixels.fill(self.color)
        self.controller.pixels.show()
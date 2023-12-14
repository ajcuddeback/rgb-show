#!/usr/bin/env python3
# Static Xmas Color Animation
# Author: Austin Cuddeback (ajcuddeback@gmail.com)
#
# Colors all lights in a pattern of colors

import time
from .MultiColorAbstractAnimation import MultiColorAbstractAnimation

class multicolors(MultiColorAbstractAnimation):
    def __init__(self, neo_pixel_controller, colors, speed):
        super().__init__(neo_pixel_controller, colors, speed)
        self.max_runs = 1
        self.runs = 0
    
    def run_animation(self):
        self.is_running = True
        while True:
            if self.runs < self.max_runs:
                self.static_xmas_colors()
                self.runs += 1
            time.sleep(0.1)
            if not self.check_if_is_running():
                break
            
    def static_xmas_colors(self):
        for i in range(self.controller.pixels.n):
                index = i % len(self.colors)
                self.controller.pixels[i] = self.colors[index]
        self.controller.pixels.show()
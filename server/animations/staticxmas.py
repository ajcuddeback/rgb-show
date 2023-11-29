#!/usr/bin/env python3
# Static Xmas Color Animation
# Author: Austin Cuddeback (ajcuddeback@gmail.com)
#
# Colors all lights in a pattern of colors
# Mocks the looks of traditional colorful Xmas light strip

import time
from animations import AbstractAnimation

class staticxmas(AbstractAnimation):
    def __init__(self, neo_pixel_controller, color):
        super().__init__(neo_pixel_controller, color)
        print(f"staticxmas __init__: neo_pixel_controller={neo_pixel_controller}, color={color}")
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

    def check_if_is_running(self):
        return self.is_running
    
    def stop(self):
        self.is_running = False

    def static_xmas_colors(self):
        colors = [(255,0,0), (0,255,0), (245,0,245), (255, 255, 0)]
        for i in range(self.controller.pixels.n):
                index = i % len(colors)
                self.controller.pixels[i] = colors[index]
        self.controller.pixels.show()
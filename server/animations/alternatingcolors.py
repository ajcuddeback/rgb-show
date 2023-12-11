#!/usr/bin/env python3
# Simple Climb Animation for a Christmas Tree
# Author: Austin Cuddeback (ajcuddeback@gmail.com)
#
# This animations highlights a set of lights based on the Axis variable
# Currently hard coded to my tree

import time
import threading
from .AbstractAnimation import  AbstractAnimation

class alternatingcolors(AbstractAnimation):
    def __init__(self, neo_pixel_controller, color):
        super().__init__(neo_pixel_controller, color)
        self.axis = [[0, 29], [30, 49], [50, 64], [65, 74], [75, 84], [85, 94], [95, 99]]
        self.colors = [(255,0,0), (0,255,0)]
        self.speed = 0.3
        self.lock = threading.Lock()
    
    def run_animation(self):
        with self.lock:
            self.is_running = True
        while True:
            self.alternate()
            with self.lock:
                if not self.check_if_is_running():
                    return
            time.sleep(self.speed)

    def alternate(self):
        for i in range(len(self.colors)):
            if not self.check_if_is_running():
                    return
            for j in range(self.controller.pixels.n):
                color_index = j + i % len(self.colors)
                self.controller.pixels[i] = self.colors[color_index]
                if not self.check_if_is_running():
                    return
            self.controller.pixels.show()
            time.sleep(self.speed)
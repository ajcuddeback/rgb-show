#!/usr/bin/env python3
# Simple Climb Animation for a Christmas Tree
# Author: Austin Cuddeback (ajcuddeback@gmail.com)
#
# This animations highlights a set of lights based on the Axis variable
# Currently hard coded to my tree

import time
import threading
from .MultiColorAbstractAnimation import  MultiColorAbstractAnimation

class climbanimation(MultiColorAbstractAnimation):
    def __init__(self, neo_pixel_controller, colors, speed):
        super().__init__(neo_pixel_controller, colors, speed)
        self.axis = [[0, 29], [30, 49], [50, 64], [65, 74], [75, 84], [85, 94], [95, 99]]
        self.lock = threading.Lock()
    
    def run_animation(self):
        with self.lock:
            self.is_running = True
        while True:
            self.fillup()
            with self.lock:
                if not self.check_if_is_running():
                    return

    def climb(self, color):
        for i in range(len(self.axis)):
            for j in range(self.axis[i][0], self.axis[i][1]):
                self.controller.pixels[j] = color
                with self.lock:
                    if not self.check_if_is_running():
                        return
            if not self.check_if_is_running():
                return
            self.controller.pixels.show()
            time.sleep(self.speed)

    def fillup(self):
        for color in self.colors:
            self.climb(color)
            with self.lock:
                if not self.check_if_is_running():
                    return
        time.sleep(self.speed)
#!/usr/bin/env python3
# Alternating Color Animation
# Author: Austin Cuddeback (ajcuddeback@gmail.com)
#
# This animation will alternate through the array of colors for each LED

import time
import threading
from .MultiColorAbstractAnimation import  MultiColorAbstractAnimation

class alternatingcolors(MultiColorAbstractAnimation):
    def __init__(self, neo_pixel_controller, colors, speed):
        super().__init__(neo_pixel_controller, colors, speed)
        self.lock = threading.Lock()
    
    def run_animation(self):
        with self.lock:
            self.is_running = True
        while True:
            self.alternate()
            with self.lock:
                if not self.check_if_is_running():
                    return

    def alternate(self):
        offset = 0
        for _ in range(len(self.colors)):
            if not self.check_if_is_running():
                    return
            if(offset > len(self.colors) - 1):
                offset = 0
            for j in range(self.controller.pixels.n):
                color_index = (j + offset) % len(self.colors)

                self.controller.pixels[j] = self.colors[color_index]
                if not self.check_if_is_running():
                    return
            self.controller.pixels.show()
            offset += 1
            time.sleep(self.speed)
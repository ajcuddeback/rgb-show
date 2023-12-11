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
        offset = 0
        for i in range(len(self.colors)):
            if not self.check_if_is_running():
                    return
            print(f'length {len(self.colors) - 1}')
            if(offset > len(self.colors) - 1):
                print('reseting')
                offset = 0
            for j in range(self.controller.pixels.n):
                print(f'offset: {offset} len: {len(self.colors)} j: {j}')
                color_index = (j + offset) % len(self.colors)
                print(f'Addition working??: {j + offset}')
                print(f'RESULT? : {j % len(self.colors)}')
                print(f'color_index {color_index}')
                self.controller.pixels[i] = self.colors[color_index]
                if not self.check_if_is_running():
                    return
            self.controller.pixels.show()
            offset += 1
            print(f'offset now: {offset}')
            time.sleep(self.speed)
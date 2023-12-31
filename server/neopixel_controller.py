#!/usr/bin/env python3
# NeoPixel Controller
# Author: Austin Cuddeback (ajcuddeback@gmail.com)
#
# Singleton class that connects to NeoPixel Compatible lights
# Uses the Adafruit NeoPixel Library

import neopixel

class NeoPixelController:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(NeoPixelController, cls).__new__(cls)
            cls._instance.__initialized = False
        return cls._instance
    
    def __init__(self, num_pixels, pin, brightness=0.1):
        if not self.__initialized:
            self.num_pixels = num_pixels
            self.pin = pin
            self.brightness = brightness
            self.pixels = neopixel.NeoPixel(self.pin, self.num_pixels, brightness=self.brightness, auto_write=False, pixel_order=neopixel.RGB)
            self.__initialized = True

    def turn_off_all_lights(self):
        self.pixels.fill((0,0,0))
        self.pixels.show()

    def change_brightness(self, brightness):
        self.brightness = brightness
        self.pixels.brightness = self.brightness
        self.pixels.show()
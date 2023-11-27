import time
from adafruit_led_animation.animation.rainbow import Rainbow

class rainbowanimation:
    def __init__(self, neo_pixel_controller):
        self.controller = neo_pixel_controller
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
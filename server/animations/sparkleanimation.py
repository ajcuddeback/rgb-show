import time
from adafruit_led_animation.animation.sparkle import Sparkle

class sparkleanimation:
    def __init__(self, neo_pixel_controller):
        self.controller = neo_pixel_controller
        self.is_running = False
    
    def run_animation(self):
        self.is_running = True
        sparkle = Sparkle(self.controller.pixels, speed=.5, period=(255,255,255), num_sparkles=10)
        while True:
            sparkle.animate()
            if not self.check_if_is_running():
                break

    def check_if_is_running(self):
        return self.is_running
    
    def stop(self):
        self.is_running = False
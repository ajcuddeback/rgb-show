import time
from adafruit_led_animation.animation.sparkle import Sparkle
from adafruit_led_animation.animation.sparklepulse import SparklePulse
from adafruit_led_animation.sequence import AnimationSequence

class sparkleanimation:
    def __init__(self, neo_pixel_controller):
        self.controller = neo_pixel_controller
        self.is_running = False
    
    def run_animation(self):
        self.is_running = True
        sparkle = Sparkle(self.controller.pixels, speed=0.05, color=(255,255,255), num_sparkles=10)
        sparkle_pulse = SparklePulse(self.controller.pixels, speed=0.05, period=3, color=(255,255,255))

        animations = AnimationSequence(
            sparkle,
            sparkle_pulse,
            advance_interval=5,
            auto_clear=True,
        )

        while True:
            animations.animate()
            if not self.check_if_is_running():
                break

    def check_if_is_running(self):
        return self.is_running
    
    def stop(self):
        self.is_running = False
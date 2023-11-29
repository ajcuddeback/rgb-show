from adafruit_led_animation.animation.sparklepulse import SparklePulse
from adafruit_led_animation.sequence import AnimationSequence
from AbstractAnimation import AbstractAnimation

class sparkleanimation(AbstractAnimation):
    def run_animation(self):
        self.is_running = True
        sparkle_pulse = SparklePulse(self.controller.pixels, speed=0.1, period=3, color=self.color)

        animations = AnimationSequence(
            sparkle_pulse,
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
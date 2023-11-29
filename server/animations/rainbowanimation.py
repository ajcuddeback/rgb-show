from adafruit_led_animation.animation.rainbow import Rainbow
from AbstractAnimation import AbstractAnimation

class rainbowanimation(AbstractAnimation):
    def run_animation(self):
        self.is_running = True
        rainbow = Rainbow(self.controller.pixels, speed=0.1, period=2)
        while True:
            rainbow.animate()
            if not self.check_if_is_running():
                break
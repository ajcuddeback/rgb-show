import time
from animations import AbstractAnimation

class singlecolor(AbstractAnimation):
    def __init__(self, neo_pixel_controller, color):
        super().__init__(neo_pixel_controller, color)
        self.max_runs = 1
        self.runs = 0
    
    def run_animation(self):
        self.is_running = True
        while True:
            if self.runs < self.max_runs:
                self.single_color()
                self.runs += 1
            time.sleep(0.1)
            if not self.check_if_is_running():
                break

    def check_if_is_running(self):
        return self.is_running
    
    def stop(self):
        self.is_running = False

    def single_color(self):
        print(f"FILLING {self.color}")
        self.controller.pixels.fill(self.color)
        self.controller.pixels.show()
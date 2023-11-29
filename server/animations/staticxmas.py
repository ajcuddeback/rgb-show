import time
from animations import AbstractAnimation

class staticxmas(AbstractAnimation):
    def __init__(self, neo_pixel_controller, color):
        super().__init__(neo_pixel_controller, color)
        self.max_runs = 1
        self.runs = 0
    
    def run_animation(self):
        self.is_running = True
        while True:
            if self.runs < self.max_runs:
                self.static_xmas_colors()
                self.runs += 1
            time.sleep(0.1)
            if not self.check_if_is_running():
                break

    def static_xmas_colors(self):
        colors = [(255,0,0), (0,255,0), (245,0,245), (255, 255, 0)]
        for i in range(self.controller.pixels.n):
                index = i % len(colors)
                self.controller.pixels[i] = colors[index]
        self.controller.pixels.show()
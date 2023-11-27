import time

class staticxmas:
    def __init__(self, neo_pixel_controller):
        self.controller = neo_pixel_controller
        self.axis = [[0, 29], [30, 49], [50, 64], [65, 74], [75, 84], [85, 94], [95, 99]]
        self.colors = [(255,20,217), (0,255,0), (255,0,0)]
        self.is_running = False
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

    def check_if_is_running(self):
        return self.is_running
    
    def stop(self):
        self.is_running = False

    def static_xmas_colors(self):
        colors = [(255,0,0), (0,255,0), (245,0,245), (255, 255, 0)]
        for i in range(self.controller.pixels.n):
                index = i % len(colors)
                self.controller.pixels[i] = colors[index]
        self.controller.pixels.show()
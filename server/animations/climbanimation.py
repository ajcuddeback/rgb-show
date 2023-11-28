import time

class climbanimation:
    def __init__(self, neo_pixel_controller, color):
        self.controller = neo_pixel_controller
        self.axis = [[0, 29], [30, 49], [50, 64], [65, 74], [75, 84], [85, 94], [95, 99]]
        self.colors = [(255,20,217), (0,255,0), (255,0,0)]
        self.is_running = False
        self.color = color
    
    def run_animation(self):
        self.is_running = True
        while True:
            self.fillup()
            print(f"runnimng {self.is_running}")
            if not self.check_if_is_running():
                return

    def check_if_is_running(self):
        return self.is_running
    
    def stop(self):
        self.is_running = False

    def climb(self, color):
        for i in range(len(self.axis)):
            for j in range(self.axis[i][0], self.axis[i][1]):
                self.controller.pixels[j] = color
                if not self.check_if_is_running():
                    return
            if not self.check_if_is_running():
                return
            self.controller.pixels.show()
            time.sleep(0.3)
            
            

    def fillup(self):
        for color in self.colors:
            self.climb(color)
            if not self.check_if_is_running():
                    return
        time.sleep(0.3)
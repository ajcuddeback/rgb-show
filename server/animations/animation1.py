import time

class animation1:
    def __init__(self, neo_pixel_controller):
        self.controller = neo_pixel_controller
        self.axis = [[0, 29], [30, 49], [50, 64], [65, 74], [75, 84], [85, 94], [95, 99]]
        self.colors = [(255,20,217), (0,255,0), (255,0,0)]
        self.is_running = False
    
    def run_animation(self):
        print("RUNNIGN THE ANIMATION BEGIN")
        self.is_running = True
        while True:
            self.fillup()
            if not self.check_if_is_running():
                print("RUNNING IS NO LONGER, BREAKING FROM LOOP")
                break

    def check_if_is_running(self):
        print("CHECKING....")
        return self.is_running
    
    def stop(self):
        print("ABOUT TO STOP THE ANIMATION IN CLASS")
        self.is_running = False

    def climb(self, color):
        for i in range(len(self.axis)):
            for j in range(self.axis[i][0], self.axis[i][1]):
                self.contoller.pixels[j] = color
            self.controller.pixels.show()
            time.sleep(0.3)

    def fillup(self):
        print("Fillin")
        for color in self.colors:
            self.climb(color)
        time.sleep(0.3)
import time
import threading

from abc import ABC, abstractmethod

class AbstractAnimation(ABC):
    def __init__(self, neo_pixel_controller, color):
        self.controller = neo_pixel_controller
        self.color = color
        self.is_running = False

    @abstractmethod
    def run_animation(self):
        """
        Method to start and run the animation.
        Should contain a `while True` loop with the animation implementation in it.
        The while True loop needs to contain a if check_if_is_running conditional that should return from the loop
        """
        pass

    @abstractmethod
    def check_if_is_running(self):
        """
        Method to check if the animation is still running.
        """
        pass

    @abstractmethod
    def stop(self):
        """
        Method to stop the animation.
        """
        pass

class climbanimation(AbstractAnimation):
    def __init__(self, neo_pixel_controller, color):
        super().__init__(neo_pixel_controller, color)
        self.axis = [[0, 29], [30, 49], [50, 64], [65, 74], [75, 84], [85, 94], [95, 99]]
        self.colors = [(255,20,217), (0,255,0), (255,0,0)]
        self.lock = threading.Lock()
    
    def run_animation(self):
        with self.lock:
            self.is_running = True
        while True:
            self.fillup()
            print(f"runnimng {self.is_running}")
            with self.lock:
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
                with self.lock:
                    if not self.check_if_is_running():
                        return
            if not self.check_if_is_running():
                return
            self.controller.pixels.show()
            time.sleep(0.3)
            
            

    def fillup(self):
        for color in self.colors:
            self.climb(color)
            with self.lock:
                if not self.check_if_is_running():
                    return
        time.sleep(0.3)
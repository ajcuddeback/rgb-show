from abc import ABC, abstractmethod

class SingleColorAbstractAnimation(ABC):
    def __init__(self, neo_pixel_controller, color, speed):
        self.controller = neo_pixel_controller
        self.color = color
        self.speed = speed
        self.is_running = False

    @abstractmethod
    def run_animation(self):
        """
        Method to start and run the animation.
        Should contain a `while True` loop with the animation implementation in it.
        The while True loop needs to contain an if check_if_is_running conditional that should return from the loop.
        """
        pass

    def check_if_is_running(self):
        """
        Method to check if the animation is still running.
        """
        return self.is_running

    def stop(self):
        """
        Method to stop the animation.
        """
        self.is_running = False

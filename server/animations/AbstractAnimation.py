from abc import ABC, abstractmethod

class AbstractAnimation(ABC):
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
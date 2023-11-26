import threading
from animations import shutdown  # Assuming you have a shutdown function in animations module

class RaspberryThread(threading.Thread):
    def __init__(self, function):
        self.paused = True
        self.should_abort = False  # Flag to indicate whether to abort the current function
        self.state = threading.Condition()
        self.function = function
        super(RaspberryThread, self).__init__()

    def start(self):
        self.paused = False
        super(RaspberryThread, self).start()

    def run(self):
        # self.resume() # unpause self
        while True:
            with self.state:
                if self.paused:
                    self.state.wait()  # block until notified
                    self.shut_off_lights()
                    if self.should_abort:
                        break
                        shut_off_lights()
            while not self.paused:
                self.should_abort = False  # Reset the abort flag
                # Call function
                self.function()
              
    def resume(self):
        with self.state:
            self.paused = False
            self.state.notify()

    def pause(self):
        with self.state:
            self.paused = True
            self.should_abort = True  # Set the abort flag

    def shut_off_lights(self):
        # Add your code to shut off the lights (using the shutdown function or any other method)
        shutdown()
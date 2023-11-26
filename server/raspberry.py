import threading
from animations import shutdown  # Assuming you have a shutdown function in animations module

class RaspberryThread(threading.Thread):
    def __init__(self, function):
        self.paused = True
        self.state = threading.Condition()
        self.function = function
        super(RaspberryThread, self).__init__()

    def start(self):
        self.paused = False
        super(RaspberryThread, self).start()

    def run(self):
        while True:
            with self.state:
                if self.paused:
                    self.state.wait()

            if self.paused:
                continue

            # If not paused, continue with the regular execution
            self.function()

            with self.state:
                if self.paused:
                    self.shut_off_lights()

    def resume(self):
        with self.state:
            self.paused = False
            self.state.notify()

    def pause(self):
        with self.state:
            self.paused = True

    def shut_off_lights(self):
        shutdown()
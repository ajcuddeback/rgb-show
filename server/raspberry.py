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
        print("Starting...")
        super(RaspberryThread, self).start()

    def run(self):
        while True:
            with self.state:
                if self.paused:
                    print("Thread paused. Waiting...")
                    self.state.wait()

            if self.paused:
                print("Thread paused. Shutting off lights...")
                self.shut_off_lights()
                continue

            # If not paused, continue with the regular execution
            print("Calling function...")
            self.function()

    def resume(self):
        with self.state:
            print("Resuming...")
            self.paused = False
            self.state.notify()

    def pause(self):
        with self.state:
            print("Pausing...")
            self.paused = True

    def shut_off_lights(self):
        # Add your code to shut off the lights (using the shutdown function or any other method)
        print("Shutting off lights...")
        shutdown()
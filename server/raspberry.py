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
        while True:
            with self.state:
                if self.paused:
                    print("Thread paused. Waiting...")
                    self.state.wait()  # block until notified

            if self.should_abort:
                print("Aborting due to pause. Shutting off lights...")
                self.shut_off_lights()
                break

            while not self.paused:
                self.should_abort = False  # Reset the abort flag
                # Call function
                print("Calling function...")
                self.function()

    def resume(self):
        with self.state:
            self.paused = False
            self.state.notify()

    def pause(self):
        with self.state:
            print("Pausing...")
            self.paused = True
            self.should_abort = True  # Set the abort flag

    def shut_off_lights(self):
        # Add your code to shut off the lights (using the shutdown function or any other method)
        print("Shutting off lights...")
        shutdown()
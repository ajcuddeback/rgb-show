import threading
from animations import shutdown  # Assuming you have a shutdown function in animations module
import time

class RaspberryThread(threading.Thread):
    def __init__(self, function, loop=True, max_runs=1):
        self.paused = False
        self.function_running = False  # Flag to indicate whether the function is currently running
        self.state = threading.Condition()
        self.function = function
        self.max_runs = max_runs  # Maximum number of times to run the function
        self.loop = loop
        self.run_count = 0
        super(RaspberryThread, self).__init__()

    def start(self):
        self.paused = False
        print("Starting...")
        super(RaspberryThread, self).start()

    def run(self):
        while True:
            with self.state:
                
                if self.paused:
                    print("Thread paused. Shutting off lights...")
                    self.state.wait()

                if self.loop and not self.paused:
                    print("LOOPING")
                    print(self.paused)
                    self.function()
                    time.sleep(0.1)

                if not self.loop:
                    if self.paused or self.run_count == self.max_runs:
                        continue
                    self.function()
                    self.run_count += 1

                if self.paused:
                    self.shut_off_lights()


    def resume(self):
        with self.state:
            print("Resuming...")
            self.paused = False
            self.run_count = 0
            self.state.notify()

    def pause(self):
        with self.state:
            print("Pausing...")
            self.paused = True
            self.shut_off_lights()
            self.state.notify()

    def shut_off_lights(self):
        # Add your code to shut off the lights (using the shutdown function or any other method)
        print("Shutting off lights...")
        shutdown()
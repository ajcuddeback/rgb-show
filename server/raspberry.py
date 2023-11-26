import threading
from animations import shutdown  # Assuming you have a shutdown function in animations module

class RaspberryThread(threading.Thread):
    def __init__(self, function, max_runs=None):
        self.paused = True
        self.function_running = False  # Flag to indicate whether the function is currently running
        self.state = threading.Condition()
        self.function = function
        self.run_count = 0
        self.max_runs = max_runs  # Maximum number of times to run the function
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

            if self.max_runs is not None and self.run_count >= self.max_runs:
                print(f"Maximum run count ({self.max_runs}) reached. Shutting off lights...")

            # Set the flag to indicate that the function is currently running
            self.function_running = True

            # If not paused, continue with the regular execution
            print("Calling function...")
            self.function()

            # Increment the run count
            self.run_count += 1

            # Reset the flag after the function has completed
            self.function_running = False

            # After the function completes, check if the thread is paused and shut off lights
            with self.state:
                if self.paused:
                    print("Thread paused. Shutting off lights...")
                    self.shut_off_lights()

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
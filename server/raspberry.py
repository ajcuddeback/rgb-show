import threading
from animations import shutdown  # Assuming you have a shutdown function in animations module

class RaspberryThread(threading.Thread):
    def __init__(self, function, loop=True, max_runs=1):
        self.paused = True
        self.function_running = False  # Flag to indicate whether the function is currently running
        self.state = threading.Condition()
        self.function = function
        self.max_runs = max_runs  # Maximum number of times to run the function
        self.loop = loop
        super(RaspberryThread, self).__init__()

    def start(self):
        self.paused = False
        print("Starting...")
        super(RaspberryThread, self).start()

    def run(self):
        if self.loop:
            while True:
                with self.state:
                    if self.paused:
                        print("Thread paused. Waiting...")
                        self.state.wait()
                        continue
                print("Running")
                self.function()

        if not self.loop:
            for _ in range(self.max_runs):
                self.function()

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
            if not self.loop:
                self.state.wait()
                self.shut_off_lights()

    def shut_off_lights(self):
        # Add your code to shut off the lights (using the shutdown function or any other method)
        print("Shutting off lights...")
        shutdown()
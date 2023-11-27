from flask import Flask, jsonify, send_from_directory
import threading
import board
from neopixel_controller import NeoPixelController
from animations.animation1 import animation1

app = Flask(__name__)

# Your Neo Pixel controller class (import and instantiate as needed)
pixel_controller = NeoPixelController(num_pixels=100, pin=board.D18)

current_animation = None
animation_thread = None

def run_animation_thread(animation_module):
    animation_module.run_animation(pixel_controller)

@app.route('/<path:path>', methods=['GET'])
def static_proxy(path):
  return send_from_directory('../templates', path)

@app.route('/')
def root():
  return send_from_directory('../templates', 'index.html')

@app.route('/start_animation/<animation_name>')
def start_animation(animation_name):
    global animation_thread
    global current_animation

    # Stop the current animation if it's running
    stop_animation()

    # Import and run the selected animation in a new thread
     # Import the animation class dynamically
    animation_class = getattr(__import__(f'animations.{animation_name}', fromlist=['']), animation_name)
    
    # Instantiate the animation class with the NeoPixelController
    animation_instance = animation_class(pixel_controller)

    current_animation = animation_instance

    # Start the animation in a new thread
    animation_thread = threading.Thread(target=run_animation_thread, args=(animation_instance))
    animation_thread.start()

    return jsonify({'status': f'{animation_name} started'})

@app.route('/stop_animation')
def stop_animation():
    global current_animation, animation_thread

    print("working on stopping...")

    # Stop the current animation if it's running
    if current_animation:
        current_animation.stop()
        current_animation = None

    print("Going to wait for thread to die")
    # Wait for the animation thread to finish
    if animation_thread and animation_thread.is_alive():
        animation_thread.join()

    print("Turning off the lights now...")
    pixel_controller.turn_off_all_lights()

    return jsonify({'status': 'Animation stopped'})

if __name__ == '__main__':
  # Run server
  app.run(
    debug=True,
    host='0.0.0.0',
    port=5000,
    threaded=True)
from flask import Flask, jsonify, send_from_directory, request
from importlib import import_module
import threading
import board
from neopixel_controller import NeoPixelController

app = Flask(__name__)

# Change these variables according to your configuration
PIN_NUMBER = board.D18
NUM_PIXELS = 100

pixel_controller = NeoPixelController(num_pixels=NUM_PIXELS, pin=PIN_NUMBER)

animation_instance = None
animation_thread = None

def run_animation_thread(animation_module):
    animation_module.run_animation()

@app.route('/<path:path>', methods=['GET'])
def static_proxy(path):
  return send_from_directory('../templates', path)

@app.route('/')
def root():
  return send_from_directory('../templates', 'index.html')

@app.route('/start_animation/<animation_name>', methods=['POST'])
def start_animation(animation_name):
    global animation_thread
    global animation_instance
    global color

    # Stop the current animation if it's running
    print("stoppping...")
    stop_animation()
    print("STOPED")

    if request.is_json:
        json_data = request.get_json()

        # Check if 'color' is in json_data
        if 'color' in json_data:
            # Check if json_data['color'] is a list
            if isinstance(json_data['color'], list):
                color = tuple(json_data['color'])
                print(color)
            else:
                return jsonify({'error': 'JSON data "color" must be an array'}), 400
        else:
            return jsonify({'error': 'COLOR is required!'}), 400
    else:
        return jsonify({'error': 'Invalid JSON data'}), 400
    
    # Import the animation class dynamically
    # Specify the full module path
    module_path = f'animations.{animation_name}'

    # Import the module dynamically
    animation_module = import_module(module_path)

    # Get the animation class dynamically
    animation_class = getattr(animation_module, animation_name)
    
    print("GONNA GEAT CLASS")

    # Instantiate the animation class with the NeoPixelController
    animation_instance = animation_class(pixel_controller, color)

    print("CREATED")

    # Start the animation in a new thread
    animation_thread = threading.Thread(target=run_animation_thread, args=(animation_instance,))
    animation_thread.start()

    return jsonify({'status': f'{animation_name} started'})


@app.route('/change_brightness', methods=['POST'])
def change_brightness():
    if request.is_json:
        json_data = request.get_json()
        
        if 'brightness' in json_data:
            print(json_data['brightness'])
            pixel_controller.change_brightness(json_data['brightness'])
        else:
            return jsonify({'error': 'BRIGHTNESS is required!'}), 400
    else:
        return jsonify({'error': 'Invalid JSON data'}), 400
    
    return jsonify({'statue': 'Brightness changed!'})
    
@app.route('/stop_animation', methods=['POST'])
def stop_animation():
    global animation_instance, animation_thread

    # Stop the current animation if it's running
    if animation_instance:
        animation_instance.stop()
        animation_instance = None

    print("Going to wait for thread to die")
    # Wait for the animation thread to finish
    if animation_thread and animation_thread.is_alive():
        animation_thread.join()

    print(f"thread died {animation_thread}")
    pixel_controller.turn_off_all_lights()

    return jsonify({'status': 'Animation stopped'})

if __name__ == '__main__':
  # Run server
  app.run(
    debug=True,
    host='0.0.0.0',
    port=5000,
    threaded=False)
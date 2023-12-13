#!/usr/bin/env python3
# Flask Server Entry Point
# Author: Austin Cuddeback (ajcuddeback@gmail.com)
#
# Simple Flask Server to connect and run animations through a web application

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
current_animation_name = ''
current_animation_module_path = ''
current_params = {}
current_color = (0,0,0)
current_colors = []

def run_animation_thread(animation_module):
    animation_module.run_animation()

@app.route('/<path:path>', methods=['GET'])
def static_proxy(path):
  return send_from_directory('../templates', path)

@app.route('/')
def root():
  return send_from_directory('../templates', 'index.html')

@app.route('/start_multi_color/<animation_name>', methods=['POST'])
def start_multi_color(animation_name):
    global animation_thread, animation_instance, current_animation_name, current_colors, params

    # Stop the current animation if it's running\
    stop_animation()

    if request.is_json:
        json_data = request.get_json()
        colors = []
        speed = 0
        # Check if 'color' is in json_data
        if 'colors' in json_data:
            # Check if json_data['color'] is a list
            if isinstance(json_data['colors'], list):
            # Convert each inner array to a tuple
                colors = [tuple(color) for color in json_data['colors']]
            else:
                return jsonify({'error': 'JSON data "colors" must be an array'}), 400
            
             # Check if 'speed' is in json_data
            if 'speed' in json_data:
                speed = json_data['speed']
            else:
                return jsonify({'error': 'speed is required!'}), 400
        else:
            return jsonify({'error': 'COLORS are required!'}), 400
    else:
        return jsonify({'error': 'Invalid JSON data'}), 400
    
    # Import the animation class dynamically
    # Specify the full module path
    module_path = f'animations.multi_color_animations.{animation_name}'

    params = { 
        "colors": colors,
        "speed": speed
    }

    import_and_start_animation(module_path, animation_name, params)

    current_colors = colors

    return jsonify({'status': f'{animation_name} started'}), 200

@app.route('/start_single_color_animation/<animation_name>', methods=['POST'])
def start_single_color_animation(animation_name):
    global animation_thread, animation_instance, current_animation_name, color, current_color, params

    # Stop the current animation if it's running\
    stop_animation()
    speed = 0
    if request.is_json:
        json_data = request.get_json()

        # Check if 'color' is in json_data
        if 'color' in json_data:
            # Check if json_data['color'] is a list
            if isinstance(json_data['color'], list):
                color = tuple(json_data['color'])
            else:
                return jsonify({'error': 'JSON data "color" must be an array'}), 400
            
             # Check if 'speed' is in json_data
            if 'speed' in json_data:
                speed = json_data['speed']
            else:
                return jsonify({'error': 'speed is required!'}), 400
        else:
            return jsonify({'error': 'COLOR is required!'}), 400
    else:
        return jsonify({'error': 'Invalid JSON data'}), 400
    
    # Import the animation class dynamically
    # Specify the full module path
    module_path = f'animations.single_color_animations.{animation_name}'

    params = {
        "color": color,
        "speed": speed
    }
    
    import_and_start_animation(module_path, animation_name, params)
   
    current_color = color

    return jsonify({'status': f'{animation_name} started'}), 200

@app.route('/start_static_animation/<animation_name>', methods=['POST'])
def start_static_animation(animation_name):
    global animation_thread, animation_instance, current_animation_name, color, current_color, params

    # Stop the current animation if it's running\
    stop_animation()

    speed = 0

    if request.is_json:
        json_data = request.get_json()

        # Check if 'speed' is in json_data
        if 'speed' in json_data:
            speed = json_data['speed']
        else:
            return jsonify({'error': 'speed is required!'}), 400
    else:
        return jsonify({'error': 'Invalid JSON data'}), 400
    
    # Import the animation class dynamically
    # Specify the full module path
    module_path = f'animations.static_animations.{animation_name}'

    params = {
        "speed": speed,
    }
    
    import_and_start_animation(module_path, animation_name, params)

    return jsonify({'status': f'{animation_name} started'}), 200


@app.route('/change_brightness', methods=['POST'])
def change_brightness():
    if request.is_json:
        json_data = request.get_json()
        
        if 'brightness' in json_data:
            pixel_controller.change_brightness(json_data['brightness'])
        else:
            return jsonify({'error': 'BRIGHTNESS is required!'}), 400
    else:
        return jsonify({'error': 'Invalid JSON data'}), 400
    
    return jsonify({'status': 'Brightness changed!'}), 200

@app.route('/get_active_state')
def get_brightness():
  global current_color
  return jsonify({ 'brightness': f'{pixel_controller.brightness}', 'animation': current_animation_name, 'color': current_color, 'colors': current_colors  }), 200
    
@app.route('/stop_animation', methods=['POST'])
def stop_animation():
    global animation_instance, animation_thread, current_animation_name

    # Stop the current animation if it's running
    if animation_instance:
        animation_instance.stop()
        animation_instance = None

    # Wait for the animation thread to finish
    if animation_thread and animation_thread.is_alive():
        animation_thread.join()

    pixel_controller.turn_off_all_lights()

    return jsonify({'status': 'Animation stopped'}), 200

@app.route('/resume_animation', methods=['POST'])
def resume_animation():
    global current_animation_module_path, current_animation_name, params
    if(current_animation_name & current_animation_module_path):
        import_and_start_animation(current_animation_module_path, current_animation_name, params)
        return jsonify({'status': 'Animation resumed'}), 200
    else: 
        return jsonify({'status': 'No animation exists'}), 500

def import_and_start_animation(module_path, animation_name, params):
    global animation_thread, current_animation_name, current_animation_module_path
     # Import the module dynamically
    animation_module = import_module(module_path)
    
    # Get the animation class dynamically
    animation_class = getattr(animation_module, animation_name)

    # Instantiate the animation class with the NeoPixelController
    animation_instance = animation_class(pixel_controller, **params)

    # Start the animation in a new thread
    animation_thread = threading.Thread(target=run_animation_thread, args=(animation_instance,))
    animation_thread.start()
    current_animation_name = animation_name
    current_animation_module_path = module_path

if __name__ == '__main__':
  # Run server
  app.run(
    debug=True,
    host='0.0.0.0',
    port=5000,
    threaded=False)
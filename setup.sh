#!/bin/bash
# Install Python packages
sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
sudo python3 -m pip install --force-reinstall adafruit-blinka
sudo pip3 install adafruit-circuitpython-led-animation

# Navigate to the client directory and install npm packages
cd client
sudo npm i

# Build the Angular project
sudo ng build --configuration=production --output-path ../templates

# Navigate to the server directory and run the Python app
cd ../server
sudo python3 app.py

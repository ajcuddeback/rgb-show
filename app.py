from flask import Flask, render_template
from raspberry import RaspberryThread
from light_functions import blink_all, all_pins_off, lightshow, cycle_all
from xmas import russian_xmas
import os

# Load the env variables
if os.path.exists('.env'):
    print('Importing environment from .env...')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]

app = Flask(__name__)

@app.route("/test", methods=["GET"])
def test():
    return "testing"

if __name__ == '__main__':
    # Run server
    app.run(
        debug=True,
        host=os.environ.get("IP_ADDRESS"),
        port=int(os.environ.get("PORT")),
        threaded=True)
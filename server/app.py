from flask import Flask, send_from_directory
from animations import fillup
from raspberry import RaspberryThread
import os

# Load the env variables
if os.path.exists('.env'):
    print('Importing environment from .env...')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]

app = Flask(__name__)

@app.route('/<path:path>', methods=['GET'])
def static_proxy(path):
  return send_from_directory('../templates', path)


@app.route('/')
def root():
  return send_from_directory('../templates', 'index.html')

@app.route("/api/fillup", methods=["GET"])
def fill():
  global threads
  global fillup_thread
  any(thread.pause() for thread in threads)
  if not fillup_thread.isAlive():
    fillup_thread.start()
  fillup_thread.resume()
  return "working"

@app.route("/api/shutdown", methods=["GET"])
def shut():
  global threads
  any(thread.pause() for thread in threads)
  return "Shutting down..."

if __name__ == '__main__':
  # Create threads
  fillup_thread = RaspberryThread(function=fillup)

  # collect threads
  threads = [
      fillup_thread
  ]

  # Run server
  app.run(
    debug=True,
    host='0.0.0.0',
    port=5000,
    threaded=True)
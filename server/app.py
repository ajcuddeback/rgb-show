from flask import Flask, send_from_directory
from animations import fillup, staticXmasColors
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
  any(thread.pause() for thread in threads)
  if not fillup_thread.isAlive():
    fillup_thread.start()
  else:
    fillup_thread.resume()
  print("ABOUT TO RETURN>> Wait. it wont'")
  return "working"

@app.route("/api/xmas", methods=["GET"])
def xmas():
  any(thread.pause() for thread in threads)
  if not staticXmasColors_thread.isAlive():
    staticXmasColors_thread.start()
  else:
    staticXmasColors_thread.resume()
  return "working"

@app.route("/api/shutdown", methods=["GET"])
def shut():
  print("WORKING ON IT shutt")
  any(thread.pause() for thread in threads)
  print("SHUT THEM DOWN")
  return "Shutting down..."

if __name__ == '__main__':
  # Create threads
  fillup_thread = RaspberryThread(function=fillup)
  staticXmasColors_thread = RaspberryThread(function=staticXmasColors, loop=False)

  # collect threads
  threads = [
      fillup_thread,
      staticXmasColors_thread
  ]

  # Run server
  app.run(
    debug=True,
    host='0.0.0.0',
    port=5000,
    threaded=True)
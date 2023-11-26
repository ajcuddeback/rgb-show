from flask import Flask, send_from_directory
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
  return send_from_directory('./templates', path)


@app.route('/')
def root():
  return send_from_directory('./templates', 'index.html')

@app.route("/api/test", methods=["GET"])
def test():
    return "testing"

if __name__ == '__main__':
    # Run server
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        threaded=True)
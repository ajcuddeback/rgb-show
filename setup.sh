#!/usr/bin/env bash
# One-shot setup for a Raspberry Pi.
#
#   ./setup.sh               install python deps + systemd service + nginx + Spotify Connect
#   ./setup.sh --no-nginx    skip nginx (serve straight from gunicorn on :8000)
#   ./setup.sh --no-spotify  skip the raspotify (Spotify Connect) receiver
#
# The Angular UI is pre-built and committed in ./templates, so Node is NOT
# required on the Pi. Rebuild it on your dev machine with `cd client && npm run build`.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WITH_NGINX=1
WITH_SPOTIFY=1
for arg in "$@"; do
  [[ "$arg" == "--no-nginx" ]] && WITH_NGINX=0
  [[ "$arg" == "--no-spotify" ]] && WITH_SPOTIFY=0
done

echo "==> Installing system packages"
sudo apt-get update -qq
# libportaudio2 + alsa-utils: audio output / input for the music effects
PKGS="python3 python3-pip python3-venv python3-dev libportaudio2 alsa-utils curl"
[[ $WITH_NGINX -eq 1 ]] && PKGS="$PKGS nginx"
sudo apt-get install -y -qq $PKGS >/dev/null

echo "==> Installing Python dependencies into server/.venv"
# Raspberry Pi OS (Bookworm+) blocks system-wide pip (PEP 668), so we use a venv.
# --system-site-packages keeps any Adafruit/ws281x libs you already installed
# with apt or an older sudo pip3 visible inside it.
VENV="$REPO_DIR/server/.venv"
[[ -x "$VENV/bin/python" ]] || sudo python3 -m venv --system-site-packages "$VENV"
sudo "$VENV/bin/python" -m pip install -q --upgrade pip
sudo "$VENV/bin/python" -m pip install -q --upgrade -r "$REPO_DIR/server/requirements.txt"
# Raspberry Pi 5 drives NeoPixels through PIO and needs an extra platform library.
if grep -qa "Raspberry Pi 5" /proc/device-tree/model 2>/dev/null; then
  echo "==> Raspberry Pi 5 detected: installing the PIO NeoPixel driver"
  sudo "$VENV/bin/python" -m pip install -q --upgrade Adafruit-Blinka-Raspberry-Pi5-Neopixel
fi

sudo "$VENV/bin/python" -m pip install -q --upgrade -r "$REPO_DIR/server/requirements-ha.txt"

echo "==> Stopping any old gunicorn3 --daemon instance"
sudo pkill -f "gunicorn3 app:app" 2>/dev/null || true

echo "==> Installing systemd service"
sed "s#/home/pi/rgb-show#$REPO_DIR#g" "$REPO_DIR/deploy/rgb-show.service" | sudo tee /etc/systemd/system/rgb-show.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable rgb-show >/dev/null
sudo systemctl restart rgb-show

echo "==> Installing Home Assistant bridge (not enabled)"
sed "s#/home/pi/rgb-show#$REPO_DIR#g" "$REPO_DIR/deploy/rgb-show-ha.service" | sudo tee /etc/systemd/system/rgb-show-ha.service >/dev/null
[[ -f /etc/rgb-show-ha.env ]] || sudo cp "$REPO_DIR/deploy/ha.env.example" /etc/rgb-show-ha.env
sudo systemctl daemon-reload
if systemctl is-enabled --quiet rgb-show-ha 2>/dev/null; then
  sudo systemctl restart rgb-show-ha
fi

if [[ $WITH_SPOTIFY -eq 1 ]]; then
  echo "==> Installing Spotify Connect receiver (raspotify)"
  if ! command -v librespot >/dev/null 2>&1 && ! dpkg -s raspotify >/dev/null 2>&1; then
    # Official installer from https://github.com/dtcooper/raspotify (adds their apt repo and installs the package)
    curl -sL https://dtcooper.github.io/raspotify/install.sh | sudo sh
  fi
  sudo mkdir -p /var/lib/rgb-show
  [[ -p /var/lib/rgb-show/audio.fifo ]] || sudo mkfifo /var/lib/rgb-show/audio.fifo
  sudo chmod 666 /var/lib/rgb-show/audio.fifo
  sudo cp "$REPO_DIR/deploy/raspotify.conf" /etc/raspotify/conf
  sudo systemctl enable raspotify >/dev/null 2>&1 || true
  sudo systemctl restart raspotify || echo "   (raspotify did not start; check: journalctl -u raspotify -n 30)"
fi

if [[ $WITH_NGINX -eq 1 ]]; then
  echo "==> Configuring nginx"
  sudo cp "$REPO_DIR/deploy/nginx-rgb-show.conf" /etc/nginx/sites-available/rgb-show
  sudo ln -sf /etc/nginx/sites-available/rgb-show /etc/nginx/sites-enabled/rgb-show
  # Remove the stock default site and the old hand-made config from the original README
  sudo rm -f /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/flask_app
  sudo nginx -t
  sudo systemctl reload nginx
fi

sleep 2
if curl -fsS http://127.0.0.1:8000/api/state >/dev/null; then
  IP=$(hostname -I | awk '{print $1}')
  echo
  echo "✅ rgb-show is running."
  [[ $WITH_NGINX -eq 1 ]] && echo "   Open: http://$IP/" || echo "   Open: http://$IP:8000/"
  echo "   Logs: journalctl -u rgb-show -f"
  if [[ $WITH_SPOTIFY -eq 1 ]]; then
    echo
    echo "   Spotify: open the Spotify app, tap the device picker, choose 'Christmas Tree'."
    echo "   Then in the web app: Music -> Source -> Spotify. (Needs a USB speaker/DAC or HDMI audio on the Pi.)"
  fi
  if ! systemctl is-enabled --quiet rgb-show-ha 2>/dev/null; then
    echo
    echo "   Home Assistant (optional): edit /etc/rgb-show-ha.env with your MQTT broker, then"
    echo "   sudo systemctl enable --now rgb-show-ha"
  fi
else
  echo "❌ Service did not come up. Check: journalctl -u rgb-show -n 50"
  exit 1
fi

#!/usr/bin/env bash
# One-shot setup for a Raspberry Pi.
#
#   ./setup.sh            install python deps + systemd service + nginx
#   ./setup.sh --no-nginx skip nginx (serve straight from gunicorn on :8000)
#
# The Angular UI is pre-built and committed in ./templates, so Node is NOT
# required on the Pi. Rebuild it on your dev machine with `cd client && npm run build`.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WITH_NGINX=1
[[ "${1:-}" == "--no-nginx" ]] && WITH_NGINX=0

echo "==> Installing system packages"
sudo apt-get update -qq
PKGS="python3 python3-pip"
[[ $WITH_NGINX -eq 1 ]] && PKGS="$PKGS nginx"
sudo apt-get install -y -qq $PKGS >/dev/null

echo "==> Installing Python dependencies"
# --break-system-packages is needed on Bookworm+ to install into the system
# interpreter, which is what the systemd unit (running as root) uses.
sudo python3 -m pip install -q --upgrade --break-system-packages -r "$REPO_DIR/server/requirements.txt" 2>/dev/null \
  || sudo python3 -m pip install -q --upgrade -r "$REPO_DIR/server/requirements.txt"

echo "==> Stopping any old gunicorn3 --daemon instance"
sudo pkill -f "gunicorn3 app:app" 2>/dev/null || true

echo "==> Installing systemd service"
sed "s#/home/pi/rgb-show#$REPO_DIR#g" "$REPO_DIR/deploy/rgb-show.service" | sudo tee /etc/systemd/system/rgb-show.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable rgb-show >/dev/null
sudo systemctl restart rgb-show

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
else
  echo "❌ Service did not come up. Check: journalctl -u rgb-show -n 50"
  exit 1
fi

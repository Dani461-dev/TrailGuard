#!/usr/bin/env bash
# Setup lengkap TrailGuard di VM (Ubuntu/LinuxONE):
#   dependensi -> .env -> make toy (data+model lokal di VM) -> systemd API :8000 -> nginx :80 (SSE-friendly)
# Jalankan sebagai user yang boleh sudo (ubuntu):  bash backend/deploy/vm_setup.sh
set -euo pipefail
cd "$(dirname "$0")/.."    # <- backend/
ROOT="$(pwd)"

echo "==> [1/5] Dependensi sistem"
sudo apt-get update -y
sudo apt-get install -y python3 python3-venv python3-pip nginx tmux curl

PYBIN="$ROOT/.venv/bin/python"
if [ ! -x "$PYBIN" ]; then
  echo "    membuat venv + pip install (hanya wheel; gagal = fallback apt)…"
  python3 -m venv .venv
  .venv/bin/pip install --upgrade pip -q || true
  if ! .venv/bin/pip install --only-binary=:all: -r requirements.txt; then
    echo "    !! pip wheel gagal (kemungkinan s390x) -> paket apt"
    sudo apt-get install -y python3-pandas python3-sklearn python3-flask \
                            python3-yaml python3-joblib python3-pytest
    PYBIN="$(command -v python3)"
    rm -rf .venv
  fi
fi
echo "    python: $PYBIN ($($PYBIN --version))"

echo "==> [2/5] .env (kunci HMAC — tidak pernah di-commit)"
if [ ! -f .env ]; then
  KEY="${TRAILGUARD_HMAC_KEY:-$(openssl rand -hex 32)}"
  printf 'TRAILGUARD_HMAC_KEY=%s\n' "$KEY" > .env
  echo "    .env dibuat dengan kunci acak."
fi
set -a; source .env; set +a

echo "==> [3/5] Pipeline toy (data + model DILATIH di VM — bundle.joblib tidak boleh disalin antar-arsitektur)"
if [ -x "$ROOT/.venv/bin/python" ]; then make toy; else PYTHONPATH=src "$PYBIN" -m trailguard.pipeline all; fi

echo "==> [4/5] systemd: trailguard-api (port 8000)"
sudo tee /etc/systemd/system/trailguard-api.service >/dev/null <<UNIT
[Unit]
Description=TrailGuard Flask API
After=network.target

[Service]
WorkingDirectory=$ROOT
Environment=PYTHONPATH=src
EnvironmentFile=$ROOT/.env
ExecStart=$PYBIN -m trailguard.api.app
Restart=on-failure
User=$(whoami)

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable --now trailguard-api
sleep 2
curl -sf http://127.0.0.1:8000/health && echo " <- API OK"

echo "==> [5/5] nginx :80 -> 127.0.0.1:8000 (streaming/SSE-friendly)"
sudo tee /etc/nginx/sites-available/trailguard >/dev/null <<NGINX
server {
    listen 80 default_server;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header Connection "";

        # Wajib untuk SSE (endpoint /api/replay/stream):
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 1h;
        proxy_send_timeout 1h;
        chunked_transfer_encoding off;
    }
}
NGINX
sudo ln -sf /etc/nginx/sites-available/trailguard /etc/nginx/sites-enabled/trailguard
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

IP="$(hostname -I | awk '{print $1}')"
echo
echo "==> Selesai. Verifikasi dari luar:"
echo "   curl http://$IP/health"
echo "   curl -sN 'http://$IP/api/replay/stream?speedup=0&limit=100000&alerts_only=1' | grep -c 'event: alert'"
echo
echo "==> Update berikutnya (di repo ini):"
echo "   git pull && sudo systemctl restart trailguard-api"

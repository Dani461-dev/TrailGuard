#!/usr/bin/env bash
# Build & jalankan container (otomatis memilih podman atau docker).  Jalankan dari root repo.
set -e
RT=$(command -v podman || command -v docker || { echo "Tidak ada podman/docker. Tanya Grup A / SME IBM."; exit 1; })
echo "Runtime: $RT  | arsitektur: $(uname -m)"
$RT build -t trailguard:latest -f deploy/Dockerfile .
$RT rm -f trailguard 2>/dev/null || true
# data/model/output di-mount dari host -> log mentah & kunci TIDAK ikut di dalam image
$RT run -d --name trailguard -p 8000:8000 \
  -v "$PWD/data:/app/data:Z" -v "$PWD/models:/app/models:Z" -v "$PWD/outputs:/app/outputs:Z" \
  --env-file .env trailguard:latest
sleep 2; curl -s localhost:8000/health && echo " <- container sehat"
$RT ps

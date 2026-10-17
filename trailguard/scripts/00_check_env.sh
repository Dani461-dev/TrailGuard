#!/usr/bin/env bash
# Langkah pertama di LinuxONE: "Hello s390x". Jalankan:  bash scripts/00_check_env.sh
echo "=== SISTEM ==="; uname -a; cat /etc/os-release | head -3
echo; echo "=== CPU / RAM / DISK ==="; lscpu | grep -E "Architecture|Model name|^CPU\(s\)|Byte Order"
free -h | head -2; df -h . | tail -1
echo; echo "=== TOOLS ==="
for t in python3 pip3 git tmux podman docker gcc; do
  if command -v $t >/dev/null; then echo "  ada    $t -> $($t --version 2>&1 | head -1)"; else echo "  TIDAK  $t"; fi
done
echo; echo "=== PAKET PYTHON ==="
PYTHONPATH=src python3 scripts/check_imports.py

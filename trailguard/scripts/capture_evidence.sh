#!/usr/bin/env bash
# Mengumpulkan BUKTI penggunaan LinuxONE (juri meminta screenshot). Jalankan, lalu SCREENSHOT layarnya.
# Teks juga disimpan di evidence/system_info.txt
OUT=evidence/system_info.txt
{
 echo "### $(date -u) UTC"
 echo "### Host / OS";        uname -a; cat /etc/os-release | head -3
 echo "### Arsitektur CPU";   lscpu | grep -E "Architecture|Model name|Byte Order|^CPU\(s\)|Hypervisor|Vendor"
 echo "### Memori / Disk";    free -h; df -h . | tail -1
 echo "### Python & paket ML"; python3 --version; pip list 2>/dev/null | grep -iE "scikit|pandas|numpy|flask|lightgbm|xgboost|shap"
 echo "### Container berjalan"
 (podman ps 2>/dev/null || docker ps 2>/dev/null || echo "(belum ada container runtime / container)")
 echo "### Metrik terakhir"; cat outputs/metrics.json 2>/dev/null
 echo "### Benchmark terakhir"; cat outputs/benchmark.json 2>/dev/null
} | tee "$OUT"
echo; echo ">> Sekarang ambil SCREENSHOT dan simpan di folder evidence/ (lihat docs/04_SUBMISSION_CHECKLIST.md)"

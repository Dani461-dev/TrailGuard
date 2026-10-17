"""Ukur latensi per-event dan throughput (angka ini dipakai di video & README).
Jalankan setelah pipeline:  PYTHONPATH=src python scripts/benchmark_latency.py
"""
import json
import statistics
import time

import argparse

import pandas as pd

from trailguard.config import load_config, path_of
from trailguard.io_utils import read_table
from trailguard.models.score import score_frame
from trailguard.models.train import load_bundle

ap = argparse.ArgumentParser(); ap.add_argument("--config", default=None)
cfg = load_config(ap.parse_args().config)
bundle = load_bundle(path_of(cfg, "model"))
feat = read_table(cfg, "features", ["day"])
w = cfg["model"]["ensemble_weight_supervised"]

# 1) latensi skor satu baris (simulasi satu event masuk)
sample = feat.sample(min(300, len(feat)), random_state=0)
lat = []
for i in range(len(sample)):
    t = time.perf_counter()
    score_frame(bundle, sample.iloc[[i]], w)
    lat.append((time.perf_counter() - t) * 1000)
lat.sort()

# 2) throughput batch, diskalakan (replikasi data) -> uji "scaled-up replay"
big = pd.concat([feat] * 20, ignore_index=True)
t = time.perf_counter()
score_frame(bundle, big, w)
dt = time.perf_counter() - t

res = {"single_row_ms_p50": round(statistics.median(lat), 2),
       "single_row_ms_p95": round(lat[int(len(lat) * 0.95)], 2),
       "batch_rows": len(big), "batch_rows_per_sec": round(len(big) / dt)}
# TODO(Grup A): tambahkan pengukuran ingestion+feature builder, dan CPU/memori saat beban (top/htop).
path = path_of(cfg, "benchmark")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(res, indent=2))
print(json.dumps(res, indent=2))

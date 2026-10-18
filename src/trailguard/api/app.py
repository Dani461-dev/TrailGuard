"""API + dashboard sederhana (Flask, pure-Python agar aman di s390x).
Jalankan:  python -m trailguard.api.app   -> http://localhost:8000
"""
import json
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from ..config import load_config, path_of
from ..models.score import score_frame
from ..models.train import load_bundle
from ..policy.policy import decide, policy_cfg

app = Flask(__name__)
CFG = load_config(os.environ.get("TRAILGUARD_CONFIG"))   # mis. TRAILGUARD_CONFIG=configs/config_lanl.yaml


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/alerts")
def alerts():
    f = path_of(CFG, "alerts")
    if not f.exists():
        return jsonify([])
    rows = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
    limit = int(request.args.get("limit", 50))
    rows.sort(key=lambda a: a["risk"], reverse=True)
    return jsonify(rows[:limit])


@app.get("/api/metrics")
def metrics():
    f = Path(path_of(CFG, "metrics"))
    return jsonify(json.loads(f.read_text()) if f.exists() else {})


@app.post("/api/score")
def score():
    """Body: {"features": {<semua kolom FEATURE_COLS>}}  -> skor + tier. (Dipakai Grup C/benchmark)

    Memakai alpha & cara gabung hasil tuning yang tersimpan di bundle, serta ambang tier hasil
    kalibrasi validasi -- sama persis dengan yang dipakai pipeline saat menulis alerts.jsonl."""
    import pandas as pd
    bundle = load_bundle(path_of(CFG, "model"))
    df = pd.DataFrame([request.get_json()["features"]])
    out = score_frame(bundle, df).iloc[0]
    risk = float(out.risk)
    return jsonify({"risk": risk, **decide(risk, policy_cfg(CFG, bundle))})


@app.get("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

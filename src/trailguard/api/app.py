"""API + dashboard (Flask, pure-Python agar aman di s390x).
Jalankan:  python -m trailguard.api.app   -> http://localhost:8000

Endpoint:
  GET  /health            cek sehat
  GET  /api/config        info dataset & policy (untuk label jujur di dashboard)
  GET  /api/alerts        alert teratas (Kontrak #3)          ?limit=N
  GET  /api/metrics       isi metrics.json (Kontrak #5)
  GET  /api/decisions     keputusan manusia yang sudah tercatat
  POST /api/decision      catat keputusan manusia (approve/reject) -> outputs/decisions.jsonl
  POST /api/score         body {"features": {...}} -> {risk, tier, ...}
  GET  /api/replay        aliran event (Kontrak #1) untuk halaman replay  ?limit=N
  GET  /api/replay/stream SSE: replay() sebagai stream — ?speedup=&limit=&alerts_only=1
"""
import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from flask import (
    Flask,
    Response,
    jsonify,
    render_template,
    request,
    send_from_directory,
    stream_with_context,
)

from ..config import load_config, path_of
from ..ingest.replay import replay
from ..io_utils import read_table
from ..models.score import score_frame
from ..models.train import load_bundle
from ..policy.policy import decide

app = Flask(__name__)
CFG = load_config(os.environ.get("TRAILGUARD_CONFIG"))   # mis. TRAILGUARD_CONFIG=configs/config_lanl.yaml


@app.after_request
def _cors(resp):
    """CORS minimal tanpa dependensi tambahan (dashboard statis beda origin)."""
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


def _read_alerts(limit=None):
    f = path_of(CFG, "alerts")
    if not f.exists():
        return []
    rows = [json.loads(line) for line in f.read_text().splitlines() if line.strip()]
    rows.sort(key=lambda a: a.get("risk", 0), reverse=True)
    return rows if limit is None else rows[:limit]


def _decisions_path() -> Path:
    return path_of(CFG, "alerts").parent / "decisions.jsonl"


def _read_decisions():
    f = _decisions_path()
    if not f.exists():
        return []
    return [json.loads(line) for line in f.read_text().splitlines() if line.strip()]


def _read_metrics():
    f = Path(path_of(CFG, "metrics"))
    return json.loads(f.read_text()) if f.exists() else {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/config")
def config_info():
    pol = CFG.get("policy", {})
    ev = CFG.get("evaluation", {})
    ex = CFG.get("explain", {})
    return jsonify({
        "dataset": CFG.get("dataset", "cert"),
        "explain_method_target": ex.get("method"),
        "policy": {
            "step_up_threshold": pol.get("step_up_threshold"),
            "ticket_threshold": pol.get("ticket_threshold"),
        },
        "alert_budget_per_day": ev.get("alert_budget_per_day"),
        "has_alerts": path_of(CFG, "alerts").exists(),
        "has_metrics": Path(path_of(CFG, "metrics")).exists(),
    })


@app.get("/api/alerts")
def alerts():
    limit = int(request.args.get("limit", 50))
    return jsonify(_read_alerts(limit))


@app.get("/api/metrics")
def metrics():
    return jsonify(_read_metrics())


@app.get("/api/decisions")
def decisions():
    return jsonify(_read_decisions())


@app.post("/api/decision")
def record_decision():
    """Catat keputusan manusia atas satu alert. Append ke outputs/decisions.jsonl."""
    body = request.get_json(silent=True) or {}
    user, day = body.get("user"), body.get("day")
    decision = body.get("decision")
    if not user or not day or decision not in ("approve", "reject"):
        return jsonify({"ok": False, "error": "butuh user, day, dan decision=approve|reject"}), 400
    row = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "user": user,
        "day": day,
        "decision": decision,
        "note": body.get("note", ""),
        "risk": body.get("risk"),
        "tier": body.get("tier"),
    }
    f = _decisions_path()
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, "a") as fh:
        fh.write(json.dumps(row) + "\n")
    return jsonify({"ok": True, "decision": row})


@app.post("/api/score")
def score():
    """Body: {"features": {<semua kolom FEATURE_COLS>}}  -> skor + tier. (Dipakai Grup C/benchmark)"""
    import pandas as pd
    bundle = load_bundle(path_of(CFG, "model"))
    df = pd.DataFrame([request.get_json()["features"]])
    out = score_frame(bundle, df, CFG["model"]["ensemble_weight_supervised"]).iloc[0]
    return jsonify({"risk": float(out.risk), **decide(float(out.risk), CFG)})


@app.get("/api/replay")
def replay_events():
    """Aliran event ter-pseudonim (Kontrak #1) untuk demo replay. Jujur: ini replay, bukan real-time."""
    limit = int(request.args.get("limit", 200))
    f = path_of(CFG, "events")
    if not f.exists():
        return jsonify({"events": [], "available": False})
    events = []

    def _cell(v):
        if _is_nan(v):
            return ""
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v)

    for row in _load_events().head(limit).to_dict("records"):
        events.append({k: _cell(v) for k, v in row.items()})
    return jsonify({"events": events, "available": True})


# ─── Streaming replay (SSE) ────────────────────────────────────────────────
# Cache events (dibaca + diurut sekali per file) agar tiap koneksi stream tidak
# membaca ulang CSV. Di-invalidasi otomatis lewat mtime file.
_EVENTS_CACHE = {"df": None, "path": None, "mtime": None}
MIN_EVENT_INTERVAL = 0.016  # jeda minimal antar event (~60/detik) — cegah banjir


def _is_nan(v):
    try:
        r = v != v
        return bool(r) if not isinstance(r, (list, tuple)) else False
    except Exception:
        return False


def _load_events():
    f = path_of(CFG, "events")
    if not f.exists():
        return None
    mtime = f.stat().st_mtime
    c = _EVENTS_CACHE
    if c["df"] is None or c["path"] != str(f) or c["mtime"] != mtime:
        df = read_table(CFG, "events", ["ts"]).sort_values("ts").reset_index(drop=True)
        c.update(df=df, path=str(f), mtime=mtime)
    return c["df"]


def _sse_json(obj) -> str:
    """JSON aman untuk SSE: numpy -> python, NaN -> null, Timestamp -> string."""
    def clean(o):
        if o is None or isinstance(o, (str, bool, int)):
            return o
        if isinstance(o, float):
            return None if math.isnan(o) or math.isinf(o) else o
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if hasattr(o, "dtype") and hasattr(o, "item"):  # skalar numpy
            try:
                return clean(o.item())
            except Exception:
                return str(o)
        if hasattr(o, "hour") and hasattr(o, "isoformat"):  # datetime/Timestamp
            return o.isoformat(sep=" ")
        return str(o)
    return json.dumps(clean(obj), ensure_ascii=False)


def _alert_index():
    """Index (user, day) -> alert dari outputs/alerts.jsonl (precomputed, Kontrak #3)."""
    return {(a.get("user"), a.get("day")): a for a in _read_alerts(None)}


@app.get("/api/replay/stream")
def replay_stream():
    """SSE: `for event in replay(ev, speedup): send_to_ui(event)` — persis pola demo.

    Query:
      speedup      : 1 detik nyata = N detik log (0 = tanpa jeda; server tetap
                     membatasi ~60 event/detik agar tidak membanjiri browser/proxy)
      limit        : jumlah event maksimum yang dikirim
      alerts_only  : 1 -> hanya memancarkan event 'alert' (untuk kanal notifikasi)
    Setiap kali stream melewati user+tanggal yang ada di outputs/alerts.jsonl,
    satu event 'alert' dipancarkan (tanpa skor ulang — fitur = agregat user-hari).
    """
    limit = int(request.args.get("limit", 1000))
    speedup = float(request.args.get("speedup", "100") or 0)
    alerts_only = request.args.get("alerts_only", "") in ("1", "true", "yes")

    df = _load_events()
    if df is None or len(df) == 0:
        return jsonify({"events": [], "available": False})

    alerts = _alert_index()

    def gen():
        sent = 0
        last = 0.0
        seen_alerts = set()
        try:
            for ev in replay(df, speedup=speedup):
                if sent >= limit:
                    break
                sent += 1
                evd = dict(ev)
                # Pacing hanya untuk mode event (ada tampilan yang harus diatur tempo).
                # Mode alerts_only menyapu secepat mungkin — hanya alert yang dikirim.
                if not alerts_only:
                    now = time.monotonic()
                    if last and now - last < MIN_EVENT_INTERVAL:
                        time.sleep(MIN_EVENT_INTERVAL - (now - last))
                    last = time.monotonic()
                key = (evd.get("user"), str(evd.get("ts"))[:10])
                a = alerts.get(key)
                if a is not None and key not in seen_alerts:
                    seen_alerts.add(key)
                    yield f"event: alert\ndata: {_sse_json(a)}\n\n"
                if not alerts_only:
                    yield f"event: event\ndata: {_sse_json(evd)}\n\n"
        except GeneratorExit:
            return  # klien menutup koneksi — hentikan replay
        yield "event: end\ndata: {}\n\n"

    return Response(
        stream_with_context(gen()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # matikan buffering nginx agar stream langsung mengalir
            "Connection": "keep-alive",
        },
    )


# ─── Penyajian dashboard-ui (hasil `make ui`) ──────────────────────────────
# static/ diisi dengan menyalin hasil build dashboard-ui/dist (lihat Makefile).
# Bila static/ belum ada, `/` tetap menyajikan dashboard lama (templates/).
STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.get("/")
def index():
    if (STATIC_DIR / "index.html").exists():
        return send_from_directory(STATIC_DIR, "index.html")
    return render_template("index.html")


@app.get("/legacy")
def legacy():
    """Dashboard lama (templates/index.html) — tetap tersedia apa adanya."""
    return render_template("index.html")


@app.get("/<path:rel>")
def static_files(rel):
    """Berkas statis dashboard-ui (halaman & aset ter-hash). Route API tetap prioritas."""
    if rel.startswith("api/") or rel == "health":
        return jsonify({"error": "not found"}), 404
    target = (STATIC_DIR / rel).resolve()
    if str(target).startswith(str(STATIC_DIR)) and target.is_file():
        return send_from_directory(STATIC_DIR, rel)
    if (STATIC_DIR / f"{rel}.html").is_file():  # mis. /dashboard -> dashboard.html
        return send_from_directory(STATIC_DIR, f"{rel}.html")
    if (STATIC_DIR / rel / "index.html").is_file():  # mis. /dashboard -> dashboard/index.html
        return send_from_directory(STATIC_DIR, f"{rel}/index.html")
    return jsonify({"error": "not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

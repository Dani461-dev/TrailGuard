"""Penjelasan alert — tiga metode, dicatat di alert['explain_method'] (itu dasar klaim di pitch):

  shap       : library `shap` (shap.Explainer + model-agnostik).  BUTUH paket shap -> uji di s390x dulu!
  shapley    : nilai Shapley dengan sampling permutasi, implementasi SENDIRI (pure numpy, jalan di mana saja).
               Sifat 'efficiency' berlaku persis: sum(kontribusi) + base = f(x).
  deviation  : seberapa jauh fitur menyimpang dari kebiasaan user itu sendiri (z-score). Fallback terakhir.

ATURAN KLAIM: tulis "SHAP" HANYA jika explain_method == 'shap'. Jika 'shapley' tulis
"Shapley-value explanations (own sampling implementation, SHAP-style)". Jika 'deviation' jangan sebut SHAP.
"""
import numpy as np

from .score import risk_from_array


def label_of(col: str, labels: dict) -> str:
    return "deviasi " + labels[col[:-2]] if col.endswith("_z") else labels.get(col, col)


# ---------- 1) deviasi (fallback) ----------
def explain_row(row, base_cols, labels, top_k=3):
    items = []
    for c in base_cols:
        z = float(row[f"{c}_z"])
        if z > 0.5:
            items.append({"feature": c, "label": labels[c], "value": float(row[c]), "z": round(z, 2)})
    return sorted(items, key=lambda d: d["z"], reverse=True)[:top_k]


# ---------- 2) Shapley sampling (implementasi sendiri) ----------
def shapley_values(f, x, background, n_samples=60, seed=0):
    """Estimasi nilai Shapley fitur-demi-fitur untuk fungsi f (array (n,d)->(n,)) pada titik x.
    Untuk tiap sampel: pilih 1 baris background & 1 permutasi fitur, ubah fitur dari background ke x
    satu per satu; selisih prediksi = kontribusi marginal. Rata-rata atas sampel -> estimasi Shapley.
    Return (phi[d], base_value) dengan sum(phi) + base = f(x) tepat (efficiency)."""
    rng = np.random.default_rng(seed)
    x = np.asarray(x, dtype=float)
    d = len(x)
    B = background[rng.integers(0, len(background), n_samples)]
    perms = np.array([rng.permutation(d) for _ in range(n_samples)])
    pts = np.empty((n_samples, d + 1, d))
    for s in range(n_samples):
        cur = B[s].astype(float).copy()
        pts[s, 0] = cur
        for k, j in enumerate(perms[s]):
            cur = cur.copy()
            cur[j] = x[j]
            pts[s, k + 1] = cur
    pred = np.asarray(f(pts.reshape(-1, d))).reshape(n_samples, d + 1)   # satu panggilan model sekaligus
    diff = pred[:, 1:] - pred[:, :-1]
    phi = np.zeros(d)
    for s in range(n_samples):
        np.add.at(phi, perms[s], diff[s])
    return phi / n_samples, float(pred[:, 0].mean())


# ---------- 3) library SHAP ----------
def shap_library_values(f, x, background):
    """UNTESTED di sandbox pengembangan (shap tidak terpasang). Uji dengan `make shap-check` di LinuxONE.
    Melempar ImportError bila shap tidak ada -> pemanggil akan fallback ke shapley sendiri."""
    import shap  # noqa: F401  (import gagal = shap tidak bisa dipakai di mesin ini)
    explainer = shap.Explainer(f, background)
    ex = explainer(np.asarray(x, dtype=float).reshape(1, -1))
    return np.asarray(ex.values)[0], float(np.asarray(ex.base_values).ravel()[0])


# ---------- gabungan ----------
def _aggregate(phi, x, feature_cols, base_cols, labels, row, top_k):
    """Jumlahkan kontribusi kolom dasar + kolom _z-nya -> satu alasan per perilaku (lebih mudah dibaca)."""
    agg = {}
    for c, v in zip(feature_cols, phi):
        agg[c[:-2] if c.endswith("_z") else c] = agg.get(c[:-2] if c.endswith("_z") else c, 0.0) + float(v)
    top = sorted(agg.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
    return [{"feature": c, "label": labels[c], "value": float(row[c]), "contribution": round(v, 4)}
            for c, v in top if v > 0]


def explain_alert(bundle, row, cfg, spec, w_sup):
    """Kembalikan (reasons, method_used). Urutan: shap -> shapley -> deviation."""
    ec = cfg.get("explain", {})
    want, top_k = ec.get("method", "shapley"), ec.get("top_k", 3)
    f = lambda X: risk_from_array(bundle, X, w_sup)[0]  # noqa: E731
    x = row[bundle["feature_cols"]].values.astype(float)
    bg = bundle["background"]
    if want == "shap":
        try:
            phi, _ = shap_library_values(f, x, bg)
            return _aggregate(phi, x, bundle["feature_cols"], spec.BASE_COLS, spec.FEATURE_LABELS, row, top_k), "shap"
        except Exception as e:                      # ImportError / masalah numba / dll.
            _warn_once(f"shap gagal ({type(e).__name__}: {str(e)[:60]}) -> pakai Shapley sendiri")
            want = "shapley"
    if want == "shapley":
        phi, _ = shapley_values(f, x, bg, ec.get("n_samples", 60))
        return _aggregate(phi, x, bundle["feature_cols"], spec.BASE_COLS, spec.FEATURE_LABELS, row, top_k), "shapley"
    return explain_row(row, spec.BASE_COLS, spec.FEATURE_LABELS, top_k), "deviation"


_warned = set()


def _warn_once(msg):
    if msg not in _warned:
        print("[explain] PERINGATAN:", msg)
        _warned.add(msg)

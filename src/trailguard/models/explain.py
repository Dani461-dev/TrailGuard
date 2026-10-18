"""Penjelasan alert — tiga metode, dicatat di alert['explain_method'] (itu dasar klaim di pitch):

  shap       : library `shap` (shap.Explainer + model-agnostik).  BUTUH paket shap -> uji di s390x dulu!
  shapley    : nilai Shapley dengan sampling permutasi, implementasi SENDIRI (pure numpy, jalan di mana saja).
               Sifat 'efficiency' berlaku persis: sum(kontribusi) + base = f(x).
  deviation  : seberapa jauh fitur menyimpang dari kebiasaan user itu sendiri (z-score). Fallback terakhir.

ATURAN KLAIM: tulis "SHAP" HANYA jika explain_method == 'shap'. Jika 'shapley' tulis
"Shapley-value explanations (own sampling implementation, SHAP-style)". Jika 'deviation' jangan sebut SHAP.
"""
import numpy as np

from ..features.registry import z_suffix_of
from .score import risk_from_array


def label_of(col: str, labels: dict) -> str:
    s = z_suffix_of(col)
    return "deviasi " + labels.get(col[: -len(s)], col[: -len(s)]) if s else labels.get(col, col)


# ---------- 1) deviasi (fallback) ----------
def explain_row(row, base_cols, labels, top_k=3):
    """Fallback termurah: seberapa jauh fitur menyimpang dari kebiasaan user itu sendiri (z-score).
    Mengenali kolom z dari builder ('*_z') maupun dari jalur notebook ('*_zscore_7d', '*_pop_z')."""
    items = []
    for c in base_cols:
        zc = next((f"{c}{s}" for s in ("_z", "_zscore_7d", "_zscore_7w", "_pop_z") if f"{c}{s}" in row.index), None)
        if zc is None:
            continue
        z = float(row[zc])
        if z > 0.5:
            items.append({"feature": c, "label": labels.get(c, c), "value": float(row[c]), "z": round(z, 2)})
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
def _aggregate(phi, x, feature_cols, labels, row, top_k):
    """Jumlahkan kontribusi kolom deviasi ke kolom dasarnya -> satu alasan per perilaku (lebih mudah dibaca).
    Nama kolom dasar bisa berbeda antar jalur fitur; yang dipakai adalah kolom yang benar-benar ada di baris."""
    agg = {}
    for c, v in zip(feature_cols, phi):
        s = z_suffix_of(c)
        key = c[: -len(s)] if s else c
        val, rep = agg.get(key, (0.0, key))
        agg[key] = (val + float(v), key if key in row.index else c)
    top = sorted(agg.items(), key=lambda kv: kv[1][0], reverse=True)[:top_k]
    return [{"feature": k, "label": labels.get(k, k), "value": float(row[rep]),
             "kind": "count" if rep == k else "z", "contribution": round(val, 4)}
            for k, (val, rep) in top if val > 0]


def explain_alert(bundle, row, cfg, labels, base_cols=None):
    """Kembalikan (reasons, method_used). Urutan: shap -> shapley -> deviation."""
    ec = cfg.get("explain", {})
    want, top_k = ec.get("method", "shapley"), ec.get("top_k", 3)
    cols = bundle["feature_cols"]
    base = base_cols or [c for c in cols if not z_suffix_of(c)]
    f = lambda X: risk_from_array(bundle, X)[0]  # noqa: E731
    if bundle.get("combine_method") == "rank":
        # Peringkat butuh pembanding dalam satu batch -> kontribusi per baris tidak terdefinisi.
        # Penjelasan dihitung pada varian berbobot dengan alpha yang sama, dan hal ini dicatat
        # supaya tidak dijual sebagai "penjelasan skor yang dipakai".
        _warn_once("combine_method=rank -> penjelasan dihitung pada varian berbobot (alpha sama)")
        f = lambda X: risk_from_array({**bundle, "combine_method": "weighted"}, X)[0]  # noqa: E731
    x = row[cols].values.astype(float)
    bg = bundle["background"]
    if want == "shap":
        try:
            phi, _ = shap_library_values(f, x, bg)
            return _aggregate(phi, x, cols, labels, row, top_k), "shap"
        except Exception as e:                      # ImportError / masalah numba / dll.
            _warn_once(f"shap gagal ({type(e).__name__}: {str(e)[:60]}) -> pakai Shapley sendiri")
            want = "shapley"
    if want == "shapley":
        phi, _ = shapley_values(f, x, bg, ec.get("n_samples", 60))
        return _aggregate(phi, x, cols, labels, row, top_k), "shapley"
    return explain_row(row, base, labels, top_k), "deviation"


_warned = set()


def _warn_once(msg):
    if msg not in _warned:
        print("[explain] PERINGATAN:", msg)
        _warned.add(msg)

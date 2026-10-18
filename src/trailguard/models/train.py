"""Latih model hibrida: supervised (pola dikenal) + Isolation Forest (perilaku baru).

SEMUA hyperparameter dipilih di sepotong VALIDASI temporal (hari-hari terakhir dari periode
train), BUKAN di test -- test hanya dipakai sekali, di step 'evaluate':
  * bobot positif supervised -> kelas sangat langka; bobot berlebih membuat model hafal
  * cara menggabungkan skor   -> rata-rata berbobot vs maksimum vs peringkat
                                (menjawab TODO B-Model di score.py; semua diukur, bukan ditebak)
  * alpha                     -> bobot supervised pada gabungan. Grid-nya juga memuat 0.0 dan 1.0
                                (= murni anomaly / murni supervised), jadi hibrida harus membuktikan
                                dirinya sendiri di validasi, bukan menang karena dipilih paksa
  * ambang tier 2 & 3         -> dikalibrasi supaya tier 3 (tiket analis) benar-benar langka
Kandidat beserta skornya ikut tersimpan di bundle (kunci 'selection') supaya bisa dijawab saat
juri bertanya: "angka ini dari mana?".
"""
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, f1_score

from .score import anomaly01, combine_scores, fit_isolation, iso_range

WEIGHT_EXP_GRID = (0.5, 0.75, 1.0)   # pos_w = (n_neg/n_pos) ** eksponen, dibatasi 50
ALPHA_GRID = (0.0, 0.4, 0.6, 0.8, 0.95, 1.0)
METHODS = ("weighted", "max", "rank")
VAL_FRACTION = 0.2                   # 20% hari terakhir dari train = validasi
MIN_VAL_POSITIVES = 5                # validasi harus punya cukup kasus positif agar tuning bermakna
MIN_FIT_FRACTION = 0.5               # batas: minimal separuh hari train tetap untuk melatih


def temporal_split(feat: pd.DataFrame, train_fraction: float):
    """Split berdasarkan WAKTU (bukan acak) agar tidak ada kebocoran masa depan."""
    days = np.sort(feat["day"].unique())
    cut = days[int(len(days) * train_fraction)]
    return feat[feat.day < cut].copy(), feat[feat.day >= cut].copy(), cut


def split_last(feat: pd.DataFrame, fraction: float,
               min_positives: int = 0, min_fit_fraction: float = MIN_FIT_FRACTION):
    """Potong bagian BELAKANG sebuah periode sebagai validasi (tetap temporal, bukan acak).

    Bila validasi tidak memuat label positif, tuning tak bisa diukur sama sekali. Di LANL ini
    benar-benar terjadi: serangan red-team menggerombol di hari-hari AWAL data, sehingga 20% hari
    terakhir dari periode train kosong dari label. Karena itu potongan validasi DIPERLEBAR ke
    belakang sampai memuat `min_positives` kasus; urutannya tetap (latih di masa lalu, validasi di
    masa sesudahnya) dan validasi tidak pernah lebih besar dari `min_fit_fraction` seluruh periode.
    """
    days = np.sort(feat["day"].unique())
    n = len(days)
    k = max(int(n * fraction), 1)
    if min_positives:
        floor_k = max(int(n * (1 - min_fit_fraction)), 1)
        while k > floor_k and int(feat.loc[feat.day >= days[k], "label"].sum()) < min_positives:
            k -= 1
    return feat[feat.day < days[k]].copy(), feat[feat.day >= days[k]].copy()


def _fit_sup(X, y, pos_w, rs):
    m = HistGradientBoostingClassifier(random_state=rs)
    m.fit(X, y, sample_weight=np.where(y == 1, pos_w, 1.0))
    return m


def _pr_auc(model, X, y) -> float:
    return float("nan") if y.sum() == 0 else float(average_precision_score(y, model.predict_proba(X)[:, 1]))


def calibrate_thresholds(y, risk) -> dict:
    """Kalibrasi ambang tier dari VALIDASI (bukan test).

    - tier 2 (verifikasi tambahan): ambang F1 terbaik di validasi, tetapi TIDAK boleh lebih rendah
      dari persentil 90 skor user-hari NORMAL. Tanpa batas itu, validasi yang "terpojok" bisa
      membuat semua alert jadi tier 3 dan cerita "manusia menyetujui" jadi tidak masuk akal.
    - tier 3 (tiket analis): ambang langka -> persentil 99,5 skor normal, dijaga tetap di atas tier 2.
    """
    y = np.asarray(y)
    normal = risk[y == 0]
    grid = np.unique(np.quantile(risk, np.linspace(0.5, 1.0, 201)))
    f1_best, t2 = -1.0, 0.5
    for cand in grid:
        f = f1_score(y, risk >= cand, zero_division=0)
        if f > f1_best:
            f1_best, t2 = f, float(cand)
    floor = float(np.quantile(normal, 0.90)) if len(normal) else 0.0
    t2 = float(np.clip(t2, floor, 0.95))
    t3 = float(np.quantile(normal, 0.995)) if len(normal) else 0.95
    t3 = float(np.clip(max(t3, t2 + 0.05), t2 + 0.02, 0.99))
    return {"step_up_threshold": round(t2, 4), "ticket_threshold": round(t3, 4),
            "val_f1_at_step_up": round(float(f1_score(y, risk >= t2, zero_division=0)), 4),
            "val_f1_best_threshold": round(float(f1_best), 4),
            "tier2_floor_p90_normal": round(floor, 4)}


def train_models(train: pd.DataFrame, cfg: dict, feature_cols: list) -> dict:
    mc = cfg["model"]
    rs = mc["random_state"]
    X, y = train[feature_cols].values, train["label"].values
    fit, val = split_last(train, 1 - VAL_FRACTION, MIN_VAL_POSITIVES)
    Xtr, ytr, Xva, yva = fit[feature_cols].values, fit["label"].values, val[feature_cols].values, val["label"].values

    selection = {"val_rows": int(len(val)), "val_positives": int(yva.sum()),
                 "val_fraction_of_train": VAL_FRACTION}
    sup, pos_w = None, mc.get("positive_class_weight", None)
    alpha, method = mc["ensemble_weight_supervised"], "weighted"
    thresholds = None

    if y.sum() == 0:
        print("[train] PERINGATAN: tidak ada label positif di train -> hanya Isolation Forest")
    elif yva.sum() == 0 or ytr.sum() == 0:
        # Validasi (atau bagian awal train) tak berlabel -> tuning tidak bisa DIUKUR. Cabang
        # supervised JANGAN dibuang: ia tetap dilatih pada seluruh periode train dengan bobot yang
        # wajar, sementara alpha tetap dari config dan TIDAK diklaim sebagai hasil tuning.
        if pos_w is None:
            ratio = (len(y) - y.sum()) / max(y.sum(), 1)
            pos_w = min(ratio ** 0.75, 50.0)          # titik tengah grid bobot
        print(f"[train] PERINGATAN: validasi temporal tak berlabel (val positif={int(yva.sum())}, "
              f"train positif={int(ytr.sum())}) -> tuning dilewati; supervised dilatih pada seluruh "
              f"train dgn bobot {round(float(pos_w), 2)}, alpha dari config ({alpha})")
        sup = _fit_sup(X, y, float(pos_w), rs)
    else:
        ratio = (len(ytr) - ytr.sum()) / max(ytr.sum(), 1)
        cands = []
        for e in WEIGHT_EXP_GRID:
            w = min(ratio ** e, 50.0)
            m = _fit_sup(Xtr, ytr, w, rs)
            cands.append({"method": "sup", "pos_weight_exp": e, "pos_weight": round(w, 2),
                          "val_pr_auc": round(_pr_auc(m, Xva, yva), 4), "_model": m})
        best = max(cands, key=lambda c: c["val_pr_auc"])
        sup, pos_w = best["_model"], best["pos_weight"]
        selection["supervised_candidates"] = [{k: v for k, v in c.items() if k != "_model"} for c in cands]

        iso_va = fit_isolation(Xtr[ytr == 0], mc["isolation_forest"]["n_estimators"], rs)
        lo_va, hi_va = iso_range(iso_va, Xtr)
        an_va = anomaly01(iso_va, Xva, lo_va, hi_va)
        sup_va = sup.predict_proba(Xva)[:, 1]
        combos = []
        for meth in METHODS:
            for a in (ALPHA_GRID if meth == "weighted" else (0.5,)):
                r = combine_scores(sup_va, an_va, meth, a)
                combos.append({"combine_method": meth, "alpha": round(a, 3),
                               "val_pr_auc": round(float(average_precision_score(yva, r)), 4)})
        bestc = max(combos, key=lambda c: c["val_pr_auc"])
        method, alpha = bestc["combine_method"], bestc["alpha"]
        selection["combination_candidates"] = combos
        selection["winner"] = dict(bestc)
        thresholds = calibrate_thresholds(yva, combine_scores(sup_va, an_va, method, alpha))
        print(f"[train] gabungan terpilih: {method} (alpha={alpha}) | val PR-AUC "
              f"{bestc['val_pr_auc']:.4f} | ambang tier2={thresholds['step_up_threshold']} "
              f"tier3={thresholds['ticket_threshold']}")
        # refit pada SELURUH periode train (hyperparameter sudah dikunci lewat validasi)
        sup = _fit_sup(X, y, float(pos_w), rs)

    iso = fit_isolation(X[y == 0], mc["isolation_forest"]["n_estimators"], rs)  # belajar "perilaku normal"
    lo, hi = iso_range(iso, X)

    normal = train[train.label == 0][feature_cols]
    return {"sup": sup, "iso": iso, "an_lo": lo, "an_hi": hi,
            "base_mean": normal.mean().to_dict(), "base_std": normal.std().replace(0, 1).to_dict(),
            "feature_cols": feature_cols,
            # baris 'normal' sebagai pembanding untuk penjelasan SHAP/Shapley
            "background": normal.sample(min(200, len(normal)), random_state=rs).values,
            # tambahan Kontrak #4: hasil tuning (semuanya bisa ditelusuri ke validasi)
            "alpha": float(alpha), "combine_method": method, "thresholds": thresholds,
            "positive_class_weight": None if pos_w is None else float(pos_w),
            "selection": selection}


def save_bundle(bundle: dict, path):
    joblib.dump(bundle, path)


def load_bundle(path) -> dict:
    return joblib.load(path)

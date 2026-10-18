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
"""Evaluasi realistis untuk data sangat langka: alert budget + time-to-detection.

Aturan jujur yang dijaga di sini (lihat B5 & R13 di docs/01_TEAM_ROLES.md):
  * semua angka dihitung pada potongan TEST, bukan train/validasi;
  * model utama SELALU dibandingkan dengan pembanding yang memakai alert budget & potongan yang
    SAMA -- tanpa itu "precision 0.30" tidak berarti apa-apa;
  * jumlah insider yang tertangkap dihitung per ORANG, bukan per baris event;
  * pembanding "z-score" memakai deviasi fitur apa adanya, jadi kalau model kalah dari pembanding
    itu, itu harus tetap dilaporkan.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
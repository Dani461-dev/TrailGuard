"""Memilih modul fitur sesuai cfg['dataset'] (cert | lanl) + kamus label untuk penjelasan alert."""
from . import builder as cert
from . import builder_lanl as lanl

# Nama fitur dari jalur notebook Grup B (01_B1_CERT_Features / 02_B2_LANL_and_Unsupervised).
# Dicatat di sini supaya penjelasan alert tetap berbahasa manusia walaupun fiturnya berasal dari
# jalur lain (lihat pipeline._normalize_feat). Nama yang tak dikenal akan tampil sebagai nama kolom.
NOTEBOOK_LABELS = {
    # CERT -- kolom dasar (hitungan harian)
    "logon_count": "jumlah logon", "off_hours_logon": "logon di luar jam kerja",
    "unique_pcs": "jumlah komputer berbeda", "usb_connect_count": "pemakaian USB",
    "file_activity_count": "operasi file", "external_email_count": "email ke luar organisasi",
    "http_visit_count": "kunjungan web",
    # CERT -- kolom turunan notebook (nama pendek ini adalah AWALAN dari `_zscore_7d`/`_spike_ratio`)
    "logon": "perubahan pola logon (7 hari)", "off_hours": "perubahan pola logon luar jam kerja (7 hari)",
    "usb": "perubahan pola pemakaian USB (7 hari)", "file": "perubahan pola operasi file (7 hari)",
    "email": "perubahan pola email keluar (7 hari)", "http": "perubahan pola kunjungan web (7 hari)",
    # LANL
    "total_auth": "autentikasi", "fail_auth": "autentikasi gagal",
    "unique_src": "komputer asal berbeda", "unique_dst": "komputer tujuan berbeda",
    "new_dst": "komputer tujuan baru", "new_src": "komputer asal baru", "new_pair": "pasangan baru",
    "total_auth_events": "jumlah autentikasi", "fail_auth_count": "autentikasi gagal",
    "off_hours_event_ratio": "porsi aktivitas di luar jam kerja",
    "unique_src_computers": "komputer asal berbeda", "unique_dst_computers": "komputer tujuan berbeda",
    "network_logon_ratio": "porsi logon jaringan", "kerberos_auth_ratio": "porsi autentikasi Kerberos",
    "ntlm_auth_ratio": "porsi autentikasi NTLM", "fail_auth_ratio": "rasio autentikasi gagal",
    "dst_per_src_ratio": "tujuan per komputer asal",
    "new_dst_computer_count": "komputer tujuan yang belum pernah dikunjungi",
    "new_src_computer_count": "komputer asal yang belum pernah terlihat",
    "new_pair_count": "pasangan asal-tujuan yang baru",
    "new_dst_ratio": "rasio tujuan baru", "new_src_ratio": "rasio komputer asal baru",
    "new_pair_ratio": "rasio pasangan baru",
}
# Sufiks yang menandai "ini deviasi dari baseline", untuk bermacam gaya penamaan fitur.
# URUTAN PENTING: periksa sufiks TERPANJANG lebih dulu, jika tidak `_pop_z`/`_zscore_7d` akan
# tertangkap oleh `_z` dan nama dasarnya salah (label alasan jadi mentah).
Z_SUFFIXES = ("_zscore_7d", "_zscore_7w", "_spike_ratio", "_spike_7w", "_pop_z", "_z")


def spec(cfg):
    return {"cert": cert, "lanl": lanl}[cfg.get("dataset", "cert")]


def feature_labels(cfg) -> dict:
    """Label milik builder diprioritaskan; nama fitur notebook jadi cadangan."""
    merged = dict(NOTEBOOK_LABELS)
    merged.update(spec(cfg).FEATURE_LABELS)
    return merged


def z_suffix_of(col: str):
    for s in Z_SUFFIXES:
        if col.endswith(s) and len(col) > len(s):
            return s
    return None
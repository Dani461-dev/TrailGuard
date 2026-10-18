from .builder import Z_CLIP, add_labels  # noqa: F401  (dipakai pipeline; label berbasis rentang waktu sama)

BASE_COLS = ["n_auth", "n_fail", "n_logon", "n_network_logon", "n_remote", "n_distinct_dst",
             "n_new_dst", "n_distinct_src", "n_new_src", "n_night", "n_new_hour"]
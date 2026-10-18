

def policy_cfg(cfg: dict, bundle: dict) -> dict:
    """Config dengan ambang tier hasil KALIBRASI VALIDASI (bundle['thresholds']).

    Model menyimpan ambang tier 2/3 yang dipilih di validasi temporal; pipeline & API memakai angka
    itu supaya tier pada alert konsisten dengan yang diukur di metrik. Bila bundle tidak punya
    (mis. model lama), angka dari config tetap dipakai. Ubah kontrak policy = bahas dengan C-Lead.
    """
    th = (bundle or {}).get("thresholds")
    if not th:
        return cfg
    keys = {k: th[k] for k in ("step_up_threshold", "ticket_threshold") if k in th}
    return {**cfg, "policy": {**cfg["policy"], **keys}}
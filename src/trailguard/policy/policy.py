"""Policy layer: skor risiko -> respons bertingkat. Sistem TIDAK pernah memblokir akun otomatis."""


def decide(risk: float, cfg: dict) -> dict:
    p = cfg["policy"]
    if risk >= p["ticket_threshold"]:
        return {"tier": 3, "action": "analyst_ticket", "requires_human_approval": True,
                "note": "Buat tiket untuk analis; tindakan lanjutan wajib disetujui manusia."}
    if risk >= p["step_up_threshold"]:
        return {"tier": 2, "action": "step_up_verification", "requires_human_approval": False,
                "note": "Minta verifikasi tambahan saat sesi berikutnya."}
    return {"tier": 1, "action": "log_only", "requires_human_approval": False,
            "note": "Catat saja."}


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

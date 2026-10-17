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

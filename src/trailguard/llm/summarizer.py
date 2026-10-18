"""Ringkasan kasus dalam bahasa biasa. HANYA menerima fitur ter-pseudonim (tidak ada ID asli).
Default = template (selalu jalan). LLM kecil = stretch goal."""


def template_summary(alert: dict) -> str:
    reasons = alert.get("reasons", [])
    if reasons:
        parts = []
        for r in reasons:
            if "contribution" in r:               # penjelasan Shapley/SHAP
                val = f"{r['value']:.2f} SD" if r.get("kind") == "z" else f"nilai {r['value']:.0f}"
                parts.append(f"{r['label']} ({val}, menambah risiko {r['contribution']:+.2f})")
            else:                                 # penjelasan deviasi
                parts.append(f"{r['label']} (nilai {r['value']:.0f}, {r['z']:+.1f} SD dari kebiasaan)")
        why = "; ".join(parts)
    else:
        why = "pola gabungan yang tidak biasa"
    return (f"Pengguna {alert['user'][:8]}… pada {alert['day']} berisiko {alert['risk']:.2f} "
            f"(tier {alert['tier']}: {alert['action']}). Penyebab utama: {why}. "
            f"{'Perlu persetujuan analis.' if alert['requires_human_approval'] else ''}").strip()


def llm_summary(alert: dict, model_path: str = None) -> str:
    """TODO(Grup C, STRETCH): panggil LLM kecil via llama-cpp-python bila terpasang.
    Prompt HANYA boleh memuat field ter-pseudonim. Fallback: template_summary(alert)."""
    return template_summary(alert)

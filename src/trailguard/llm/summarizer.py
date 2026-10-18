        parts = []
        for r in reasons:
            if "contribution" in r:               # penjelasan Shapley/SHAP
                val = f"{r['value']:.2f} SD" if r.get("kind") == "z" else f"nilai {r['value']:.0f}"
                parts.append(f"{r['label']} ({val}, menambah risiko {r['contribution']:+.2f})")
            else:                                 # penjelasan deviasi
                parts.append(f"{r['label']} (nilai {r['value']:.0f}, {r['z']:+.1f} SD dari kebiasaan)")
        why = "; ".join(parts)
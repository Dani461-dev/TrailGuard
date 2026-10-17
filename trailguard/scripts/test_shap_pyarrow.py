"""GO / NO-GO: apakah SHAP (library) dan pyarrow benar-benar jalan di mesin ini (LinuxONE s390x)?
Jalankan SEGERA setelah `make setup`:   make shap-check      (hasil juga disimpan di evidence/)

Cara memasang (beri batas waktu ±45 menit per paket; jika gagal catat pesan error di 05_DECISION_LOG.md):
  pip install pyarrow
  pip install shap          # menarik numba + llvmlite -> di s390x kemungkinan HARUS compile; butuh LLVM dev
                            # (Ubuntu: sudo apt install llvm-dev | RHEL: sudo dnf install llvm-devel)
"""
import platform
import sys
import time
from pathlib import Path

lines = [f"arsitektur={platform.machine()} python={sys.version.split()[0]} byteorder={sys.byteorder}"]
result = {}


def run(name, fn):
    t = time.time()
    try:
        info = fn()
        result[name] = True
        lines.append(f"[OK]    {name}: {info} ({time.time() - t:.1f}s)")
    except Exception as e:
        result[name] = False
        lines.append(f"[GAGAL] {name}: {type(e).__name__}: {str(e)[:120]}")


def t_pyarrow():
    import pandas as pd, pyarrow as pa, tempfile, os  # noqa: E401
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"], "t": pd.to_datetime(["2010-01-01"] * 3)})
    p = os.path.join(tempfile.mkdtemp(), "t.parquet")
    df.to_parquet(p, index=False)
    assert pd.read_parquet(p).equals(df), "round-trip parquet tidak identik"
    return f"pyarrow {pa.__version__}, parquet round-trip identik"


def t_shap():
    import numpy as np, shap  # noqa: E401
    from sklearn.ensemble import HistGradientBoostingClassifier
    rng = np.random.default_rng(0)
    X = rng.normal(size=(300, 6)); y = (X[:, 0] + X[:, 1] > 1).astype(int)
    m = HistGradientBoostingClassifier(random_state=0).fit(X, y)
    f = lambda a: m.predict_proba(a)[:, 1]  # noqa: E731
    ex = shap.Explainer(f, X[:50])(X[:3])
    top = int(np.argmax(np.abs(ex.values[0])))
    return f"shap {shap.__version__}, bentuk {ex.values.shape}, fitur teratas contoh = {top} (harus 0 atau 1)"


def t_own_shapley():
    import numpy as np
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from trailguard.models.explain import shapley_values
    w = np.array([3.0, -1.0, 0.0, 2.0])
    f = lambda X: X @ w  # noqa: E731
    bg = np.zeros((20, 4)); x = np.ones(4)
    phi, base = shapley_values(f, x, bg, 30)
    assert abs(phi.sum() + base - f(x[None])[0]) < 1e-9 and np.allclose(phi, w)
    return "Shapley sendiri benar (efficiency terpenuhi)"


run("pyarrow", t_pyarrow)
run("shap (library)", t_shap)
run("Shapley implementasi sendiri", t_own_shapley)

lines += ["", "=== KESIMPULAN KLAIM ==="]
lines.append("SHAP library : " + ("BOLEH klaim 'SHAP'." if result["shap (library)"] else
             "TIDAK bisa. Pakai 'Shapley-value explanations (implementasi sendiri, gaya SHAP)'. Jangan tulis 'SHAP library'."))
lines.append("Parquet      : " + ("BOLEH pakai io.format=parquet." if result["pyarrow"] else
             "TIDAK. Tetap CSV.gz; jangan klaim Parquet/pyarrow."))
text = "\n".join(lines)
print(text)
Path("evidence").mkdir(exist_ok=True)
Path("evidence/shap_pyarrow_check.txt").write_text(text + "\n")
sys.exit(0 if result["Shapley implementasi sendiri"] else 1)

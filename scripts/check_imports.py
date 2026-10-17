"""Cek paket Python mana yang bisa dipakai di mesin ini (penting untuk s390x)."""
import importlib
import platform
import sys

print(f"Arsitektur : {platform.machine()}  (LinuxONE = s390x)")
print(f"Python     : {sys.version.split()[0]}")
print(f"Byte order : {sys.byteorder}  (s390x = big)\n")
CORE = ["pandas", "numpy", "sklearn", "joblib", "yaml", "flask", "pytest"]
OPTIONAL = ["pyarrow", "shap", "numba", "lightgbm", "xgboost", "llama_cpp"]
bad = 0
for group, pk in (("INTI", CORE), ("OPSIONAL", OPTIONAL)):
    print(f"== {group} ==")
    for m in pk:
        try:
            mod = importlib.import_module(m)
            print(f"  OK    {m:12s} {getattr(mod, '__version__', '')}")
        except Exception as e:
            print(f"  GAGAL {m:12s} {type(e).__name__}: {str(e)[:70]}")
            bad += group == "INTI"
sys.exit(1 if bad else 0)

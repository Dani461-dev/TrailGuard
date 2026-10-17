"""Memilih modul fitur sesuai cfg['dataset'] (cert | lanl)."""
from . import builder as cert
from . import builder_lanl as lanl


def spec(cfg):
    return {"cert": cert, "lanl": lanl}[cfg.get("dataset", "cert")]

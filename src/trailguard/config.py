"""Pemuat konfigurasi. Semua path & parameter ada di configs/config.yaml."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_config(path=None) -> dict:
    path = Path(path) if path else ROOT / "configs" / "config.yaml"
    with open(path) as f:
        cfg = yaml.safe_load(f)
    return cfg


def path_of(cfg: dict, key: str) -> Path:
    """Path absolut dari kunci di cfg['paths']."""
    return ROOT / cfg["paths"][key]

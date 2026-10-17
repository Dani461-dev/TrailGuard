import pandas as pd

from trailguard.config import load_config
from trailguard.features.builder import FEATURE_COLS, build_daily_features
from trailguard.ingest.pseudonymize import pseudonymize
from trailguard.policy.policy import decide


def test_pseudonymize_deterministic_and_keyed():
    assert pseudonymize("ACM2278", b"k1") == pseudonymize("ACM2278", b"k1")
    assert pseudonymize("ACM2278", b"k1") != pseudonymize("ACM2278", b"k2")
    assert "ACM2278" not in pseudonymize("ACM2278", b"k1")


def test_policy_tiers_and_human_approval():
    cfg = load_config()
    assert decide(0.1, cfg)["action"] == "log_only"
    assert decide(0.7, cfg)["action"] == "step_up_verification"
    t3 = decide(0.95, cfg)
    assert t3["action"] == "analyst_ticket" and t3["requires_human_approval"] is True


def test_features_offhours_and_columns():
    cfg = load_config()
    ev = pd.DataFrame({
        "ts": pd.to_datetime(["2010-01-04 09:00", "2010-01-04 23:00"]),
        "user": ["u1", "u1"], "host": ["h1", "h2"], "source": ["logon", "logon"],
        "action": ["logon", "logon"], "target": ["", ""], "size": [0, 0]})
    f = build_daily_features(ev, cfg)
    assert set(FEATURE_COLS) <= set(f.columns)
    assert f.loc[0, "n_offhours_logon"] == 1 and f.loc[0, "n_distinct_host"] == 2


def test_shapley_efficiency_and_linear_exactness():
    import numpy as np
    from trailguard.models.explain import shapley_values
    w = np.array([3.0, -1.0, 0.0, 2.0])
    f = lambda X: X @ w                      # noqa: E731
    bg, x = np.zeros((10, 4)), np.array([1.0, 2.0, 3.0, 4.0])
    phi, base = shapley_values(f, x, bg, n_samples=40)
    assert abs(phi.sum() + base - f(x[None])[0]) < 1e-9      # efficiency
    assert np.allclose(phi, w * x)                           # fungsi linear -> Shapley eksak


def test_io_parquet_falls_back_to_csv_without_pyarrow(tmp_path):
    import pandas as pd
    from trailguard import io_utils
    cfg = {"io": {"format": "parquet"}, "paths": {"t": "x.csv.gz"}}
    orig = io_utils.path_of
    io_utils.path_of = lambda c, k: tmp_path / "x.csv.gz"      # path sementara untuk tes
    try:
        df = pd.DataFrame({"a": [1, 2]})
        io_utils.write_table(df, cfg, "t")
        assert io_utils.read_table(cfg, "t")["a"].tolist() == [1, 2]
    finally:
        io_utils.path_of = orig

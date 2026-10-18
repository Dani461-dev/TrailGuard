# TrailGuard — Privacy-Preserving, Explainable Insider-Threat Detection on IBM LinuxONE

**[TeamName]_IBM Z Datathon 2026 Project** · Event code: `SSF2026` · Theme: *AI Secured — Innovation Without Exposure*

> Status: **kerangka (skeleton)** — bagian bertanda `TODO` dikerjakan selama datathon. Dokumen internal tim ada di [`docs/`](docs/).

## What it does
Replays multi-source activity logs as an event stream **inside a containerized LinuxONE environment**, pseudonymizes identities at ingestion (keyed HMAC), maintains per-user behavioral baselines, scores risk with a **hybrid model** (supervised gradient boosting + Isolation Forest), explains each alert, and maps risk to **tiered responses with mandatory human approval** for high-impact actions.

```
logs → pseudonymize → features → hybrid models → risk + reasons → policy tier → analyst
                  (all stages run on IBM LinuxONE)
```
*(TODO: replace with the final architecture figure)*

## Quick start (on the LinuxONE VM)
```bash
git clone <repo-url> && cd trailguard
bash scripts/00_check_env.sh        # architecture & tools check (expect s390x)
bash scripts/01_setup_env.sh        # venv + dependencies
cp .env.example .env && nano .env   # set TRAILGUARD_HMAC_KEY (never commit)
set -a; source .env; set +a
make toy                            # synthetic CERT-style data + full pipeline (< 1 min, writes outputs/toy_*)
make lanl-toy                       # synthetic LANL-style data + LANL pipeline (writes outputs/lanl_toy_*)
make shap-check                     # does SHAP / pyarrow actually work on this machine?
make test                           # unit tests
make api                            # dashboard on :8000
make bench                          # latency / throughput
make container                      # build & run in podman/docker
```
Real data (after placing the datasets — see [`data/README.md`](data/README.md)):
```bash
make run                            # full CERT pipeline on data/configs path (paths.raw = data/raw/cert_r4.2)
make prefilter-lanl                 # stream auth.txt + redteam.txt -> hashed LANL subset (key from .env)
make lanl-run                       # full LANL pipeline on that subset
```
> `make toy` / `make lanl-toy` write to **separate** output paths (`outputs/toy_*`, `outputs/lanl_toy_*`),
> so a quick smoke test can never overwrite the real `outputs/metrics.json` / `alerts.jsonl`.

## Repository layout
```
configs/        all parameters (config.yaml)
src/trailguard/
  ingest/       loaders (CERT, LANL), pseudonymize (HMAC), replay (stream simulation)
  features/     per-user-day behavioral features + baseline deviations (CERT: builder.py, LANL: builder_lanl.py)
  models/       train (temporal split), score, evaluate (alert budget), explain (SHAP / Shapley / deviation)
  policy/       tiered responses, human approval
  llm/          case summaries (template; small local LLM = optional)
  api/          Flask API + dashboard
  pipeline.py   CLI: ingest → features → train → evaluate → score
scripts/        env check, setup, toy data (CERT/LANL), LANL prefilter, SHAP/pyarrow check, benchmark, evidence
deploy/         Dockerfile, run_container.sh
tests/  docs/  evidence/
```

## Datasets
Two datasets, evaluated separately (different environments): **CMU CERT Insider Threat** (insider misuse) and **LANL** authentication logs with red-team labels. See [`data/README.md`](data/README.md) for schema, sizes and the two r4.2 label traps.

- **CERT r4.2** — 330,285 user-days (1,000 users, 501 days, 1,364 labelled malicious user-days covering **all 70 r4.2 insiders**). Features come from the Group-B notebook pilot and use `shift(1)` baselines (no leakage).
- **LANL** — used as a **streaming subset**: all red-team victim users + a 2.5% sample of normal users, system accounts dropped, cut off two days after the last red-team event. **15,065,146 auth rows → 15,065 user-days, 1,247 users, 181 labelled user-days (104 red-team users, 749 events)**. LANL's `time` is anonymized and **only relative**, so its "days" are not calendar dates.

## Explainability
The method actually used for each alert is recorded per row in `outputs/alerts.jsonl` (`explain_method`), and that field is the **only** basis for any SHAP claim.

In the run behind the numbers below the `shap` library was **not** installed on the analysis machine (its install is a go/no-go item on LinuxONE, see `make shap-check`). Therefore every explained alert used **our own Shapley-value sampling implementation** (`models/explain.py`) and is described as *Shapley-value explanations (own implementation, SHAP-style)* — **not** as "SHAP". Alerts that are not worth the compute (or fall outside `explain.max_alerts` / `explain.min_tier`) carried a cheap deviation explanation instead:

| `explain_method` | Alerts (CERT run) | Meaning |
|---|---|---|
| `shap` | 0 | library path (only if `shap` actually ran) |
| `shapley` | 300 | own permutation-sampling Shapley (exact efficiency: `Σφ + base = f(x)`) |
| `deviation` | 579 | per-feature z-score vs the user's own baseline (cheaper fallback) |

## Results
All numbers below are copied from [`outputs/metrics.json`](outputs/metrics.json) (CERT) and [`outputs/lanl_metrics.json`](outputs/lanl_metrics.json) (LANL). Nothing here comes from toy data. Split is **temporal** (no random split anywhere), metric is **alerts per day (budget)**, never accuracy.

### CERT r4.2 — test window 2010-11-23 … 2011-05-17 (176 days, 106,272 user-days, 489 malicious)
| Metric (alert budget = 5/day) | Value |
|---|---|
| Precision @ budget | **0.4608** |
| Recall @ budget | **0.8282** |
| Insiders detected / total in test | **26 / 27** |
| Median days to detection | **0.0** |
| Model actually used | supervised `HistGradientBoostingClassifier` (see note) |
| PR-AUC train → val → test | 0.9933 → 0.9956 → **0.9222** |

Comparators on the **same** test slice and the same budget:

| Explanation | Precision @ budget | Recall @ budget | Insiders |
|---|---|---|---|
| TrailGuard (selected model) | 0.4608 | 0.8282 | 26/27 |
| supervised only | 0.4608 | 0.8282 | 26/27 |
| Isolation Forest only (no labels) | 0.0091 | 0.0164 | 7/27 |
| max-abs-z baseline | 0.0125 | 0.0225 | 11/27 |
| random | 0.0046 | 0.0082 | 4/27 |

### LANL subset — test window (12 days, 5,846 user-days, only 34 malicious user-days)
| Metric (alert budget = 5/day) | Value |
|---|---|
| Precision @ budget | 0.0833 |
| Recall @ budget | 0.1471 |
| Insiders detected / total in test | 4 / 26 |
| PR-AUC: fit / validation / **test** | 0.9988 / 0.9901 / **0.1030** |

Comparators on the same test slice and budget (LANL):

| Explanation | Precision @ budget | Recall @ budget | Insiders |
|---|---|---|---|
| TrailGuard (selected model) | 0.0833 | 0.1471 | 4/26 |
| supervised only | 0.0833 | 0.1471 | 4/26 |
| Isolation Forest only (no labels) | 0.0500 | 0.0882 | 1/26 |
| max-abs-z baseline | 0.0167 | 0.0294 | 1/26 |
| random | 0.0000 | 0.0000 | 0/26 |

**These LANL numbers are a negative result and we report them as such** (also flagged as risk R13 in the project plan): with 181 labelled user-days clustered in the early part of an anonymized 32-day window, the model scores 0.99 on validation and collapses to 0.10 on the later test window. We did **not** tune on the test set to hide this.

**Model selection (why the "hybrid" is really the supervised branch here).** `alpha` = weight of the supervised branch is one of several hyperparameters chosen **only on a temporal validation slice**, and its grid deliberately contains `0.0` (pure anomaly) and `1.0` (pure supervised). On both datasets validation selected `weighted, alpha = 1.0`, i.e. the Isolation Forest did **not** add measurable value at that operating point — so the pipeline uses the supervised branch and says so in `metrics.model.description`. The full candidate list (weight grid, `alpha` grid, `weighted`/`max`/`rank`) is stored in `model_selection` in the metrics file, and the Isolation-Forest-only and z-score comparators above show what the unsupervised branch does on its own. `make run` on a different dataset can select a different `alpha` — nothing is hard-coded.

## How it uses IBM Z / LinuxONE  *(TODO — only claims backed by screenshots in `evidence/`)*
- Platform: LinuxONE Community Cloud, `s390x` (screenshot)
- Containerized deployment (screenshot)
- Measured per-event latency / throughput: TODO (`outputs/benchmark.json`)
- Identity data and the pseudonymization key never leave the instance

## Limitations
Measured, not boilerplate. Each item is traceable to `outputs/metrics.json`, `outputs/lanl_metrics.json`, `model_selection` in those files, or the dataset notes in [`data/README.md`](data/README.md).

**Data**
- Public datasets are synthetic (CERT) / de-identified (LANL) and do not fully represent production networks. CERT research data is *simulated* insider behaviour; LANL red-team labels are *known compromised credentials*, not confirmed insider misuse.
- **CERT**: our evaluated feature file covers a **1,000-user pilot sample** (330,285 user-days), not every r4.2 user, and comes from the Group-B notebook pilot. Its 12 deviation features use a small epsilon guard and are **not clipped** — measured maxima reach **4·10⁷** (`http_zscore_7d`; then `file_zscore_7d` 2.7·10⁶, `email_zscore_7d` 1.4·10⁶) — whereas the pipeline's own `features/builder.py` clips at ±10 (`Z_CLIP`). The z-score comparator therefore benefits from extreme unclipped outliers on CERT — which is exactly why we report it as a comparator instead of only reporting the model.
- **LANL is a subset**: all 104 red-team victim users + a 2.5% sample of normal users (system accounts dropped), cut off 2 days after the last red-team event → 15,065,146 auth rows → **181 labelled user-days**. Positives are **clustered in the early part** of an anonymized 32-day window.
- **LANL time is anonymized and relative only** (seconds since the start of the dataset). All LANL "days" are synthetic (epoch-based) and `n_night` is a *proxy* that depends on an unknown timezone; we added `n_new_hour` (an hour the user has never used before) precisely so at least one time feature is timezone-free.
- **Label scarcity + drift (the biggest limitation).** LANL scores 0.99 PR-AUC on validation and **0.10 on test**. A model cannot be trusted on a 34-positive test window; our LANL result is a negative result, reported on purpose. CERT is much more stable (0.9933 train → 0.9222 test) but still loses ~7 PR-AUC points out of sample.

**Labels and evaluation**
- `label = 1` means "this user-day falls inside an insider's labelled activity range" (CERT r4.2 rows only) or "a red-team credential event happened" (LANL). It is the dataset's ground truth, not proof of malicious intent, and it is only available **offline** — the live system never sees it.
- Detection granularity is **one user-day**. `median_days_to_detection = 0.0` means "flagged on the same day", not "instantaneous"; we make no sub-day real-time claim.
- Alert-budget metrics depend on `K` (5 alerts/day). A different budget changes precision/recall; the full precision-recall picture is in `test_evaluation` and `generalization_audit`, not just the headline table.
- Hyperparameters (positive-class weight, `alpha`, combination method, tier thresholds) are chosen on a **temporal validation slice**, never on test — but that slice is small (CERT: 43,435 user-days / 324 positives; **LANL: 1,918 user-days / 14 positives**). Small validation support means the "supervised wins over the hybrid" conclusion is itself uncertain, especially on LANL.
- When the validation slice contains **no** positives (a real LANL failure mode, since attacks cluster early), the validation window is deliberately **widened backwards** until it holds ≥5 positives, with at least 50% of the period kept for fitting. This is a pragmatic compromise (it uses label availability to define validation) that is documented in `train.split_last`; the test window is never used for any choice.
- **The hybrid is not automatically better.** Validation selected `alpha = 1.0` (supervised only) on both datasets, so the Isolation Forest contributed nothing measurable at that operating point. The unsupervised branch is reported separately (`unsupervised_only`, `zscore_baseline`) rather than being credited.

**Explainability**
- The `shap` library was **not available** in the run behind these numbers, so claims are limited to *Shapley-value explanations (own sampling implementation)*. Any "SHAP" claim requires `explain_method == "shap"` in `outputs/alerts.jsonl` and a green `make shap-check`.
- Explanations are **per-alert cost-bounded**: only the top `explain.max_alerts` (300) alerts get permutation-sampling Shapley; the rest get the cheaper `deviation` explanation. Read the method per row.
- Shapley sampling is **Monte-Carlo**: with `n_samples = 60` the contributions are estimates (the efficiency identity `Σφ + base = f(x)` still holds exactly). `combine_method = rank` cannot be explained per row at all (ranks need a batch); if it ever wins, explanations are computed on the equivalent weighted variant and that is warned about at runtime.

**Privacy and operations**
- Pseudonymization **reduces exposure**; it is not a formal privacy guarantee. HMAC-SHA256 with a per-deployment secret + 16-hex truncation is a practical measure: short hashes are linkable within the dataset and a leaked key defeats the pseudonymization. Raw LANL `auth.txt` and CERT logs never enter the pipeline outputs, but they do exist on the machine that runs the prefilter.
- Time is a quasi-identifier: even with hashed IDs, LANL timestamps are kept (only relatively anonymized), so re-identification from side channels is not fully prevented.
- "Real-time" is a **replay** of historical logs (see `ingest/replay.py`); throughput/latency claims must come from `outputs/benchmark.json`, not from this README.
- Models are `joblib` pickles tied to the machine/architecture that created them — train and serve on the same (LinuxONE/s390x) instance.

## Credits & open-source
pandas, NumPy, scikit-learn, joblib, PyYAML, Flask — *(TODO: add links; add `shap` / `pyarrow` ONLY if they actually ran on the instance)*.
Datasets: CMU CERT Insider Threat Test Dataset; LANL Comprehensive Multi-Source Cyber-Security Events — sources, licences and the exact subset recipe are in `data/README.md`.

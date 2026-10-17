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
make toy                            # CERT-style synthetic data + full pipeline (< 1 min)
make lanl-toy                       # LANL-style synthetic data + LANL pipeline
make shap-check                     # does SHAP / pyarrow actually work on this machine?
make test                           # unit tests
make api                            # dashboard on :8000
make bench                          # latency / throughput
make container                      # build & run in podman/docker
```

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
Two datasets, evaluated separately (different environments): **CMU CERT Insider Threat** (insider misuse) and **LANL** authentication logs with red-team labels (stolen credentials; used as a **filtered subset**: all red-team victim users + a sample of other users). See `data/README.md`.

## Explainability  *(TODO: state which method was actually used — see `explain_method` in `outputs/alerts.jsonl`)*
Risk explanations use SHAP when the `shap` library runs on the LinuxONE instance; otherwise our own Shapley-value sampling implementation (`models/explain.py`) is used and described as such.

## Results  *(TODO — fill from `outputs/metrics.json`; do not report toy-data numbers)*
| Metric (temporal split, alert budget = K/day) | Value |
|---|---|
| Precision @ budget | TODO |
| Recall @ budget | TODO |
| Insiders detected / total | TODO |
| Median days to detection | TODO |

## How it uses IBM Z / LinuxONE  *(TODO — only claims backed by screenshots in `evidence/`)*
- Platform: LinuxONE Community Cloud, `s390x` (screenshot)
- Containerized deployment (screenshot)
- Measured per-event latency / throughput: TODO (`outputs/benchmark.json`)
- Identity data and the pseudonymization key never leave the instance

## Limitations
- Public datasets are synthetic (CERT) / de-identified (LANL) and do not fully represent production networks.
- Pseudonymization **reduces exposure**; it is not a formal privacy guarantee.
- "Real-time" is a **replay** of historical logs.
- *(TODO: add measured limitations)*

## Credits & open-source
pandas, NumPy, scikit-learn, joblib, PyYAML, Flask — *(TODO: add links; add `shap` / `pyarrow` ONLY if they actually ran on the instance)*.
Datasets: CMU CERT Insider Threat Test Dataset; LANL Comprehensive Multi-Source Cyber-Security Events (if used) — see `data/README.md`.

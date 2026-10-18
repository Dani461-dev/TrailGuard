/**
 * Single source of truth for TrailGuard landing content.
 * Compiled from the real `trailguard/` repo + Project Plan v3.1.
 * Model & result numbers are intentionally marked "to be filled by the team" — no real results yet.
 */

export interface Meta {
  name: string;
  subtitle: string;
  event: string;
  eventCode: string;
  theme: string;
  tagline: string;
  goal: string;
  flow: string[];
}

export const meta: Meta = {
  name: "TrailGuard",
  subtitle: "Privacy-Preserving, Explainable Insider-Threat Detection on IBM LinuxONE",
  event: "IBM Z Datathon 2026",
  eventCode: "SSF2026",
  theme: "AI Secured — Innovation Without Exposure",
  tagline:
    "Privacy-preserving, explainable insider-threat detection — running entirely on IBM LinuxONE.",
  goal:
    "Build an insider-threat detection pipeline that runs entirely on LinuxONE, with explainable risk scores, pseudonymized user IDs, and final decisions kept in human hands.",
  flow: [
    "logs",
    "pseudonymize",
    "features",
    "hybrid models",
    "risk + reasons",
    "policy tier",
    "analyst",
  ],
};

export interface PipelineStep {
  id: string;
  cmd: string;
  title: string;
  desc: string;
  output: string;
  icon: string;
}

export const pipelineSteps: PipelineStep[] = [
  {
    id: "ingest",
    cmd: "ingest",
    title: "Ingest & pseudonymize",
    desc: "CERT/LANL loaders ingest multi-source logs; identities are hashed (HMAC-SHA256) right at ingestion.",
    output: "data/interim/events.csv.gz · Contract #1",
    icon: "lock",
  },
  {
    id: "features",
    cmd: "features",
    title: "Daily behavior features",
    desc: "Per user × day aggregation + deviation (z-score) against each user's own 14-day baseline — leakage-free.",
    output: "data/processed/features.csv.gz · Contract #2",
    icon: "chart",
  },
  {
    id: "train",
    cmd: "train",
    title: "Train hybrid models",
    desc: "TEMPORAL split: supervised (HistGradientBoosting) + Isolation Forest for novel behavior.",
    output: "models/bundle.joblib · Contract #4",
    icon: "brain",
  },
  {
    id: "evaluate",
    cmd: "evaluate",
    title: "Alert-budget evaluation",
    desc: "Realistic metrics for rare events: precision/recall @ budget + time-to-detection.",
    output: "outputs/metrics.json · Contract #5",
    icon: "gauge",
  },
  {
    id: "score",
    cmd: "score",
    title: "Score, explain, decide",
    desc: "Risk score 0–1, per-alert explanation (SHAP/Shapley/deviation), then mapped to the 3-tier policy.",
    output: "outputs/alerts.jsonl · Contract #3",
    icon: "alert",
  },
];

export interface ModuleItem {
  title: string;
  path: string;
  desc: string;
  icon: string;
}

export const modules: ModuleItem[] = [
  {
    title: "Pseudonymization",
    path: "ingest/pseudonymize.py",
    desc: "HMAC-SHA256 keyed hash (16 hex). The key lives in `.env` and never leaves the instance.",
    icon: "lock",
  },
  {
    title: "Replay stream",
    path: "ingest/replay.py",
    desc: "Replays logs as an event stream — honestly declared as a replay, not real-time.",
    icon: "play",
  },
  {
    title: "Explanations",
    path: "models/explain.py",
    desc: "shap → shapley (own sampling, exact efficiency) → deviation. The method used is recorded as-is.",
    icon: "explain",
  },
  {
    title: "Policy",
    path: "policy/policy.py",
    desc: "Score → 3 response tiers. The system NEVER blocks accounts automatically.",
    icon: "shield",
  },
  {
    title: "Case summaries",
    path: "llm/summarizer.py",
    desc: "Plain-language template (default). Accepts only pseudonymized fields.",
    icon: "doc",
  },
  {
    title: "API + dashboard",
    path: "api/app.py",
    desc: "Flask :8000 — /health, /api/alerts, /api/metrics, POST /api/score, alert page.",
    icon: "server",
  },
  {
    title: "Container",
    path: "deploy/Dockerfile",
    desc: "python:3.11-slim (fallback ubi9/python-311). Data & keys are mounted, never baked into the image.",
    icon: "box",
  },
  {
    title: "Pipeline CLI",
    path: "src/trailguard/pipeline.py",
    desc: "`python -m trailguard.pipeline all` — ingest → features → train → evaluate → score.",
    icon: "code",
  },
];

export interface DataContract {
  id: string;
  file: string;
  maker: string;
  consumer: string;
  note: string;
}

export const contracts: DataContract[] = [
  {
    id: "#1",
    file: "data/interim/events.csv.gz",
    maker: "ingest (loader + pseudonymize)",
    consumer: "features",
    note: "No real IDs. user & host = keyed-hash, 16 hex.",
  },
  {
    id: "#2",
    file: "data/processed/features.csv.gz",
    maker: "Group B",
    consumer: "model · API · benchmark",
    note: "1 row = 1 user × 1 day; base features + deviations, label 0/1.",
  },
  {
    id: "#3",
    file: "outputs/alerts.jsonl",
    maker: "pipeline (score)",
    consumer: "dashboard",
    note: "risk, reasons, explain_method, tier, requires_human_approval, summary.",
  },
  {
    id: "#4",
    file: "models/bundle.joblib",
    maker: "Group B",
    consumer: "score · explain · API",
    note: "Trained & loaded on the same machine (s390x pickle).",
  },
  {
    id: "#5",
    file: "outputs/metrics.json · benchmark.json",
    maker: "Group B · Group A",
    consumer: "README · video",
    note: "Every published number must be traceable back here.",
  },
];

export interface Principle {
  title: string;
  desc: string;
  icon: string;
}

export const principles: Principle[] = [
  {
    title: "Always a working version",
    desc: "`main` must pass `make toy` at any time. Toy data lets every group work in parallel.",
    icon: "check",
  },
  {
    title: "Data contracts first, code second",
    desc: "Groups communicate only through the agreed Data Contracts (#1–#5).",
    icon: "layers",
  },
  {
    title: "Only claim what actually works",
    desc: "Terms like “SHAP” or “Parquet” are not written until they are proven to run on LinuxONE.",
    icon: "shield",
  },
  {
    title: "Cut scope early",
    desc: "Cut decisions happen at the Gate, not at the end. MoSCoW guides priorities.",
    icon: "scissors",
  },
  {
    title: "Everyone passes Linux survival",
    desc: "Every member (not just Group A) completes the basic Linux & LinuxONE checklist first.",
    icon: "terminal",
  },
];

export interface ScopeLevel {
  level: string;
  tone: "must" | "target" | "should" | "could" | "wont" | "deferred";
  items: string[];
  limit: string;
}

export const scope: ScopeLevel[] = [
  {
    level: "MUST",
    tone: "must",
    items: [
      "Runs on LinuxONE",
      "Pseudonymization",
      "Daily features",
      "Isolation Forest + supervised",
      "Risk score",
      "3-tier policy (human approval)",
      "Simple dashboard",
      "Alert-budget evaluation + time-to-detection",
      "Two datasets: CERT + LANL (subset)",
      "Shapley-value based explanations (own implementation)",
    ],
    limit: "Required to finish",
  },
  {
    level: 'TARGET — the "SHAP" claim',
    tone: "target",
    items: ["Library `shap` runs on s390x", "pyarrow / Parquet"],
    limit: "Go/no-go at Gate 1",
  },
  {
    level: "SHOULD",
    tone: "should",
    items: [
      "Container runs",
      "Latency/throughput benchmark",
      "Baseline comparison in the evaluation",
      "LANL: full evaluation with a comparison baseline",
    ],
    limit: "Gate 2 / Gate 3",
  },
  {
    level: "COULD",
    tone: "could",
    items: [
      "Small LLM for case summaries",
      "Live replay with speed control",
      "Approve/reject buttons in the dashboard",
    ],
    limit: "Gate 3",
  },
  {
    level: "WON'T",
    tone: "wont",
    items: [
      "Full LANL (1 billion rows, ~7 GB gz) on the VM",
      "Deep learning",
      "Multi-user authentication",
    ],
    limit: "Out of scope",
  },
  {
    level: "DEFERRED",
    tone: "deferred",
    items: [
      "Evidence screenshots",
      "Final README",
      "Limitations section",
      "Demo video",
      "Submission",
    ],
    limit: "Split after Gate 3",
  },
];

export interface Decision {
  id: string;
  decision: string;
  reason: string;
}

export const decisions: Decision[] = [
  {
    id: "D1",
    decision: "Flask (not FastAPI/Streamlit)",
    reason: "Pure-Python; avoids pydantic-core/pyarrow, which are risky on s390x.",
  },
  {
    id: "D2",
    decision: "CSV.gz between steps by default; Parquet optional",
    reason: "pyarrow is risky on s390x; the pipeline falls back automatically with a warning.",
  },
  {
    id: "D3",
    decision: "Supervised = HistGradientBoostingClassifier (sklearn); fallback GradientBoostingClassifier",
    reason: "No extra dependencies; light enough for LinuxONE. Older sklearn builds (e.g. s390x apt 0.23) lack HGB — the actual model used is recorded in metrics (sup_model).",
  },
  {
    id: "D4",
    decision: "SHAP is a target claim. Order: shap → shapley → deviation",
    reason: "Claims must match the method that actually ran (explain_method column).",
  },
  {
    id: "D5",
    decision: "LANL stays in scope as a subset (streaming prefilter)",
    reason: "Full data is not viable on the VM; separate pipeline via config_lanl.yaml.",
  },
  {
    id: "D6",
    decision: "TEMPORAL split + alert-budget & time-to-detection metrics",
    reason: "Extremely rare data; avoids future leakage.",
  },
  {
    id: "D7",
    decision: "Replay = stream simulation, honestly declared",
    reason: "A “real-time” claim must be backed by numbers.",
  },
];

export interface FeatureSet {
  dataset: string;
  file: string;
  base: string[];
  zCount: number;
  note: string;
}

export const featureSets: FeatureSet[] = [
  {
    dataset: "CERT (insider misuse)",
    file: "features/builder.py",
    base: [
      "n_logon",
      "n_offhours_logon",
      "n_weekend_logon",
      "n_distinct_host",
      "n_new_host",
      "n_usb_connect",
      "n_file_ops",
      "n_http",
      "n_new_domain",
      "n_email",
      "n_email_ext",
      "email_ext_bytes",
    ],
    zCount: 12,
    note: "12 base features + 12 deviations (14-day baseline z-score per user).",
  },
  {
    dataset: "LANL (stolen credentials)",
    file: "features/builder_lanl.py",
    base: [
      "n_auth",
      "n_fail",
      "n_logon",
      "n_network_logon",
      "n_remote",
      "n_distinct_dst",
      "n_new_dst",
      "n_distinct_src",
      "n_new_src",
      "n_night",
    ],
    zCount: 10,
    note: "10 base features + 10 deviations. `n_night` is only a proxy (LANL timestamps are anonymous).",
  },
];

export interface ModelFact {
  label: string;
  value: string;
  icon: string;
}

export const modelFacts: ModelFact[] = [
  { label: "Split", value: "Temporal (not random) — 65% train / 35% test", icon: "clock" },
  { label: "Supervised", value: "HistGradientBoostingClassifier + class weights (fallback: GradientBoostingClassifier when HGB is unavailable)", icon: "brain" },
  { label: "Anomaly", value: "IsolationForest, trained on normal behavior", icon: "radar" },
  { label: "Score blend", value: "risk = 0.6 · p_supervised + 0.4 · p_anomaly", icon: "merge" },
  { label: "Evaluation", value: "Alert budget 5/day · precision/recall · median days-to-detection", icon: "gauge" },
];

export interface ExplainMethod {
  name: string;
  method: string;
  desc: string;
  tone: "ok" | "warn" | "neutral";
}

export const explainMethods: ExplainMethod[] = [
  {
    name: "SHAP library",
    method: "shap",
    desc: "shap.Explainer + model-agnostic. Requires the shap package (numba/llvmlite) — must be tested on s390x first.",
    tone: "ok",
  },
  {
    name: "Shapley (own implementation)",
    method: "shapley",
    desc: "Permutation sampling, pure NumPy. Exact efficiency holds: Σ contributions + base = f(x).",
    tone: "neutral",
  },
  {
    name: "Deviation",
    method: "deviation",
    desc: "Last resort: how far features deviate from the user's usual behavior (z-score).",
    tone: "warn",
  },
];

export interface ClaimRule {
  claim: string;
  allowed: string;
  forbidden: string;
}

export const claimRules: ClaimRule[] = [
  {
    claim: "Runs on LinuxONE",
    allowed: "uname/lscpu screenshot showing Architecture: s390x",
    forbidden: "Only runs on a laptop",
  },
  {
    claim: '"SHAP"',
    allowed: "explain_method == \"shap\" in alerts + [OK] shap in shap_pyarrow_check.txt",
    forbidden: "explain_method == \"shapley\" → write “Shapley-value explanations (own implementation)”",
  },
  {
    claim: '"Parquet / pyarrow"',
    allowed: "[OK] pyarrow + io.format: parquet actually used",
    forbidden: "pyarrow failed / fell back to CSV.gz",
  },
  {
    claim: '"Two datasets"',
    allowed: "CERT and LANL results from metrics.json / lanl_metrics.json",
    forbidden: "Claiming full LANL (1 billion rows) was processed",
  },
  {
    claim: "Privacy-preserving",
    allowed: "“Reduces exposure through pseudonymization”",
    forbidden: "Claiming formal privacy guarantees / differential privacy",
  },
  {
    claim: '"Near real-time"',
    allowed: "Per-event latency numbers exist + described as a replay",
    forbidden: "Writing “real-time” without measurement",
  },
];

export interface PolicyTier {
  tier: number;
  action: string;
  range: string;
  desc: string;
  human: boolean;
  tone: "t1" | "t2" | "t3";
}

export const policyTiers: PolicyTier[] = [
  {
    tier: 1,
    action: "log_only",
    range: "risk < 0.60",
    desc: "Log only. No automatic action.",
    human: false,
    tone: "t1",
  },
  {
    tier: 2,
    action: "step_up_verification",
    range: "0.60 ≤ risk < 0.85",
    desc: "Request additional verification on the next session.",
    human: false,
    tone: "t2",
  },
  {
    tier: 3,
    action: "analyst_ticket",
    range: "risk ≥ 0.85",
    desc: "Create an analyst ticket; follow-up actions MUST be approved by a human.",
    human: true,
    tone: "t3",
  },
];

export interface SampleAlert {
  user: string;
  day: string;
  risk: number;
  tier: number;
  action: string;
  human: boolean;
  explainMethod: string;
  summary: string;
  reasons: { label: string; detail: string }[];
}

/** Sample alert (Contract #3 shape) for the dashboard preview — not real results. */
export const sampleAlerts: SampleAlert[] = [
  {
    user: "7f3ce1b2c497fb5c",
    day: "2010-03-03",
    risk: 0.92,
    tier: 3,
    action: "analyst_ticket",
    human: true,
    explainMethod: "shap",
    summary:
      "Risk 0.92 (tier 3: analyst_ticket). Requires analyst approval. Main triggers: new web domains, USB usage, off-hours logons.",
    reasons: [
      { label: "new web domain", detail: "value 7 · +0.31" },
      { label: "USB usage", detail: "value 3 · +0.24" },
      { label: "off-hours logon", detail: "value 5 · +0.18" },
    ],
  },
  {
    user: "a91b0d7e6c2f4410",
    day: "2010-03-04",
    risk: 0.71,
    tier: 2,
    action: "step_up_verification",
    human: false,
    explainMethod: "shapley",
    summary:
      "Risk 0.71 (tier 2: step_up_verification). Main triggers: large outbound email volume, a never-seen computer.",
    reasons: [
      { label: "outbound email volume", detail: "value 1.4e6 · +0.33" },
      { label: "never-seen computer", detail: "value 2 · +0.19" },
    ],
  },
  {
    user: "0c48be1fa7d93e55",
    day: "2010-03-05",
    risk: 0.48,
    tier: 1,
    action: "log_only",
    human: false,
    explainMethod: "deviation",
    summary:
      "Risk 0.48 (tier 1: log_only). Deviating from habit: web visits (+2.1 SD), file operations (+1.3 SD).",
    reasons: [
      { label: "web visits", detail: "2.1 SD" },
      { label: "file operations", detail: "1.3 SD" },
    ],
  },
];

export interface Dataset {
  name: string;
  kind: string;
  detail: string;
  points: string[];
  icon: string;
}

export const datasets: Dataset[] = [
  {
    name: "CMU CERT Insider Threat",
    kind: "Primary · synthetic",
    detail: "Multi-source: logon, device, file, http, email (+ LDAP & psychometric).",
    points: [
      "Version r4.2; the answers/ folder marks insiders",
      "Large (http.csv especially) — cap it with max_rows_per_file",
      "Synthetic → does not represent production networks (say so in Limitations)",
    ],
    icon: "database",
  },
  {
    name: "LANL Cyber-Security Events",
    kind: "Secondary · subset",
    detail: "De-identified authentication logs (~58 days) + red-team labels.",
    points: [
      "auth.txt.gz ~1 billion rows / ~7 GB gz — do NOT load it fully",
      "Streaming prefilter: all red-team victim users + a 2% sample of others",
      "Time is anonymous (relative only); very few labels — report as-is",
    ],
    icon: "network",
  },
];

export interface DeployItem {
  title: string;
  desc: string;
  icon: string;
}

export const deploy: DeployItem[] = [
  {
    title: "s390x platform",
    desc: "LinuxONE Community Cloud. Verify with uname/lscpu: Architecture: s390x.",
    icon: "server",
  },
  {
    title: "Container",
    desc: "python:3.11-slim (fallback ubi9/python-311). Data & model are mounted; raw logs & keys never go into the image.",
    icon: "box",
  },
  {
    title: "Static nginx",
    desc: "This landing page builds to static files (dist/) and is served by nginx — a natural fit for a LinuxONE VM.",
    icon: "globe",
  },
  {
    title: "R17 — Node tooling",
    desc: "If npm/build misbehaves on s390x: build on a laptop then copy dist/ to the VM, or serve via Flask.",
    icon: "alert",
  },
];

export interface EvidenceItem {
  id: string;
  title: string;
}

export const evidenceItems: EvidenceItem[] = [
  { id: "01", title: "uname -a + lscpu (Architecture: s390x)" },
  { id: "02", title: "free -h, df -h, nproc (VM resources)" },
  { id: "03", title: "make run finished on the VM (log & timing)" },
  { id: "04", title: "podman/docker ps + curl /health" },
  { id: "05", title: "Dashboard (via tunnel) with alerts & tiers" },
  { id: "06", title: "metrics.json & benchmark.json" },
  { id: "07", title: "top/htop during the benchmark (CPU/memory)" },
  { id: "08", title: "Evidence of pseudonymization + .env not in the repo" },
  { id: "09", title: "shap_pyarrow_check.txt (claim proof / fallback)" },
  { id: "10", title: "LANL subset size & prefilter log" },
];

export interface RoleGroup {
  group: string;
  icon: string;
  roles: { name: string; focus: string }[];
}

export const teamRoles: RoleGroup[] = [
  {
    group: "A — Platform & Deploy",
    icon: "server",
    roles: [
      { name: "A-Platform", focus: "LinuxONE environment: SSH, Python, packages, data on the VM, system evidence" },
      { name: "A-Deploy", focus: "Containers, performance benchmark, Makefile, security evidence" },
    ],
  },
  {
    group: "B — Data & Model",
    icon: "brain",
    roles: [
      { name: "B-Data", focus: "CERT/LANL loaders, feature building, data quality" },
      { name: "B-Model", focus: "Hybrid model, tuning, honest evaluation, alert explanations" },
    ],
  },
  {
    group: "C — Integration & Product",
    icon: "layers",
    roles: [
      { name: "C-Lead (PM)", focus: "Pipeline, pseudonymization, policy, API; keeps Gates & the Decision Log" },
      { name: "C-Demo", focus: "Dashboard, replay, case summaries, README, video & submission" },
    ],
  },
];

export interface Stage {
  tag: string;
  title: string;
  kind: "stage" | "gate" | "checkpoint";
  points: string[];
}

export const stages: Stage[] = [
  {
    tag: "Stage 0",
    title: "Ready",
    kind: "stage",
    points: [
      "A1 SSH + make check (record OS/Python/RAM/disk)",
      "B1 download & understand CERT",
      "C1 repo, .env, HMAC key",
    ],
  },
  {
    tag: "Stage 1",
    title: "Foundation",
    kind: "stage",
    points: [
      "A2 make setup / make toy / make lanl-toy",
      "A3 go/no-go SHAP & pyarrow",
      "C8 start review; read the data contracts",
    ],
  },
  {
    tag: "Gate 1",
    title: "Foundation proven",
    kind: "gate",
    points: [
      "make toy & make lanl-toy succeed on LinuxONE",
      "SHAP & pyarrow decisions recorded",
      "Node/npm (React) tests on the VM recorded",
    ],
  },
  {
    tag: "Stage 2",
    title: "Real data + baseline",
    kind: "stage",
    points: [
      "A5 CERT data to the VM · A11 download+prefilter LANL",
      "B2/B3 real CERT loader & features",
      "C3a main pages (toy data)",
    ],
  },
  {
    tag: "Checkpoint LANL",
    title: "LANL subset ready",
    kind: "checkpoint",
    points: ["data/raw/lanl_sub/ exists & its size is recorded", "B-Data can use it"],
  },
  {
    tag: "Gate 2",
    title: "End-to-end",
    kind: "gate",
    points: [
      "CERT (sample) end-to-end → alerts visible in the dashboard",
      "LANL pipeline end-to-end on the subset",
    ],
  },
  {
    tag: "Stage 3",
    title: "Polish & wire up",
    kind: "stage",
    points: [
      "Container, benchmark, evaluation + comparison",
      "Final policy, case summaries, approve/reject",
    ],
  },
  {
    tag: "Gate 3",
    title: "FEATURE FREEZE",
    kind: "gate",
    points: [
      "After this only bug fixes + deferred work",
      "Evidence, documentation, video split (§8)",
    ],
  },
];

export interface Risk {
  id: string;
  risk: string;
  impact: string;
  mitigation: string;
  owner: string;
}

export const risks: Risk[] = [
  { id: "R1", risk: "ML packages fail to install on s390x (big-endian, no wheels)", impact: "High", mitigation: "Core stays light (sklearn/pandas/flask). Fallback: HistGradientBoosting, own Shapley / deviation", owner: "A" },
  { id: "R2", risk: "Scope too large", impact: "High", mitigation: "MoSCoW; the Gate decides cuts", owner: "PM" },
  { id: "R3", risk: "VM limits (RAM/CPU/disk) vs large data", impact: "Medium", mitigation: "CERT sampling; max_rows_per_file; check free -h", owner: "A+B" },
  { id: "R4", risk: "SSH drops, processes die", impact: "Medium", mitigation: "Always run inside tmux", owner: "A" },
  { id: "R5", risk: "Real CERT label/file format differs from toy", impact: "Medium", mitigation: "B adapts loader.py at Stage 2", owner: "B" },
  { id: "R6", risk: "Not enough LinuxONE evidence later", impact: "Medium", mitigation: "Periodic make evidence as archive; screenshot split waits for §8", owner: "A-Deploy" },
  { id: "R7", risk: "Overclaiming (real-time, SHAP, formal privacy)", impact: "Medium", mitigation: "Claim rules §3b; dashboard shows explain_method as-is", owner: "C" },
  { id: "R8", risk: "Last-minute integration bugs", impact: "High", mitigation: "Feature freeze at Gate 3; main always green", owner: "PM" },
  { id: "R9", risk: "Keys/tokens leak to GitHub", impact: "High", mitigation: ".gitignore, .env never committed, check before push", owner: "C-Lead" },
  { id: "R10", risk: "Originality rule violations", impact: "Fatal", mitigation: "See the Integrity section in 04_SUBMISSION_CHECKLIST.md", owner: "Everyone" },
  { id: "R11", risk: "LANL ~7 GB / 1B rows: disk/RAM/time not enough", impact: "High", mitigation: "Streaming prefilter; measure --max-lines; check df -h; Checkpoint LANL", owner: "A-Deploy + B-Data" },
  { id: "R12", risk: "shap/numba/llvmlite cannot be installed → SHAP claim fails", impact: "Medium", mitigation: "Go/no-go at Gate 1; fallback own Shapley; claim follows explain_method", owner: "A-Platform + B-Model" },
  { id: "R13", risk: "LANL: few red-team labels & anonymous time → unstable metrics", impact: "Medium", mitigation: "Report positive counts as-is + intervals; do not round away", owner: "B-Model" },
  { id: "R14", risk: "api/templates/ conflict", impact: "—", mitigation: "No longer applicable — the whole dashboard is owned by C-Demo", owner: "—" },
  { id: "R17", risk: "Node/npm or esbuild/rollup problems on s390x, or registry unreachable", impact: "Medium", mitigation: "Test npm install && npm run build at A3b; fallback: build on a laptop, copy dist to the VM", owner: "A-Platform + C-Demo" },
  { id: "R15", risk: "PM is an AI: does not monitor Discord/Git/VM by itself", impact: "Medium", mitigation: "Standard stand-up relay per Gate (format §8); Decision Log as memory", owner: "C-Lead" },
  { id: "R16", risk: "Unbalanced workload / misestimates", impact: "Medium", mitigation: "Re-check at Gate 1; move tasks via PM & record in the Decision Log", owner: "PM" },
];

export const dod: string[] = [
  "make toy and make lanl-toy run on LinuxONE",
  "CERT (sample) & LANL subset pipelines run end-to-end on LinuxONE",
  "make ui builds the React dashboard on the VM",
  "Dashboard shows alerts + reasons + tier + approval status; the demo page shows the replay",
  "outputs/metrics.json, lanl_metrics.json & benchmark.json contain real numbers from LinuxONE",
  "docs/06_ARSITEKTUR_KEAMANAN.md completed",
  "main is green (make toy + make lanl-toy pass)",
];

export const deferred: string[] = [
  "LinuxONE evidence screenshots and the make evidence archive",
  "“Limitations” section (synthetic data, LANL subset & anonymization, label scarcity, leakage risk)",
  "Final claim review (match against explain_method & shap_pyarrow_check.txt)",
  "Final README",
  "Demo video",
  "Submission & dry-run (04_SUBMISSION_CHECKLIST.md)",
];

export const stack: string[] = [
  "pandas",
  "NumPy",
  "scikit-learn",
  "joblib",
  "PyYAML",
  "Flask",
  "pytest",
];

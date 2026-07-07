# Reproducibility Guide

What is currently reproducible in-repo, what needs external resources (an Anthropic API key with
credit, a machine capable of local LoRA fine-tuning), and which artifacts should or should not be
treated as final paper evidence.

## Evidence Types

| Evidence type | Status | Where it lives | Cite as final paper evidence? |
| --- | --- | --- | --- |
| Experiment 1 (schema parsing) | Measured, no external deps | `scripts/run_experiment1.py` | Yes, at this pilot's 3-API scale |
| Experiment 2 (intent generation) | Measured, needs `ANTHROPIC_API_KEY` | `scripts/run_experiment2.py` | Yes, pilot scale (15 endpoints/API) |
| Experiment 3 (trajectory generation) | Measured, needs API key + Exp 2 output | `scripts/run_experiment3.py` | Yes, with the self-consistency caveat in `RESULTS.md` |
| Experiment 4 (schema verification) | Measured, no external deps, needs Exp 3 output | `scripts/run_experiment4.py` | Yes — the strongest result in the repo |
| Experiment 5 (downstream fine-tuning) | Measured, needs API key + local torch/transformers/peft | `scripts/run_experiment5.py` | Yes, for the substitute model (Qwen2.5-0.5B) explicitly, not yet for the paper's 7–8B target |
| Ablation A1/A3/A4 | Measured, needs API key | `scripts/run_ablation_study.py` | Yes, with A3/A4's "inconclusive" framing preserved |
| Ablation A2 | Measured, reuses Experiment 4's data, no re-run needed | (no script — see `RESULTS.md`) | Yes |
| Knowledge Graph / Planner / Response Schema ablations | **Not run — components don't exist** | n/a | No — see `DESIGN_DOC.md` §8.1 for why these were dropped rather than faked |

The most important boundary: every script above produces **real measured numbers from a real
model call or real code path**, never a projected or illustrative number. Where a result is
pilot-scale (3–4 APIs, tens of examples), that is stated explicitly in `RESULTS.md`, not implied
to be larger.

## Environment

```bash
python3 -m venv .venv
./.venv/bin/pip install -e ".[dev]"
```

CI (`.github/workflows/ci.yml`) runs the API-independent test suite (`tests/`, 16 tests) on
Python 3.10/3.11/3.12 on every push/PR to `main`. It does **not** run the experiment scripts,
since those need a funded `ANTHROPIC_API_KEY` that isn't configured as a repo secret.

## External Requirements

- **Experiments 2, 3, 5, and the ablation study (A1/A3/A4)** need `ANTHROPIC_API_KEY` set (env var
  or `.env` file at the repo root — already gitignored) on an account with available credit. A
  billing/credit error (`anthropic.BadRequestError: ... credit balance is too low`) means the key
  is valid but the account has no funds — this is a console.anthropic.com billing fix, not a code
  bug.
- **Experiment 5** additionally needs `torch`, `transformers`, `peft`, `accelerate` installed
  (`./.venv/bin/pip install torch transformers peft accelerate`) and downloads
  Qwen2.5-0.5B-Instruct (~1GB) on first run. No GPU is required — it runs on Apple Silicon's MPS
  backend or CPU; a real GPU would only be needed for the paper's eventual 7–8B target model, which
  this repo does not yet attempt (see `DESIGN_DOC.md` §6.7 for the hardware-scoping rationale).
- **Figures** (`scripts/make_figures.py`) need `matplotlib` and read only committed
  `data/generated/*.json` — no API key, no re-running experiments.

## Fastest Reproduction Paths

### 1. Sanity check (no API key, ~1 second)

```bash
./.venv/bin/python -m pytest tests/ -v
```

### 2. Schema parsing + verification (no API key, ~1 second)

```bash
./.venv/bin/python scripts/run_experiment1.py
./.venv/bin/python scripts/run_experiment4.py   # needs experiment3_trajectories.json, already committed
```

### 3. Full pipeline from scratch (needs a funded API key, several minutes)

```bash
set -a && source .env && set +a
./.venv/bin/python scripts/run_experiment2.py
./.venv/bin/python scripts/run_experiment3.py
./.venv/bin/python scripts/run_experiment4.py
./.venv/bin/python scripts/prepare_experiment5_data.py
./.venv/bin/python scripts/run_experiment5.py
./.venv/bin/python scripts/run_ablation_study.py
```

### 4. Regenerate figures only (no API key)

```bash
./.venv/bin/python scripts/make_figures.py
```

## Known Non-Determinism

- Experiments 2/3/5 and the ablation study call Claude Sonnet 5 without a fixed seed — exact
  wording of generated intents/trajectories will differ between runs, though aggregate metrics
  (coverage, tool-selection accuracy) have been stable within a few percentage points across the
  repeated runs performed during development (see `RESULTS.md`'s note on Slack's 93.3–100% range
  in Experiment 3).
- Endpoint/distractor **sampling** is seeded (`SEED = 42` in each script) and is fully
  deterministic given the same spec file.

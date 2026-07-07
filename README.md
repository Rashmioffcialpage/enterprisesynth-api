# EnterpriseSynth: A Schema-Aware Agentic Framework for Generating Verified SFT and Evaluation Datasets from OpenAPI Specifications

**Status:** pilot-scale experiments complete (Experiments 1–5 + Ablation Study A1–A4). See
`DESIGN_DOC.md` for the full design, results, and honest accounting of what is/isn't implemented.

## Pitch

A framework that ingests an OpenAPI/Swagger spec and emits verified SFT traces
AND eval records with intent specs — without executing the live API. Targets
the enterprise cold-start problem: teams that have an API schema but no
existing tool-use training data or eval suite for it.

**What's actually implemented** (four stages, not the aspirational seven — see
`DESIGN_DOC.md` §4 and §8): API Schema Parser → Intent Synthesis Agent → Trajectory Generator
→ Schema Verification Engine.

## Target venues

- MLinPL 2026 — deadline Aug 1, 2026
- AAAI 2027 Workshop on Enterprise AI Evaluation — deadline Jul 28, 2026

## Eval suite naming (resolved)

The evaluation dataset EnterpriseSynth jointly emits is called **EnterpriseSynth-Eval**. An
earlier draft informally called it "EnterpriseBench," which collided with an unrelated
live-sandbox benchmark (arXiv:2510.27287, Vishwakarma et al., Oct 2025) — renamed to avoid
confusion. See `DESIGN_DOC.md`'s top-of-file note for the full history.

## Repository layout

- `DESIGN_DOC.md` — full design, literature review, methodology, all measured results
- `paper/` — LaTeX draft (`main.tex`), bibliography, figures, related-work audit
- `src/enterprisesynth/` — parser, intent agent, trajectory agent, verifier, ablation agents
- `scripts/` — one script per experiment/ablation, plus figure generation
- `data/specs/` — committed real OpenAPI specs (GitHub, Stripe, Slack, Zoom)
- `data/generated/` — committed experiment outputs (JSON)
- `tests/` — pytest suite (16 tests)

## Setup

```bash
python3 -m venv .venv
./.venv/bin/pip install -e ".[dev]"
```

Requires `ANTHROPIC_API_KEY` in your environment (or a `.env` file at the repo root — already
gitignored) for Experiments 2, 3, 5 and the ablation study, which call Claude Sonnet 5. Experiments
1 and 4 are pure code, no API key needed.

## Reproduce Results

Run in order — later scripts depend on earlier ones' output:

```bash
# 0. Run the test suite (no API key needed)
./.venv/bin/python -m pytest tests/ -v

# 1. Schema parsing accuracy (no API key needed)
./.venv/bin/python scripts/run_experiment1.py

# 2. Intent generation (needs ANTHROPIC_API_KEY)
./.venv/bin/python scripts/run_experiment2.py

# 3. Trajectory generation (needs ANTHROPIC_API_KEY; depends on Experiment 2's output)
./.venv/bin/python scripts/run_experiment3.py

# 4. Schema verification + corruption testing (no API key needed; depends on Experiment 3's output)
./.venv/bin/python scripts/run_experiment4.py

# 5. Downstream fine-tuning pilot (needs ANTHROPIC_API_KEY + torch/transformers/peft;
#    depends on Experiments 2-3's output; downloads Qwen2.5-0.5B-Instruct, ~1GB)
./.venv/bin/pip install torch transformers peft accelerate
./.venv/bin/python scripts/prepare_experiment5_data.py
./.venv/bin/python scripts/run_experiment5.py

# Ablation study A1/A3/A4 (needs ANTHROPIC_API_KEY; A2 reuses Experiment 4's data, no re-run needed)
./.venv/bin/python scripts/run_ablation_study.py

# Regenerate all figures from committed data/generated/*.json (no re-run of experiments needed)
./.venv/bin/pip install matplotlib
./.venv/bin/python scripts/make_figures.py
```

## Status log

- 2026-07-06: Repo created; literature review (Self-Instruct, WizardLM, AgentInstruct, API-Bank,
  ToolLLM/ToolBench); dataset selection (APIs.guru); Experiments 1–5 implemented and run at pilot
  scale; Ablation Study A1–A4 run against the actual four-stage implementation.

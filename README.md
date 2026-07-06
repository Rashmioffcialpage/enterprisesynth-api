# EnterpriseSynth: Agentic SFT + Eval Data from API Schemas Without Live Execution

**Status:** early setup — literature review in progress.

## Pitch

A framework that ingests an OpenAPI/Swagger spec and emits verified SFT traces
AND eval records with intent specs — without executing the live API. Targets
the enterprise cold-start problem: teams that have an API schema but no
existing tool-use training data or eval suite for it.

## Target venues

- MLinPL 2026 — deadline Aug 1, 2026
- AAAI 2027 Workshop on Enterprise AI Evaluation — deadline Jul 28, 2026
- Ideally submitted jointly with a companion "EnterpriseBench" project as one
  flagship submission.

## Repository layout (planned)

- `paper/` — literature review, design doc, draft
- `src/` — schema ingestion, trace generation, verification, eval emission
- `data/` — source OpenAPI/Swagger specs and generated traces
- `tests/`

## Status log

- 2026-07-06: Repo created. Literature review underway to select a base paper
  and source dataset(s).

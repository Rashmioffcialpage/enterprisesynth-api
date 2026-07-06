# EnterpriseSynth — Research Design Document

**Topic (T1b):** Agentic SFT + Eval Data from API Schemas Without Live Execution
**Author:** Rashmi Thimmaraju
**Target venues:** MLinPL 2026 (deadline Aug 1, 2026) · AAAI 2027 Workshop on Enterprise AI Evaluation (deadline Jul 28, 2026)

---

## ⚠ Open naming/positioning issue — resolve before drafting further

The paper draft names its evaluation suite **"EnterpriseBench."** That name is already taken:
**arXiv:2510.27287, "Can LLMs Help You at Work? A Sandbox for Evaluating LLM Agents in
Enterprise Environments" (Oct 2025)** ships a benchmark under the identical name (500 tasks,
SWE/HR/finance/admin, simulated enterprise sandbox with live task execution). Reviewers at the
AAAI Enterprise AI Evaluation workshop will very likely know this paper.

Two options, not mutually exclusive:

1. **Rename** our eval suite — candidates: `SpecEvalBench`, `EnterpriseColdBench`, `APISpecBench`.
2. **Reframe as complementary** and cite it directly: "Vishwakarma et al.'s EnterpriseBench
   (arXiv:2510.27287) evaluates agents against a simulated *live* enterprise sandbox; our benchmark
   evaluates whether spec-only-generated, intent-labeled eval records correlate with performance on
   such a sandbox, without requiring the sandbox to exist yet." This is a legitimate
   differentiation, but the name still needs to change to avoid being read as a duplicate
   submission.

Decision needed before Section 4 of the paper is finalized.

---

## 1. Goal

Solve the enterprise cold-start problem for tool-using LLM agents: an organization has an
OpenAPI/Swagger spec for its internal or partner APIs but no historical traffic logs, no safe
sandbox, and no existing SFT or eval data for that API surface. EnterpriseSynth ingests the spec
alone and emits (a) verified multi-turn SFT traces and (b) paired evaluation records, each tied to
a formal **intent spec**, without ever executing a live call against the target system.

### Research Questions

- **RQ1 (feasibility):** Can structurally valid, verifiable multi-step agent traces be synthesized
  from an OpenAPI spec alone — no execution, no historical request/response data?
- **RQ2 (verification):** Does a static constraint validator (schema/type/format checking, no
  runtime calls) catch the same class of errors that execution-based verification (e.g., APIGen)
  catches, and where does it fall short?
- **RQ3 (utility):** Does fine-tuning a compact open model on EnterpriseSynth-generated traces
  measurably improve API sequencing accuracy and constraint compliance versus the untuned baseline?
- **RQ4 (cold-start generalization):** Given a spec the base model has plausibly never seen paired
  training data for, how well do zero-execution-generated SFT+eval pairs transfer — i.e., does this
  actually work for a *new* organization's API on day one, not just on well-known public APIs that
  may already be in pretraining data?

---

## 2. The Execution Paradox (problem framing)

Current synthetic tool-use / instruction-data generation splits into two camps, neither of which
fits the enterprise cold-start setting:

- **Execution-based** (API-Bank, ToolLLM/ToolBench): ground and verify traces against real APIs —
  API-Bank uses reproducibility-constrained real databases, ToolBench makes ~470k live RapidAPI
  calls during DFSDT annotation. Fails behind the enterprise firewall — no sandbox exists for most
  internal systems, live calls against production risk data corruption/security violations, and
  network-bound generation is rate-limited.
- **Execution-free but ungrounded** (AgentInstruct): generates tool-use data without executing
  anything, but when seeded from raw code it **hallucinates the API surface** — synthesizing an API
  description from a code snippet, or having the LLM hypothesize additional APIs it believes exist,
  with no ground-truth check. Verification is a soft editorial refinement loop plus a post-hoc,
  held-out GPT-4-judged benchmark (Orca-Bench) — not a per-sample structural gate.
- **General-purpose, non-tool bootstrapping** (Self-Instruct, Evol-Instruct/WizardLM): both are
  execution-free and filtered (ROUGE-similarity/keyword heuristics; "elimination evolving" rules),
  but neither has any notion of tools, APIs, or structural grounding at all.

EnterpriseSynth targets the gap: **a real spec is the only required input** (removing
AgentInstruct's hallucination failure mode), verification is a **hard structural gate** derived
from that spec (not a heuristic text filter or a post-hoc judge), and no execution, sandbox, or
historical traffic is ever required.

---

## 3. Related Work

Literature review scope is exactly five papers (full-text read, not abstract-only — see
`paper/related_work_audit.md` for the complete per-paper breakdown):

| Paper | Execution? | Relevant mechanism | Gap vs. EnterpriseSynth |
| --- | --- | --- | --- |
| Self-Instruct (Wang et al., 2022, [2212.10560](https://arxiv.org/abs/2212.10560)) | None | Bootstrap from 175 seeds; ROUGE-L/keyword/format filtering | No tool/API notion; filtering is text-heuristic, not structural |
| Evol-Instruct / WizardLM (Xu et al., 2023, [2304.12244](https://arxiv.org/abs/2304.12244)) | None | In-depth/in-breadth instruction evolution; "elimination evolving" quality filter | No tool/API handling anywhere in the method |
| AgentInstruct (Mitra et al., 2024, [2407.03502](https://arxiv.org/abs/2407.03502)) | None (LLM-simulated tool responses) | Three-flow agentic pipeline (content transform → taxonomy-driven seed gen → Suggester-Editor refinement) | Hallucinates API surface when seeded from code; verification is soft/post-hoc (Orca-Bench GPT-4 judge), not a per-sample structural gate; no paired eval artifact |
| API-Bank (Li et al., 2023, [2304.08244](https://arxiv.org/abs/2304.08244)) | Real (reproducibility-constrained DBs) | 5-agent pipeline generates 1,888 training dialogues (98% cheaper than human annotation) | Still execution-dependent; hard-codes live-data snapshots for reproducibility |
| ToolLLM / ToolBench (Qin et al., 2023, [2307.16789](https://arxiv.org/abs/2307.16789)) | **Real** — ~470k live RapidAPI calls during DFSDT annotation | DFSDT search grounded in real API responses; ToolEval pass-rate/win-rate judging | Requires a live backend at generation time; not schema-only |

**Base paper: AgentInstruct.** It is the only one of the five that is both agentic/multi-flow and
execution-free for tool-use data — the closest architectural skeleton to adapt. We fix its two
concrete gaps: (1) replace hallucinated/code-derived API seeding with ingestion of a real
OpenAPI/Swagger spec, so nothing needs to be hypothesized; (2) replace its soft, post-hoc
verification (Suggester-Editor judgment + held-out GPT-4 scoring) with a hard, per-sample Static
Constraint Validator checked against the spec itself; (3) jointly emit an intent-spec-tied eval
record from the same generation pass, which none of the five papers do (Orca-Bench, API-Bank's
human-annotated set, and ToolEval are all separate from — not mechanically derived from — the
training-data generation act). API-Bank and ToolBench remain the primary execution-dependent
contrast cases for the Execution Paradox argument.

Full per-paper breakdown is in `paper/related_work_audit.md`.

---

## 4. Methodology — Three Pillars

1. **Structural Graph Extractor** — parses OpenAPI/Swagger specs into a directed relational graph
   $\mathcal{G} = (\mathcal{V}, \mathcal{E})$: endpoints as nodes, parameter/response-to-parameter
   dependencies as edges. Unlike AgentInstruct's tool-use flow, which must synthesize or
   hypothesize an API description when seeded from code, this graph is built directly from the
   real spec — there is nothing to hallucinate.
2. **Deterministic Intent Engine** — the schema-grounded analog of AgentInstruct's taxonomy-driven
   seed generation and Evol-Instruct's "complicate input" evolution step: traverses graph edges to
   define multi-turn intents (e.g., a parent endpoint's response token mapped into a child
   endpoint's parameter slot), generating the paired natural-language instruction + reasoning
   trace + intent spec, with task complexity derived from real dependency depth rather than a
   heuristic evolution rule.
3. **Static Constraint Validator** — a compiler-style firewall: checks generated tool calls against
   the spec's declared parameter types/required fields/response schema, entirely offline (no
   execution). Where Self-Instruct and Evol-Instruct filter with text heuristics (ROUGE similarity,
   keyword rules, degeneracy checks) and AgentInstruct verifies only via soft editorial refinement
   plus a post-hoc held-out judge, this is a hard, per-sample structural gate tied to the intent
   spec object.

---

## 5. Dataset Plan

- **Primary source:** [APIs.guru](https://apis.guru/) / `openapi-directory` — thousands of
  structured OpenAPI 2.0/3.x specs, good diversity, tractable per-spec licensing.
- **Baseline comparison:** held-out slice of ToolBench's RapidAPI pool (16,464 APIs), to benchmark
  against ToolLLM/ToolACE-style methods on a known corpus.
- **Cold-start validation set:** a small, hand-authored set of synthetic "enterprise-internal" specs
  (CRM, ticketing, HRIS, internal billing) modeled on real enterprise API shapes. Required because
  public specs may already be in pretraining data — using only public specs would undermine the
  cold-start claim.
- **Scale target (Phase 1):** ingest production-tier nested public schemas (Kubernetes, Stripe) plus
  the synthetic enterprise set; generate 5,000 SFT rows (`train_sft_pool.jsonl`, multi-turn
  conversation format) + 1,000 eval records (`eval_records_spec.jsonl`).

---

## 6. Training & Evaluation Plan

- **Fine-tuning:** LoRA adapter on an open base model (Mistral-7B-Instruct-v0.3 or
  Llama-3-8B-Instruct), 3 epochs, Paged AdamW, base LR 3e-4, cosine annealing schedule.
- **Metrics:**
  - **Valid JSON Generation Rate (VJGR)** — syntax/positioning-token error reduction.
  - **API Sequence Match Rate (SMR)** — dependent child endpoints only called after correct parent
    parameter initialization.
- **Protocol:** run untuned baseline and fine-tuned model against the 1,000 held-out eval records,
  score both through the Static Constraint Validator.

---

## 7. Timeline

| Date | Milestone |
| --- | --- |
| Jul 21, 2026 | AAAI abstract enrollment |
| Jul 28, 2026 | AAAI 2027 full paper (7 pages) |
| Aug 1, 2026 | MLinPL 2026 submission, adapted to systems/compiler-centric narrative |

---

## 8. Open Items

- Resolve the EnterpriseBench naming collision (see flag at top).
- Verify per-spec licensing before redistributing any derived dataset built on APIs.guru/ToolBench
  sources.
- Confirm In-N-Out's released graph data isn't reusable outright for the Structural Graph Extractor
  before building a parser from scratch.

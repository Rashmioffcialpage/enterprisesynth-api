# Related Work Audit

Literature review scope, as directed: exactly five papers. This is the full reading, not a
survey — each entry below reflects the actual method sections (fetched full-text), not just
abstracts.

## 1. Self-Instruct (Wang et al., 2022, [arXiv:2212.10560](https://arxiv.org/abs/2212.10560))

Bootstraps instruction-tuning data from a model's own generations. Pipeline:

1. Start from 175 human-written seed tasks.
2. Each iteration samples 8 task instructions (6 human-written + 2 previously generated) as
   in-context examples; the model generates new instructions.
3. Classify each instruction as classification vs. non-classification task (few-shot, 12+19 seed
   examples) — this routing matters because generation strategy differs per type.
4. Generate instances: **input-first** (write input, then output) for non-classification tasks;
   **output-first** (pick a label, then condition input generation on it) for classification
   tasks — avoiding label-imbalance bias that input-first produces on classification data.
5. Filter: ROUGE-L similarity to existing instructions must be < 0.7 (dedup), keyword blocklist
   (e.g. reject anything mentioning images — the model can't process them), instance-level
   dedup, and format/degeneracy heuristics (length, repetitiveness).

No execution of anything. No tool/API notion at all — general-purpose instruction diversity.
Filtering is entirely text-heuristic (similarity + keyword rules), not structural/schema-based.

**Relevance to EnterpriseSynth:** the ur-method for "bootstrap synthetic SFT data, filter with
cheap heuristics." EnterpriseSynth's Static Constraint Validator is the schema-grounded analog of
this filtering step — replacing ROUGE-similarity/keyword rules with structural correctness checks
against a real API definition.

## 2. Evol-Instruct / WizardLM (Xu et al., 2023, [arXiv:2304.12244](https://arxiv.org/abs/2304.12244))

Takes existing instructions and evolves them into harder ones, rather than generating from
scratch:

- **In-depth evolving** (5 operations): add constraints, deepen the inquiry, concretize general
  concepts, increase reasoning steps, complicate the input format (inject XML/JSON/SQL, etc.).
  Each evolution step adds only ~10–20 words to keep difficulty progression controlled.
- **In-breadth evolving:** generate a "brand new" instruction inspired by an existing one, same
  domain but rarer topic — diversity injection.
- **Elimination evolving** (quality filter): reject an evolution if (a) it produced no
  information gain vs. the original, (b) the response contains "sorry" and is under 80 words
  (model struggled), (c) the response is only punctuation/stopwords, or (d) the evolved
  instruction leaks template scaffolding (e.g. copies "#Rewritten Prompt#" literally).
- Response generation: same LLM answers its own evolved instruction directly.

No execution, no tool/API-specific handling anywhere in the method — confirmed by full-text read,
not just the abstract.

**Relevance to EnterpriseSynth:** a second execution-free, heuristic-filtered synthesis method,
but with zero structural grounding to any schema. Useful precedent for the idea that *increasing
task complexity along controlled axes* (here: complicating input format) is itself a viable
lever — EnterpriseSynth's Deterministic Intent Engine effectively replaces "complicate input"
with "traverse the real dependency graph one hop deeper," making the complexity axis
schema-derived rather than heuristic.

## 3. AgentInstruct (Mitra et al., 2024, [arXiv:2407.03502](https://arxiv.org/abs/2407.03502))

An agentic, three-flow pipeline that produced the 25M-pair dataset behind Orca-3
(Mistral-7B-based):

1. **Content Transformation Flow:** converts raw, unstructured seed material (documents, code
   files) into an intermediate representation suited to instruction generation. For reading
   comprehension, one of several specialized transformation agents (Argument Passage Generator,
   Debate Passage Generator, Conversation Generator, ...) reshapes a seed article.
2. **Seed Instruction Generation Flow:** taxonomy-driven agents generate diverse instruction
   instances from the transformed content — e.g. 43 predefined reading-comprehension question
   types, 18 text-modification task types. Diversity comes from taxonomy coverage, not random
   sampling.
3. **Instruction Refinement Flow:** Suggester-Editor agent pairs iteratively increase complexity
   and diversity. The Suggester proposes a way to make the instruction harder/trickier; the
   Editor executes that change while preserving validity.

**Tool-use skill, specifically (the closest analog to EnterpriseSynth):** seeded from either a
code snippet or an API description. **If only code is given, a transformation agent synthesizes
an API description from it** — and separately, an "API retrieval agent" or the LLM itself
**hypothesizes additional APIs it believes exist in the library**, without any ground-truth check.
Seed instructions cover single-API, multi-API/sequenced, "impossible task" (missing API), and
missing-required-parameter cases. Tool responses in the generated traces are **LLM-simulated
JSON, never executed** — e.g. a `Create Meal Plan(...)` call is followed by a fabricated
`status: success` response the model invents.

**Verification:** no per-sample structural filter. Quality assurance is (a) the Suggester-Editor
refinement loop itself, which is a soft editorial check, not a hard filter, and (b) a **held-out,
post-hoc benchmark** — Orca-Bench, 1,700 samples (100/skill), scored 0–10 by a GPT-4 judge — used
to evaluate the resulting dataset/model, not to gate individual generated samples before they
enter the training set. The paper explicitly acknowledges: *"Synthetic data may not perfectly
replicate the complexity and nuances of real-world data... additional work is needed to better
assess the quality of the data."*

**Relevance to EnterpriseSynth — closest architectural base paper:** AgentInstruct is the only one
of the five that is (a) agentic/multi-flow and (b) execution-free for tool-use data. Its two
concrete weaknesses relative to what EnterpriseSynth targets:
- It **hallucinates the API surface** when seeded from code (invents plausible APIs with no
  ground truth) — a real API spec removes this failure mode entirely, since the schema *is* the
  ground truth, nothing needs to be hypothesized.
- Verification is **soft and post-hoc** (editorial refinement + held-out GPT-4 scoring), not a
  **hard, per-sample structural gate** against declared parameter types/required fields/response
  schema.
- It produces no paired, mechanically-derived eval artifact — Orca-Bench is a generic
  quality-scoring set, not something tied to the same intent spec that generated each SFT trace.

## 4. API-Bank (Li et al., 2023, [arXiv:2304.08244](https://arxiv.org/abs/2304.08244))

- **API Pool:** 73 implemented APIs for evaluation, 2,138 APIs (1,000 domains) for training.
- **Execution model:** real, but reproducibility-constrained. The team stood up actual databases
  ("we establish the requisite databases and initialize them with initial entries") for
  stateful operations; for APIs pulling external/live data, results are **hard-coded from a
  specific query time** to keep the benchmark reproducible. So responses are genuinely executed
  against real (or realistic, seeded) backends, not LLM-simulated — but frozen at a point in time
  rather than live.
- **Training data (1,888 dialogues, 4,149 API calls):** synthesized by a **5-agent automated
  pipeline** ("Multi-agent" method) that steps through domain → API → query → API-response
  generation. Reported **98% cost reduction vs. human annotation**, **94% available rate** after
  filtering.
- **Eval data (314 dialogues, 753 API calls):** human-annotated, 4 reviewers per instance.
- **Correctness verification:** predicted API call compared against the annotated gold call for
  equivalence (same query/modification performed, same returned result); free-text response
  quality scored via ROUGE-L.

**Relevance to EnterpriseSynth:** API-Bank's own training-data-generation pipeline is itself a
close precedent for "a multi-agent system can synthesize usable tool-dialogue training data far
cheaper than human annotation" (98% cheaper, 94% valid) — evidence supporting EnterpriseSynth's
cost/scale argument. But its execution model (real DBs, hard-coded live-data snapshots) is still
execution-dependent — exactly the sandbox/backend requirement that doesn't exist for most
internal enterprise APIs, and the "hard-code query-time results for reproducibility" workaround is
itself evidence of how much friction real execution introduces even in a research setting.

## 5. ToolLLM / ToolBench (Qin et al., 2023, [arXiv:2307.16789](https://arxiv.org/abs/2307.16789))

- **API collection:** 16,464 real RESTful APIs, 49 categories, scraped from RapidAPI Hub.
- **Instruction generation:** sample APIs, prompt ChatGPT (guided by 12/36 human-written seed
  examples for single-/multi-tool settings) to produce instructions plus the relevant API subset.
  Three categories: single-tool (I1), intra-category multi-tool (I2), intra-collection multi-tool
  (I3, exploiting RapidAPI's own category hierarchy for functional relatedness).
- **DFSDT solution-path annotation:** ChatGPT proposes an action (API + parameters); **the system
  actually calls the real API** and feeds the genuine response back into context; the model can
  expand further or call "Finish by Giving Up"; exploration uses pre-order traversal (not
  exhaustive) to control API-call cost; long responses are compressed (ChatGPT strips
  unimportant fields) to manage context length. Confirmed **real execution**: 469,585 actual API
  calls were made during data annotation.
- **ToolEval:** automatic evaluator; Pass Rate (pass/fail/unsure, majority vote over ≥4 ChatGPT
  predictions) and Win Rate (6 criteria: completeness, factual accuracy, reasoning quality,
  milestones reached, API-exploration breadth, redundancy) — validated at 87.1%/80.3% agreement
  with human judges.

**Relevance to EnterpriseSynth:** the sharpest execution-dependent contrast case. Every solution
path in the training data is grounded by a real, live API call — this is precisely the dependency
that collapses behind an enterprise firewall (no sandbox, security/PII exposure, rate limits).
ToolEval's pass-rate/win-rate design (majority-vote LLM judging validated against humans) is a
reusable idea for EnterpriseSynth's eval-record scoring, even though the underlying data-generation
mechanism it evaluates cannot be reused directly (it assumes live execution exists).

---

## Base Paper Decision: AgentInstruct

Adopt AgentInstruct's three-flow agentic architecture (content transformation → taxonomy-driven
seed generation → iterative refinement) as the methodological skeleton, and fix its two concrete
gaps for the enterprise cold-start setting:

1. **Replace hallucinated API seeding with real spec ingestion.** AgentInstruct's `tool_use` flow
   invents API descriptions from code or hypothesizes unverified APIs. EnterpriseSynth starts
   from an actual OpenAPI/Swagger spec, so there is nothing to hypothesize — endpoints,
   parameters, and response schemas are all ground truth from the start.
2. **Replace soft, post-hoc verification with a hard, per-sample structural gate.** AgentInstruct
   relies on Suggester-Editor editorial judgment plus a held-out GPT-4-judged benchmark
   (Orca-Bench) computed after the fact. EnterpriseSynth's Static Constraint Validator checks every
   generated trace against the spec's declared types/required fields/response schema before it
   enters the training set — closer in spirit to Self-Instruct/Evol-Instruct's per-sample
   filtering, but structural instead of heuristic-textual.
3. **Emit a jointly-derived eval artifact.** None of the five papers tie their eval mechanism
   (Orca-Bench, API-Bank's human-annotated set, ToolEval) back to the *same* generative act that
   produced the training sample. EnterpriseSynth's intent spec is designed to drive both the SFT
   trace and its paired eval record from one generation pass.

API-Bank and ToolBench remain the primary contrast points for the paper's core claim (the
Execution Paradox): both are effective precisely because they ground responses in real execution
(API-Bank's reproducibility-constrained real DBs; ToolBench's ~470k live RapidAPI calls), which is
exactly the capability enterprise cold-start settings lack.

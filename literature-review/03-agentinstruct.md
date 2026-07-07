# AgentInstruct

**Mitra, Arindam; Del Corro, Luciano; Zheng, Guoqing; Mahajan, Shweti; Rouhana, Dany; Codas,
Andres; Lu, Yadong; Chen, Wei-ge; Vrousgos, Olga; Rosset, Corby; Silva, Fillipe; Khanpour, Hamed;
Lara, Yash; Awadallah, Ahmed (2024).** *AgentInstruct: Toward Generative Teaching with Agentic
Flows.* [arXiv:2407.03502](https://arxiv.org/abs/2407.03502)

## Method

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
   and diversity. The Suggester proposes a way to make the instruction harder/trickier; the Editor
   executes that change while preserving validity.

**Tool-use skill, specifically (the closest analog to EnterpriseSynth):** seeded from either a code
snippet or an API description. **If only code is given, a transformation agent synthesizes an API
description from it** — and separately, an "API retrieval agent" or the LLM itself **hypothesizes
additional APIs it believes exist in the library**, without any ground-truth check. Seed
instructions cover single-API, multi-API/sequenced, "impossible task" (missing API), and
missing-required-parameter cases. Tool responses in the generated traces are **LLM-simulated JSON,
never executed** — e.g. a `Create Meal Plan(...)` call is followed by a fabricated `status:
success` response the model invents.

## Execution model

None (LLM-simulated tool responses). **Verification** is not a per-sample structural filter:
quality assurance is (a) the Suggester-Editor refinement loop itself, a soft editorial check, not
a hard filter, and (b) a **held-out, post-hoc benchmark** — Orca-Bench, 1,700 samples (100/skill),
scored 0–10 by a GPT-4 judge — used to evaluate the resulting dataset/model, not to gate
individual generated samples before they enter the training set. The paper explicitly
acknowledges: *"Synthetic data may not perfectly replicate the complexity and nuances of
real-world data... additional work is needed to better assess the quality of the data."*

## Relevance to EnterpriseSynth — closest architectural base paper

AgentInstruct is the only one of the five reviewed papers that is (a) agentic/multi-flow and (b)
execution-free for tool-use data. Its two concrete weaknesses relative to what EnterpriseSynth
targets, and what EnterpriseSynth changes:

- It **hallucinates the API surface** when seeded from code (invents plausible APIs with no
  ground truth) — a real API spec removes this failure mode entirely, since the schema *is* the
  ground truth, nothing needs to be hypothesized.
- Verification is **soft and post-hoc** (editorial refinement + held-out GPT-4 scoring), not a
  **hard, per-sample structural gate** against declared parameter types/required fields/response
  schema — EnterpriseSynth's Schema Verification Engine is exactly this hard gate.
- It produces no paired, mechanically-derived eval artifact — Orca-Bench is a generic
  quality-scoring set, not something tied to the same intent spec that generated each SFT trace.

This is the paper whose architecture EnterpriseSynth adapts (see `paper/related_work_audit.md`'s
"Base Paper Decision" section for the full reasoning).

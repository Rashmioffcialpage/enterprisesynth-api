# API-Bank

**Li, Minghao; Zhao, Yingxiu; Yu, Bowen; Song, Feifan; Li, Hangyu; Yu, Haiyang; Li, Zhoujun; Huang,
Fei; Li, Yongbin (2023).** *API-Bank: A Comprehensive Benchmark for Tool-Augmented LLMs.*
[arXiv:2304.08244](https://arxiv.org/abs/2304.08244)

## Method

- **API Pool:** 73 implemented APIs for evaluation, 2,138 APIs (1,000 domains) for training.
- **Training data (1,888 dialogues, 4,149 API calls):** synthesized by a **5-agent automated
  pipeline** ("Multi-agent" method) that steps through domain → API → query → API-response
  generation. Reported **98% cost reduction vs. human annotation**, **94% available rate** after
  filtering.
- **Eval data (314 dialogues, 753 API calls):** human-annotated, 4 reviewers per instance.
- **Correctness verification:** predicted API call compared against the annotated gold call for
  equivalence (same query/modification performed, same returned result); free-text response
  quality scored via ROUGE-L.

## Execution model

Real, but reproducibility-constrained. The team stood up actual databases ("we establish the
requisite databases and initialize them with initial entries") for stateful operations; for APIs
pulling external/live data, results are **hard-coded from a specific query time** to keep the
benchmark reproducible. Responses are genuinely executed against real (or realistic, seeded)
backends, not LLM-simulated — but frozen at a point in time rather than live.

## Relevance to EnterpriseSynth

API-Bank's own training-data-generation pipeline is itself a close precedent for "a multi-agent
system can synthesize usable tool-dialogue training data far cheaper than human annotation" (98%
cheaper, 94% valid) — evidence supporting EnterpriseSynth's cost/scale argument. But its execution
model (real DBs, hard-coded live-data snapshots) is still execution-dependent — exactly the
sandbox/backend requirement that doesn't exist for most internal enterprise APIs, and the
"hard-code query-time results for reproducibility" workaround is itself evidence of how much
friction real execution introduces even in a research setting. API-Bank remains one of the two
primary execution-dependent contrast cases for the Execution Paradox argument (the other being
ToolLLM/ToolBench).

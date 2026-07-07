# ToolLLM / ToolBench

**Qin, Yujia; Liang, Shihao; Ye, Yining; Zhu, Kunlun; Yan, Lan; Lu, Yaxi; Lin, Yankai; Cong, Xin;
Tang, Xiangru; Qian, Bill; Zhao, Sihan; Hong, Lauren; Tian, Runchu; Xie, Ruobing; Zhou, Jie;
Gerstein, Mark; Li, Dahai; Liu, Zhiyuan; Sun, Maosong (2023).** *ToolLLM: Facilitating Large
Language Models to Master 16000+ Real-world APIs.*
[arXiv:2307.16789](https://arxiv.org/abs/2307.16789)

## Method

- **API collection:** 16,464 real RESTful APIs, 49 categories, scraped from RapidAPI Hub.
- **Instruction generation:** sample APIs, prompt ChatGPT (guided by 12/36 human-written seed
  examples for single-/multi-tool settings) to produce instructions plus the relevant API subset.
  Three categories: single-tool (I1), intra-category multi-tool (I2), intra-collection multi-tool
  (I3, exploiting RapidAPI's own category hierarchy for functional relatedness).
- **DFSDT solution-path annotation:** ChatGPT proposes an action (API + parameters); **the system
  actually calls the real API** and feeds the genuine response back into context; the model can
  expand further or call "Finish by Giving Up"; exploration uses pre-order traversal (not
  exhaustive) to control API-call cost; long responses are compressed (ChatGPT strips unimportant
  fields) to manage context length.
- **ToolEval:** automatic evaluator; Pass Rate (pass/fail/unsure, majority vote over ≥4 ChatGPT
  predictions) and Win Rate (6 criteria: completeness, factual accuracy, reasoning quality,
  milestones reached, API-exploration breadth, redundancy) — validated at 87.1%/80.3% agreement
  with human judges.

## Execution model

**Real.** Confirmed: 469,585 actual API calls were made during data annotation — this is the
paper's own reported figure, not an estimate.

## Relevance to EnterpriseSynth

The sharpest execution-dependent contrast case among the five. Every solution path in the training
data is grounded by a real, live API call — this is precisely the dependency that collapses
behind an enterprise firewall (no sandbox, security/PII exposure, rate limits). ToolEval's
pass-rate/win-rate design (majority-vote LLM judging validated against humans) is a reusable idea
for EnterpriseSynth's eval-record scoring, even though the underlying data-generation mechanism it
evaluates cannot be reused directly (it assumes live execution exists). ToolBench remains one of
the two primary execution-dependent contrast cases for the Execution Paradox argument (the other
being API-Bank).

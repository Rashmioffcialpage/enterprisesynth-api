# Evol-Instruct / WizardLM

**Xu, Can; Sun, Qingfeng; Zheng, Kai; Geng, Xiubo; Zhao, Pu; Feng, Jiazhan; Tao, Chongyang; Lin,
Qingwei; Jiang, Daxin (2023).** *WizardLM: Empowering Large Pre-Trained Language Models to Follow
Complex Instructions.* [arXiv:2304.12244](https://arxiv.org/abs/2304.12244)

## Method

Takes existing instructions and evolves them into harder ones, rather than generating from
scratch:

- **In-depth evolving** (5 operations): add constraints, deepen the inquiry, concretize general
  concepts, increase reasoning steps, complicate the input format (inject XML/JSON/SQL, etc.).
  Each evolution step adds only ~10–20 words to keep difficulty progression controlled.
- **In-breadth evolving:** generate a "brand new" instruction inspired by an existing one, same
  domain but rarer topic — diversity injection.
- **Elimination evolving** (quality filter): reject an evolution if (a) it produced no information
  gain vs. the original, (b) the response contains "sorry" and is under 80 words (model
  struggled), (c) the response is only punctuation/stopwords, or (d) the evolved instruction leaks
  template scaffolding (e.g. copies "#Rewritten Prompt#" literally).
- Response generation: the same LLM answers its own evolved instruction directly.

## Execution model

None. No tool/API-specific handling anywhere in the method — confirmed by a full-text read, not
just the abstract.

## Relevance to EnterpriseSynth

A second execution-free, heuristic-filtered synthesis method, but with zero structural grounding
to any schema. Useful precedent for the idea that *increasing task complexity along controlled
axes* (here: complicating input format) is itself a viable lever — EnterpriseSynth's Deterministic
Intent Engine effectively replaces "complicate input" with "traverse the real dependency graph one
hop deeper," making the complexity axis schema-derived rather than heuristic.

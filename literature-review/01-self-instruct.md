# Self-Instruct

**Wang, Yizhong; Kordi, Yeganeh; Mishra, Swaroop; Liu, Alisa; Smith, Noah A.; Khashabi, Daniel;
Hajishirzi, Hannaneh (2022).** *Self-Instruct: Aligning Language Models with Self-Generated
Instructions.* [arXiv:2212.10560](https://arxiv.org/abs/2212.10560)

## Method

Bootstraps instruction-tuning data from a model's own generations:

1. Start from 175 human-written seed tasks.
2. Each iteration samples 8 task instructions (6 human-written + 2 previously generated) as
   in-context examples; the model generates new instructions.
3. Classify each instruction as classification vs. non-classification (few-shot, 12+19 seed
   examples) — this routing matters because generation strategy differs per type.
4. Generate instances: **input-first** (write input, then output) for non-classification tasks;
   **output-first** (pick a label, then condition input generation on it) for classification
   tasks — avoiding the label-imbalance bias that input-first produces on classification data.
5. Filter: ROUGE-L similarity to existing instructions must be < 0.7 (dedup), a keyword blocklist
   (e.g. reject anything mentioning images — the model can't process them), instance-level dedup,
   and format/degeneracy heuristics (length, repetitiveness).

## Execution model

None. No tool/API notion at all — this is general-purpose instruction diversity. Filtering is
entirely text-heuristic (similarity + keyword rules), not structural or schema-based.

## Relevance to EnterpriseSynth

The ur-method for "bootstrap synthetic SFT data, filter with cheap heuristics." EnterpriseSynth's
Static Constraint Validator is the schema-grounded analog of Self-Instruct's filtering step —
replacing ROUGE-similarity/keyword rules with structural correctness checks against a real API
definition. Self-Instruct is also the method this project's Self-Instruct baseline
(`scripts/run_baseline_selfinstruct.py`) implements faithfully, per this exact bootstrap mechanism,
for the downstream fine-tuning comparison in Experiment 5 (see `RESULTS.md`).

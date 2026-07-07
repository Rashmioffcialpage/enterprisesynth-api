# Literature Review

Scope, as directed: **exactly five papers**, full-text read (not abstract-only), no additions
beyond this set. Each file below is the per-paper breakdown already used to derive `DESIGN_DOC.md`
§3 and `paper/main.tex` §2 — this folder exists to make the review browsable paper-by-paper rather
than only as a condensed table. Citations are verified against each paper's arXiv abstract page
(see `paper/references.bib` for the exact, checked author lists) — an earlier external draft this
project moved away from contained fabricated author lists for some of these titles, so every name
below was independently confirmed, not taken from memory.

| # | Paper | arXiv | File |
| --- | --- | --- | --- |
| 1 | Self-Instruct (Wang et al., 2022) | [2212.10560](https://arxiv.org/abs/2212.10560) | [01-self-instruct.md](01-self-instruct.md) |
| 2 | Evol-Instruct / WizardLM (Xu et al., 2023) | [2304.12244](https://arxiv.org/abs/2304.12244) | [02-wizardlm.md](02-wizardlm.md) |
| 3 | AgentInstruct (Mitra et al., 2024) | [2407.03502](https://arxiv.org/abs/2407.03502) | [03-agentinstruct.md](03-agentinstruct.md) |
| 4 | API-Bank (Li et al., 2023) | [2304.08244](https://arxiv.org/abs/2304.08244) | [04-api-bank.md](04-api-bank.md) |
| 5 | ToolLLM / ToolBench (Qin et al., 2023) | [2307.16789](https://arxiv.org/abs/2307.16789) | [05-toolbench.md](05-toolbench.md) |

**Base paper decision:** AgentInstruct — the only one of the five that is both agentic/multi-flow
and execution-free for tool-use data, making it the closest architectural skeleton to adapt. See
[03-agentinstruct.md](03-agentinstruct.md) for the two concrete gaps EnterpriseSynth fixes.

**Note on a sixth citation:** `paper/references.bib` also cites Vishwakarma et al. 2025
(arXiv:2510.27287, "EnterpriseBench") — this is not part of the five-paper literature review
above. It exists solely to resolve a naming collision (an early draft of this project informally
called its evaluation suite "EnterpriseBench," which collided with that paper's unrelated
live-sandbox benchmark of the same name; ours was renamed to EnterpriseSynth-Eval). See
`DESIGN_DOC.md`'s top-of-file note for the full history.

For the condensed comparison table and the base-paper adaptation decision in prose, see
`DESIGN_DOC.md` §3 or `paper/related_work_audit.md` (the original full audit this folder is
derived from).

# Self-Review

A mock-reviewer pass on the current state of the paper (`PAPER.md`/`paper/main.tex`) and repo,
written to surface what an actual AAAI/MLinPL reviewer would flag — not to reassure. See
`RESULTS.md` for the numbers referenced below and `DESIGN_DOC.md` §15 for the running open-items
list.

> **Update:** this is a point-in-time snapshot. Since it was written, all five items of the
> Recommendation section below have been resolved (Self-Instruct baseline run and scaled to 3
> held-out APIs, §4.4/§7 Haiku ablation-arm inconsistency fixed by actually implementing it, PDF
> compiled and visually checked, EnterpriseBench naming collision resolved). Beyond that original
> list: the single-draw DigitalOcean result was given a real 5-seed treatment (mean ± std,
> EnterpriseSynth wins on average there too), a private never-published-API cold-start validation
> was built and run (the paper's strongest new evidence for RQ4), 6 more real APIs were added
> (17 total), and an independent LLM-as-a-judge evaluation found — and disclosed against the
> paper's own headline numbers — that binary Tool Selection Accuracy overstates practical quality
> by roughly 2×. See `RESULTS.md` for current numbers — the recommendations below are left as
> originally written for the record.

## Strengths

- **The bug-discovery narrative in Experiment 4 is the paper's best asset.** Going from 57–80%
  to 100% detection, with four named, fixed, regression-tested bugs, is a far more convincing
  verification-quality argument than a flat "100% first try" claim would have been. A reviewer
  who has built anything similar will recognize this as real engineering, not a polished retelling.
- **The paper is unusually candid about scope.** The Summary of Contributions explicitly disclaims
  the Knowledge Graph and Planner as not implemented; the Ablation Study explicitly drops three
  ablations rather than fabricating results for non-existent components. This preempts an obvious
  reviewer objection ("why do you claim a graph-based architecture with no graph in the system?")
  before it's asked.
- **The Experiment 5 result is genuinely the strongest evidence in the paper** (12.5% → 87.5% tool
  selection on a held-out API), and its own limitation (57.1% parameter validity, traced to a
  concrete invented-field-name failure) is reported rather than smoothed over.
- **Citations were independently verified against arXiv abstract pages**, not taken from model
  memory — this matters because at least one earlier draft (not part of the current paper)
  contained fabricated author lists for real paper titles; the current bibliography does not.

## Weaknesses a Reviewer Will Flag

1. **Everything is pilot scale.** 3–4 real APIs, 45 examples per experiment, one held-out API.
   AAAI/MLinPL reviewers will ask whether any of these effects (especially Experiment 5's
   12.5%→87.5%) survive at the paper's stated target scale (~65 specs, 7–8B model). Right now
   there is no evidence either way — this is the single biggest risk to the paper's central claim.
   **[Further resolved since this review was written]** the single-held-out-API framing is now
   stale twice over — Experiment 5 first scaled to 3 held-out APIs (Zoom, DigitalOcean, Spotify;
   the single-run effect turned out non-uniform, a loss on DigitalOcean), then to 17 total APIs (9
   real held-out + 5 private never-published + 3 training), and a 5-seed sweep replaced the
   single-draw numbers with mean ± std — averaged over 5 seeds, EnterpriseSynth wins on all three
   original APIs including DigitalOcean, though individual seeds still vary there. Still short of
   the paper's ~65-spec target scale, but "no evidence either way" is no longer an accurate
   description of where this stands.
2. **Experiment 3's headline numbers (100%/100%) are self-consistency, not generalization**,
   because the same model generated both the intents and the tool selections. The paper says this
   plainly, but a reviewer will still discount these numbers heavily until an independently-
   authored or cross-model-generated intent set exists.
3. **No baselines have actually been run.** Self-Instruct, ToolBench, prompt-only-agent, and
   AgentInstruct are all named as planned comparisons (§4.3) but none exist in any experiment or
   ablation. Without them, "EnterpriseSynth achieves broader coverage than X" (RQ2) is an
   unaddressed research question, not a supported claim. This is the second-biggest gap.
   **[Partially resolved since this review was written]** a real, faithfully-implemented
   Self-Instruct baseline now backs RQ2 (see `RESULTS.md`) — ToolBench, prompt-only-agent, and
   AgentInstruct baselines are still not run.
4. **Experiment 5 substitutes a 0.5B model for the paper's actual 7–8B target**, for real,
   disclosed hardware reasons — but a reviewer may read this as "the core claim was never tested
   at the scale the paper is about." The honest framing (§6.7's "hardware-driven scope change")
   helps, but doesn't remove the gap.
5. **A3 and A4 are inconclusive**, and said so directly — good practice, but it means two of four
   ablations produced no usable result. A reviewer could reasonably ask why these were included at
   all rather than replaced with better-designed tests before submission. (Answer, for the record:
   they were run, the metrics turned out to have a ceiling effect, and that finding — including
   catching our own invalid "sequencing-language" proxy metric — was judged more valuable to
   report than to hide by silently dropping the ablation. A reviewer may not find that framing
   sufficient on its own.)
6. **[Resolved since this review was written]** The PDF has never actually been compiled. No
   LaTeX distribution was available in the development environment (installing one required sudo
   access that wasn't available), so `paper/main.tex` had only been checked for balanced
   `\begin`/`\end` environments and existing figure files — never rendered. Resolved by installing
   `tectonic` (a sudo-free, standalone LaTeX engine); the paper now compiles cleanly to a 30-page
   PDF, visually inspected page-by-page for layout and overflow issues.
7. **[Resolved since this review was written]** The EnterpriseBench naming collision
   (arXiv:2510.27287 already used that name for a different benchmark) was resolved by renaming
   our evaluation dataset to `EnterpriseSynth-Eval`; see `DESIGN_DOC.md`'s top-of-file note.
8. **Figures 2 and 3 (Intent Generation, Trajectory Generation) show flat 100% bars** because the
   pilot scale saturates the chosen metrics. They're accurate, but not visually informative — a
   reviewer skimming figures only will see "everything is 100%" without reading the text that
   explains why that's not the interesting part of those two experiments.
9. **[Resolved since this review was written]** Model choice in §4.4 (Claude Sonnet 5 for
   generation, Claude Haiku 4.5 for an ablation arm) was never actually implemented as an
   ablation — the paper's Models subsection described a planned LLM-based semantic-check ablation
   arm on top of the deterministic verifier that did not appear anywhere in the actual Ablation
   Study (§7). Resolved by implementing it as Ablation A5: confirms the deterministic gate is
   blind to semantic errors by construction, and that Haiku catches 100% of them but with a real,
   disclosed 33% false-positive rate on GitHub (see `RESULTS.md`).
10. **[New finding, added after this review was written]** Every Tool Selection Accuracy number in
    the paper — the metric behind every headline claim — measures endpoint selection only, not
    whether the resulting call is usable. An independent LLM-as-a-judge evaluation (§10 of
    `paper/main.tex`) found that 61% of predictions marked "correct" by the binary metric actually
    contained a real defect (usually a missing or hallucinated parameter): only 21.3% of
    predictions are fully correct by the stricter standard, vs. 48.9% by binary accuracy alone.
    This is disclosed directly in the paper's own Discussion, Limitations, and Conclusion sections
    rather than left for a reviewer to discover — but it does mean a reviewer who reads only the
    Results section and not the Discussion will come away with an inflated sense of how usable
    these generated trajectories actually are. Recommend making sure the abstract-level framing
    (which now does mention this) stays prominent in any future revision.
11. **The private cold-start validation (the paper's strongest new claim) is itself unreplicated.**
    §6.7.3 of `DESIGN_DOC.md` reports a single run on 5 hand-authored, never-published API specs
    showing the fine-tuning effect holds with no meaningful degradation versus public APIs. This
    is exactly the kind of headline number ("87.5% on Zoom", "40.0% on private APIs") that Weakness
    1's history shows should not be trusted from a single draw. A 5-seed treatment of this specific
    result, matching what was already done for the public comparison, would substantially
    strengthen the paper's central claim rather than leave it resting on one run.

## Recommendation

The paper's honesty about its own limitations is a real strength, but right now it reads as a
**pilot-scale systems report with one strong result (Experiment 5) and one very strong result
(Experiment 4)**, not yet as a complete empirical paper. Before submission, prioritize in this
order:

1. Run at least one real baseline (Self-Instruct is the cheapest to implement) against the same
   held-out Zoom set used in Experiment 5 — without this, RQ2 has zero empirical support.
2. Scale Experiment 5 to more held-out APIs (even 3–4, not just Zoom) to see if 12.5%→87.5% is
   representative or a single lucky/unlucky draw.
3. Resolve the §4.4/§7 inconsistency (either implement or remove the Haiku ablation-arm mention).
4. Get the PDF actually compiled and visually checked, even if that means using a different
   machine or a cloud LaTeX service.
5. Resolve the EnterpriseBench name.

Item 6 in the weaknesses list (uncompiled PDF) is low-risk content-wise but should be fixed before
any external reviewer sees a `.tex` file that has literally never been rendered.

# Your Internal APIs Have No Training Data, and You Can't Safely Generate Any By Calling Them. We Tested a Fix.

*Rashmi Thimmaraju · July 2026*

---

Every enterprise team that wants to fine-tune an LLM on their internal tools hits the same wall:
you have an OpenAPI spec, you have zero tool-use training data for it, and every existing method
for generating that data assumes you can safely call the API thousands of times to bootstrap a
dataset. You can't. It's rate-limited, gated behind a VPN, or simply too consequential — nobody
wants to generate SFT data by actually issuing refunds against a production payments API.

We call this the **execution paradox**: the data you need to teach a model to use a tool well is
most valuable exactly where you're least able to generate it by using the tool. We built
**EnterpriseSynth** to resolve it — a pipeline that ingests an OpenAPI spec and emits verified
SFT trajectories and a paired evaluation set, without ever calling the live API. Here's what we
measured.

---

## The question nobody was answering

Every recent method for generating tool-use training data assumes execution. ToolLLM/ToolBench
made 469,585 real RapidAPI calls to ground its data. API-Bank stood up real databases and
hard-coded live-data snapshots for reproducibility. AgentInstruct is execution-free, but it pays
for that by hallucinating the API surface when seeded from code, and it verifies quality with a
soft, post-hoc GPT-4 judge rather than a hard per-sample gate.

The open question: can you get grounding without execution, and verification without a live
oracle to check against? We built a four-stage pipeline to test it — Schema Parser → Intent
Synthesis Agent → Trajectory Generator → Schema Verification Engine — and ran it against real
specs (GitHub, Stripe, Slack, held out: Zoom, DigitalOcean, Spotify).

---

## The headline result: verification is binary, and it wasn't free

A deterministic gate that checks every generated trajectory against the spec's declared types,
required fields, and structure closes a **0%-to-100% gap** on planted structural errors —
without it, every planted error survives; with it, none do (`A2`, `data/generated/ablation_*.json`).

That's a clean result, and clean results on the first try deserve suspicion. So we adversarially
tested the verifier instead of trusting it: planted known errors (wrong types, missing required
params, invalid enums) and measured detection rate. First run: **57–80%**, not 100%. Chasing down
why surfaced four real bugs — not edge cases, load-bearing ones:

| Bug | Where | Real-world impact |
| --- | --- | --- |
| Verifier accepted any value for declared type `"string"`, including objects | `verifier.py` | Silently passed malformed payloads |
| Parser silently dropped `$ref`-indirected parameters | `parser.py` | GitHub's required-param count read as 67; real count is **1,721** |
| `requestBody` schema fields never parsed into typed parameters | `parser.py` | Every Stripe endpoint with body-only params (e.g. `/v1/charges`) was invisible to verification |
| Corruption test harness could drop an optional param instead of a required one | test harness | Was under-testing its own claim |

All four fixed and regression-tested (`tests/`, 21 passing). The methodological point outlives
this codebase: **a static verifier's correctness can't be established by checking that it accepts
good input.** It has to be adversarially tested against bad input it's specifically supposed to
reject, or it will silently pass a third to a half of the errors it exists to catch — and you
won't find out until it matters.

---

## Where the gate runs out — and what closes the rest of the gap

The deterministic gate checks structure, not semantics. It can't tell you a charge amount of
`-500` is wrong, because `-500` is still a well-typed integer. To quantify that blind spot rather
than just gesture at it, we layered a Claude Haiku 4.5 semantic-plausibility check on top:

| API | Semantically corrupted, still structurally valid | ...caught by Haiku |
| --- | --- | --- |
| GitHub | 15/15 (100%) | 15/15 (100%) |
| Stripe | 15/15 (100%) | 15/15 (100%) |
| Slack | 15/15 (100%) | 15/15 (100%) |

100% of the blind spot, closed. Not a free upgrade, though: a **33% false-positive rate on
GitHub**, traced to the model being overly literal about things the tool call never needed to
prove (flagging a numeric repository ID as "unverifiable" because it doesn't obviously match a
name). The practical design isn't "replace the deterministic gate" — it's two-tier: deterministic
gate as the hard blocking filter, LLM semantic check as an advisory signal, calibrated per
parameter type before it gates anything on its own.

---

## The downstream test, and the result we didn't smooth over

Fine-tuning Qwen2.5-0.5B-Instruct (a hardware-scoped stand-in for the target 7–8B model) on
EnterpriseSynth-verified data, evaluated on a held-out API never touched during training:

| Held-out API | Base (untuned) | Self-Instruct baseline | EnterpriseSynth |
| --- | --- | --- | --- |
| Zoom | 12.5% | 25.0% | **75.0%** |
| DigitalOcean | 31.2% | **50.0%** | 43.8% |
| Spotify | 12.5% | 25.0% | **43.8%** |

(Self-Instruct here isn't a strawman — it's a faithful implementation of the actual published
bootstrap mechanism: seed examples, few-shot generation, similarity-based dedup.)

EnterpriseSynth beats the untuned base on all three APIs and beats Self-Instruct on two of three.
On the third — **DigitalOcean — it loses**, 43.8% to 50.0%. We're reporting that loss, not
dropping DigitalOcean from the writeup. Our working hypothesis: Self-Instruct's bootstrap leans on
the base model's pretraining familiarity with GitHub's extremely public API (12/45 of its
"invented" endpoints turned out real — all 12 were GitHub), and DigitalOcean's
infrastructure/DevOps conventions sit structurally closer to GitHub's than Zoom's or Spotify's do.

If that holds up, it's an uncomfortable point about the field's default habit of benchmarking
tool-use methods on GitHub, Stripe, and Slack: a base model's prior exposure to a popular API's
public docs can substitute for genuine schema grounding — an advantage that will not exist for the
private, undocumented internal APIs this entire approach is built for. That strengthens the
cold-start motivation; it also means we can't yet distinguish "EnterpriseSynth generalizes better"
from "EnterpriseSynth generalizes better specifically on APIs unlike ones the base model already
knows." Also worth flagging plainly: retraining for this 3-API comparison gave a **different**
Zoom number than our original single run (75.0% vs. the earlier 87.5%) — expected variance from
unseeded weight init and data order, and a reminder that one run is a draw from a distribution,
not the distribution.

---

## What this pilot can't tell you yet

- **Everything above is pilot scale** — 3–5 real APIs, 45–89 examples each, not the ~65-spec
  stratified sample this is aimed at. Every percentage here is a signal, not a population estimate.
- **The 0.5B model is a stand-in**, not the target scale (Mistral-7B/Llama-3-8B). Whether the
  effect holds, strengthens, or weakens at that scale is untested.
- **Two planned baselines aren't built yet** (ToolBench, a prompt-only agent) — only Self-Instruct
  is a real, run comparison so far.
- **The DigitalOcean hypothesis is unconfirmed.** It's our best current explanation, not a settled
  finding — needs more held-out APIs per structural category to test properly.

---

## Update, July 8: we ran it 5 times, built a real cold-start test, and found our own metric lies a little

Everything above was written after a single run per experiment. Since then we did three things a
single-run pilot can't skip if it wants to be believed:

**We reran the multi-API comparison 5 times, seeds 42/123/777/2025/9999, varying only training
randomness.** The DigitalOcean loss above was real — it also wasn't the average. Across 5 seeds,
EnterpriseSynth beats both the untuned base and Self-Instruct on all three held-out APIs,
including DigitalOcean (53.7% vs. 37.5%, averaged) — but the variance is genuinely large
(±13.7 / ±21.2), so individual seeds still lose there sometimes. Both facts are true at once, and
we're reporting both instead of picking the flattering one.

**We built the cold-start test we didn't have before.** Every held-out API up to this point —
Zoom, DigitalOcean, Spotify — is a real, extremely well-documented public API a base model may
already half-know. So we hand-authored 5 synthetic enterprise API specs that don't exist anywhere
publicly (a fake CRM, HRIS, procurement system, ticketing system, asset registry) and ran the
identical pipeline against them. EnterpriseSynth-tuned accuracy on these never-published APIs
(40.0%) matches accuracy on the public ones (39.6%) — no degradation. This is the closest thing
we have to actually testing the cold-start claim in the headline, rather than a proxy for it.

**We asked an independent judge whether "correct" actually means correct, and it mostly doesn't.**
Every accuracy number in this post is Tool Selection Accuracy — did the model pick the right
endpoint. It says nothing about whether the call it produced is usable. We had Claude score real
predictions on intent match, argument correctness, missing parameters, and reasoning quality, plus
classify the primary error. Result: of predictions marked "correct" by Tool Selection Accuracy,
**61% still had a real defect** — usually a missing or hallucinated parameter. Only 21.3% of
predictions are fully correct by the stricter standard, not the 48.9% the binary metric implies.
**Read every accuracy number above as an upper bound on usability, not an estimate of it.** We're
telling you this about our own headline metric for the same reason we told you about the
DigitalOcean loss: a result you can't poke holes in yourself isn't one you should trust either.

Also scaled to 6 more real APIs (Twilio, Notion, OpenAI, Jira, Asana, Trello) via APIs.guru — wins
on all 6, 17 APIs touched by the pipeline now, and picked up real training/eval latency numbers
(619.8s to fine-tune, 27–95s per API to evaluate) as a byproduct of doing it.

## What we're releasing

**EnterpriseSynth** is open source at
[github.com/Rashmioffcialpage/enterprisesynth-api](https://github.com/Rashmioffcialpage/enterprisesynth-api)
(also mirrored at
[github.com/anote-ai/Research-Enterprise-Synth-API](https://github.com/anote-ai/Research-Enterprise-Synth-API)).
It includes the four-stage pipeline (parser, intent agent, trajectory generator, verifier), the
adversarial verification test harness that found the four bugs above, a real Self-Instruct
baseline implementation, the 5-seed multi-API downstream fine-tuning evaluation, a private
never-published-API cold-start test, an LLM-as-a-judge semantic evaluation, and a full ablation
study scoped strictly to components that actually exist in the code — no ablating modules that
were never built. 45 tests, 17 real and synthetic API specs committed alongside all the generated
data, including every one of the 5 seed runs.

---

## The one-sentence summary

A deterministic schema gate closes a verification gap from 0% to 100% — but only after
adversarial testing forced four real bug fixes — fine-tuning on the resulting data beats a real
Self-Instruct baseline on average across 5 seeds and on APIs that were never published anywhere,
and an independent judge found our own headline metric overstates usability by roughly 2×, which
we're telling you because a benchmark that only reports the numbers that flatter it isn't one you
should trust.

---

*Full experimental writeup, ablations, and honest limitations: `DESIGN_DOC.md` and
`paper/main.tex` in the repository. Questions and issues welcome via GitHub.*

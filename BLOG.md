# The Execution Paradox: Why Enterprise Tool-Use Data Can't Wait for a Sandbox

*A companion post to the EnterpriseSynth paper draft. Numbers and methodology below are pilot-scale
and cited from `RESULTS.md` / `DESIGN_DOC.md` in this repo — see there for full detail.*

## The problem, stated plainly

Every recent paper on training LLM agents to use tools shares one assumption: that you can execute
the tool. AgentInstruct refines trajectories against a live sandbox. API-Bank and ToolLLM/ToolBench
both construct their training data by actually calling APIs and recording what happens. This is a
reasonable assumption if you are building a benchmark around Wikipedia's API or a weather service.
It is not a reasonable assumption inside an enterprise.

Enterprise APIs are frequently unversioned, gated behind VPNs, rate-limited to the point of
uselessness for bulk data generation, or simply too consequential to call thousands of times while
bootstrapping a training set — nobody wants to generate SFT data by actually issuing refunds
against a production payments API. The result is a specific kind of cold start: a team has a
perfectly good OpenAPI schema for their internal service and no tool-use training data or
evaluation suite for it, because every existing method for building one assumes access to a live
environment they don't have and can't safely fake.

We call this the **execution paradox**: the data you need to teach a model to use a tool well is
most valuable exactly where you're least able to generate it by using the tool.

## What we built

EnterpriseSynth is a schema-aware, zero-execution pipeline. Feed it an OpenAPI/Swagger
specification and it emits two things jointly: verified SFT trajectories for fine-tuning, and a
paired evaluation dataset (which we call EnterpriseSynth-Eval, after resolving a naming collision
with an unrelated existing benchmark) with explicit intent specifications attached to each record.
Nothing in the pipeline ever calls the live API.

Structurally, it's four stages: an API Schema Parser that resolves the spec (including `$ref`
indirection and `requestBody` fields, both of which turned out to be nontrivial — more below), an
Intent Synthesis Agent that generates a natural-language task grounded in a specific endpoint, a
Trajectory Generator that produces the corresponding tool-call sequence, and a Schema Verification
Engine that deterministically checks the result against the spec before it's allowed into the
dataset. We were deliberately narrow in scoping related work — five papers only
(Self-Instruct, WizardLM, AgentInstruct, API-Bank, ToolLLM/ToolBench) — because the goal was depth
against the closest prior methods, not a survey. Of those five, AgentInstruct is the only one that
is both agentic and execution-free, which made it the natural architecture to adapt rather than
start from scratch. We changed two things: grounding generation in a real spec instead of letting
the model hallucinate an API surface from seed code, and replacing AgentInstruct's soft
editorial-refinement-plus-held-out-judge pipeline with a hard structural verification gate.

That second choice — deterministic verification as a hard gate rather than a soft signal — turned
out to be the paper's central empirical claim, and the reason it's defensible is not that we
assumed it works.

## The result we didn't expect to be the interesting one

The obvious ablation is: does removing the verifier matter? Yes, unambiguously — 0% of planted
structural errors are caught without it, 100% are caught with it. That's a clean result, but a
clean result you get on the first try is also the kind of result a reviewer should be suspicious
of, because a verifier that reports 100% might just be a verifier nobody has tried hard enough to
break.

So we tried to break it. We built an adversarial test harness that plants specific, known errors
(wrong types, missing required parameters, invalid enum values) into trajectories and checks
whether the verifier catches each one. The first run caught only 57–80% of planted errors —
not 100%. Chasing down why surfaced four real, distinct bugs: the parser was silently dropping
`$ref`-indirected parameters (GitHub's spec went from an apparent 67 required parameters to a
correct 1,721 once fixed), it wasn't parsing `requestBody` fields into typed parameters at all
(which meant every Stripe endpoint whose parameters live entirely in the request body, like
`/v1/charges`, was invisible to verification), the verifier's type-compatibility check silently
accepted objects and lists wherever a string was expected, and our own test harness had a
subtle bug where "drop a required parameter" could accidentally drop an optional one instead.

Every one of those bugs is now fixed and regression-tested, and the verifier's 100% is real. But
the methodological point outlives this specific codebase: **a static verifier's correctness cannot
be established by checking that it accepts good input.** It has to be adversarially tested against
bad input it's specifically supposed to reject, or it will silently pass a third to a half of the
errors it exists to catch, and you will not find out until it matters.

## Where verification runs out, and what we did about it

The deterministic gate checks structure — types, required fields, enum membership — not semantics.
It can't tell you that a charge amount of `-500` is wrong, or that a placeholder string slipped
into a field, because both are still well-typed values. To quantify that blind spot rather than
just gesture at it, we ran an ablation with a Claude Haiku 4.5 semantic-plausibility check layered
on top of the deterministic gate. It confirmed the blind spot exists (100% of semantically
corrupted trajectories pass the structural gate) and that a cheap LLM check can close it (100%
caught). It also showed this isn't a free upgrade: a 33% false-positive rate on GitHub, where the
model flagged things as implausible that the underlying tool call never actually needed to prove
(treating a numeric repository ID as suspicious because it doesn't obviously "match" a repository
name). The honest takeaway is a two-tier design — deterministic gate as the hard blocking filter,
LLM semantic check as an advisory signal calibrated per parameter type — not a wholesale
replacement of one by the other.

## The downstream result, and the part of it we didn't smooth over

The most direct test of whether any of this matters is downstream: does fine-tuning on
EnterpriseSynth-generated data actually improve tool-use performance on a held-out API? On a
single held-out API (Zoom), the answer was a large yes — tool-selection accuracy went from 12.5%
untuned to 87.5% after fine-tuning. That's the kind of number that's tempting to lead with and stop
there.

We scaled it to three held-out APIs instead, and compared against a real Self-Instruct baseline —
not a strawman, but an implementation faithful to Self-Instruct's actual published bootstrap
mechanism (seed examples, few-shot generation, similarity-based deduplication). Retraining from
scratch for this comparison also gave us an honest check on the original number: on Zoom, the
retrained model scored 75.0%, not 87.5% — expected variance, since neither weight
initialization nor training-data order was seed-fixed, but a useful reminder that a single run is
a draw from a distribution, not the distribution. Across all three held-out APIs (Zoom,
DigitalOcean, Spotify), EnterpriseSynth beat the untuned baseline every time (75.0%, 43.8%, and
43.8% vs. 12.5%, 31.2%, and 12.5%) and beat Self-Instruct on two of three (Zoom 75.0% vs. 25.0%;
Spotify 43.8% vs. 25.0%). On the third — DigitalOcean — it lost, 43.8% to Self-Instruct's 50.0%.

We reported that loss rather than dropping DigitalOcean from the write-up. Our working hypothesis
is that Self-Instruct's bootstrap leans on the base model's pretraining familiarity with
well-documented public APIs, and DigitalOcean's infrastructure/DevOps conventions sit closer to
GitHub's (which seeded the bootstrap) than Zoom's or Slack's do. If that holds up, it's an
uncomfortable point about the field's default practice of benchmarking tool-use methods against
GitHub, Stripe, and Slack: a base model's prior exposure to a popular API's public documentation
can substitute for genuine schema grounding in a way that will never be available for the private,
undocumented internal APIs this whole line of work is actually motivated by. That would make the
cold-start problem harder, not easier, to demonstrate convincingly with public benchmark APIs — a
real methodological challenge for evaluating this class of method, and one we don't yet have a
clean answer to.

## What this is and isn't, right now

Everything above is pilot scale: three to five real APIs, 45–89 examples per experiment, a
0.5B-parameter model standing in for the 7–8B target because of local hardware constraints. Every
percentage in this post should be read as a signal worth investigating further, not a population
estimate. Two planned baselines (ToolBench, a prompt-only agent) aren't built yet. The Knowledge
Graph and multi-step Planner in the original design remain unimplemented, and we've said so
explicitly in the paper rather than describing an architecture the code doesn't have.

What we think is worth taking away regardless of scale: verification against a live sandbox is not
the only way to make tool-use training data trustworthy, a deterministic schema-based gate can get
you most of the way there if you're willing to adversarially test it rather than trust it, and the
gap that's left over is measurable rather than mysterious. That's a narrower claim than "solves
enterprise tool use," and we think it's the right size of claim for where this work actually is.

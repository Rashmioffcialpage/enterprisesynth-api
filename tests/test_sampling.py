import json
from pathlib import Path

import pytest

from enterprisesynth.parser import SchemaParser
from enterprisesynth.sampling import sample_and_distract

SPECS_DIR = Path(__file__).resolve().parent.parent / "data" / "specs"
GENERATED_DIR = Path(__file__).resolve().parent.parent / "data" / "generated"


@pytest.fixture(scope="module")
def github_schema():
    with open(SPECS_DIR / "github.json") as f:
        raw = json.load(f)
    return SchemaParser().parse(raw)


def test_sample_size_returns_correct_count(github_schema):
    sample, _ = sample_and_distract(github_schema, sample_size=5)
    assert len(sample) == 5


def test_same_seed_is_deterministic(github_schema):
    sample1, distractors1 = sample_and_distract(github_schema, seed=42, sample_size=5)
    sample2, distractors2 = sample_and_distract(github_schema, seed=42, sample_size=5)
    assert [(e.method, e.path) for e in sample1] == [(e.method, e.path) for e in sample2]
    assert [(e.method, e.path) for e in distractors1] == [(e.method, e.path) for e in distractors2]


def test_distractors_never_overlap_with_sample(github_schema):
    sample, distractors = sample_and_distract(github_schema, seed=42, sample_size=5, n_distractors=10)
    sample_keys = {(e.method, e.path) for e in sample}
    distractor_keys = {(e.method, e.path) for e in distractors}
    assert sample_keys.isdisjoint(distractor_keys)


def test_exclude_mode_skips_sample_step(github_schema):
    sample, distractors = sample_and_distract(github_schema, seed=42, sample_size=None, exclude=[])
    assert sample is None
    assert len(distractors) == 10  # default n_distractors


def test_matches_committed_experiment2_sampling(github_schema):
    # Regression: this exact sampling (seed=42, sample_size=5) must reproduce the endpoints
    # already committed in data/generated/experiment2_intents.json, generated before the
    # sampling logic was refactored into this shared module.
    with open(GENERATED_DIR / "experiment2_intents.json") as f:
        committed = json.load(f)

    sample, _ = sample_and_distract(github_schema, seed=42, sample_size=5)
    new_keys = sorted((e.method, e.path) for e in sample)
    committed_keys = sorted((item["method"], item["path"]) for item in committed["GitHub"])
    assert new_keys == committed_keys

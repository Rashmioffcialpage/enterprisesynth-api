"""Aggregates scripts/run_private_coldstart_eval.py's per-seed output files into mean +/- std,
giving the private cold-start validation the same multi-seed rigor already applied to the public
comparison (scripts/aggregate_multi_seed_scaling.py) -- closing the gap flagged in
DESIGN_DOC.md's Limitations and REVIEW.md item 11: the paper's strongest new claim (RQ4) rested
on a single un-seeded run.

Reads every data/generated/private_coldstart_results_seed*.json file present, computes
tool-selection-accuracy mean/std across seeds for each (eval set, arm) pair.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "generated"


def main() -> None:
    seed_files = sorted(OUT_DIR.glob("private_coldstart_results_seed*.json"))
    if not seed_files:
        print("No seed result files found. Run run_private_coldstart_eval.py --seed N first.")
        return

    print(f"Aggregating {len(seed_files)} seed runs: {[f.name for f in seed_files]}\n")

    per_set_arm: dict[str, dict[str, list[float]]] = {}
    for f in seed_files:
        with open(f) as fh:
            data = json.load(fh)
        for eval_set, arms in data.items():
            per_set_arm.setdefault(eval_set, {})
            for arm_name, arm in arms.items():
                per_set_arm[eval_set].setdefault(arm_name, [])
                per_set_arm[eval_set][arm_name].append(arm["tool_selection_accuracy"])

    summary = []
    for eval_set, arms in per_set_arm.items():
        row = {"Eval set": eval_set, "n_seeds": len(seed_files)}
        for arm_name, values in arms.items():
            mean = statistics.mean(values)
            std = statistics.stdev(values) if len(values) > 1 else 0.0
            row[arm_name] = f"{mean:.1f} +/- {std:.1f}"
            row[f"_{arm_name}_raw"] = values
        summary.append(row)

    print(json.dumps(summary, indent=2))

    out_path = OUT_DIR / "private_coldstart_multi_seed_summary.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()

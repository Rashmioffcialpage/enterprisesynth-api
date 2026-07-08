"""Aggregates scripts/scale_experiment5_heldout.py's per-seed output files into mean +/- std per
held-out API per model, replacing the single-draw numbers that were shown not to replicate
(DESIGN_DOC.md's disclosed limitation: "Mostly single-seed runs").

Reads every data/generated/experiment5_multi_api_results_seed*.json file present, computes
tool-selection-accuracy mean/std across seeds for each (API, model) pair.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "generated"


def main() -> None:
    seed_files = sorted(OUT_DIR.glob("experiment5_multi_api_results_seed*.json"))
    if not seed_files:
        print("No seed result files found. Run scale_experiment5_heldout.py --seed N first.")
        return

    print(f"Aggregating {len(seed_files)} seed runs: {[f.name for f in seed_files]}\n")

    per_api_model: dict[str, dict[str, list[float]]] = {}
    for f in seed_files:
        with open(f) as fh:
            data = json.load(fh)
        for api_name, arms in data.items():
            per_api_model.setdefault(api_name, {})
            for arm_name, arm in arms.items():
                per_api_model[api_name].setdefault(arm_name, [])
                per_api_model[api_name][arm_name].append(arm["tool_selection_accuracy"])

    summary = []
    for api_name, arms in per_api_model.items():
        row = {"Held-out API": api_name, "n_seeds": len(seed_files)}
        for arm_name, values in arms.items():
            mean = statistics.mean(values)
            std = statistics.stdev(values) if len(values) > 1 else 0.0
            row[arm_name] = f"{mean:.1f} +/- {std:.1f}"
            row[f"_{arm_name}_raw"] = values
        summary.append(row)

    print(json.dumps(summary, indent=2))

    out_path = OUT_DIR / "experiment5_multi_seed_summary.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()

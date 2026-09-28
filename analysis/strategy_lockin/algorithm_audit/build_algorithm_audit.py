#!/usr/bin/env python3
"""Audit the 16 trajectories that change their training algorithm.

Only 16 of the 1,338 trajectories ever change training algorithm, over 35
transitions.  That is small enough to read by hand, and the paper's Appendix A.2
audit plus the Table 6 case studies come from doing so.  This script rebuilds
the mechanical part of that audit from the released annotations.

Outputs (output/):
  algorithm_change_trajectories.csv  the 16, with their switch counts
  algorithm_transitions.csv          the 35 transitions, with direction
  table6_cases.csv                   the 5 case studies, structure verified

What is *not* reproducible here: the `observation` column of Table 6 quotes each
run's own comparator and sample size, read out of trajectory logs that are not
redistributed.  Those strings are carried as curated constants below and the
script verifies everything around them -- that the case exists, that it sits in
the stated benchmark / base model / framework cell, and that it really does
change algorithm in the stated direction.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any

HERE = Path(__file__).resolve().parent

FRAMEWORK = {
    "Claude": "Claude Code",
    "GLM-X": "Claude Code",
    "Qwen3Max": "Claude Code",
    "Codex": "Codex CLI",
    "OpenCode": "OpenCode",
}
# Objective forms, in the paper's shorthand.  Full SFT and PEFT share the
# supervised-likelihood form, so swapping one for the other is not an algorithm
# change and does not appear here.
SHORTHAND = {
    "supervised_likelihood": "SFT",
    "preference_optimization": "DPO",
    "reward_optimization": "GRPO",
}
UNRECOGNIZED = {None, "", "objective_unknown", "unknown"}

# Appendix A.2, as printed.
PAPER_AUDIT = {
    "trajectories": 16,
    "transitions": 35,
    "begin_with_sft": 14,
    "switch_at_least_twice": 11,
    "return_to_sft": 15,
    "median_first_switch": 0.40,
    "median_all_switches": 0.67,
}

# Table 6.  `observation` and `interpretation` are quoted from the paper, which
# read them out of the run's own logs; everything else is verified below.
PAPER_TABLE_6: tuple[dict[str, str], ...] = (
    {
        "case": "3fd3ea0b",
        "benchmark": "ArenaHardWriting",
        "base_model": "SmolLM3-3B-Base",
        "agent_framework": "Codex CLI",
        "change": "SFT->DPO",
        "observation": "Held-out 256-pair proxy: 66.0% -> 66.8%",
        "interpretation": "Positive; +0.8pp",
    },
    {
        "case": "c92715d6",
        "benchmark": "ArenaHardWriting",
        "base_model": "Gemma-3-4B-PT",
        "agent_framework": "Claude Code",
        "change": "SFT->DPO",
        "observation": "Benchmark win rate: ~8% -> 16.7%",
        "interpretation": "Positive; approximately 2x",
    },
    {
        "case": "50c64287",
        "benchmark": "ArenaHardWriting",
        "base_model": "Qwen3-4B-Base",
        "agent_framework": "Codex CLI",
        "change": "SFT->DPO",
        "observation": "Same 8-prompt local proxy: 7.14% -> 7.69%",
        "interpretation": "Positive; small sample",
    },
    {
        "case": "860ceacd",
        "benchmark": "AIME 2025",
        "base_model": "Qwen3-1.7B-Base",
        "agent_framework": "Claude Code",
        "change": "SFT->GRPO",
        "observation": "30-problem evaluation: 0% -> 3.3% (1/30)",
        "interpretation": "Positive; high variance",
    },
    {
        "case": "8226f786",
        "benchmark": "ArenaHardWriting",
        "base_model": "SmolLM3-3B-Base",
        "agent_framework": "Codex CLI",
        "change": "SFT->DPO",
        "observation": (
            "External proxy: 0.539 -> 0.478; internal DPO reward accuracy: 0.713 -> 0.727"
        ),
        "interpretation": "Counterexample; metric mismatch",
    },
)


def check(label: str, observed: Any, expected: Any) -> None:
    if observed != expected:
        raise AssertionError(f"{label}: recomputed {observed!r}, paper reports {expected!r}")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"No rows generated for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--annotations",
        type=Path,
        default=HERE.parents[1] / "annotations" / "strategy_level",
    )
    parser.add_argument(
        "--broad-criterion",
        type=Path,
        default=HERE.parent / "broad_criterion" / "output",
    )
    parser.add_argument("--output", type=Path, default=HERE / "output")
    args = parser.parse_args()

    with (args.annotations / "tables" / "trajectory_analysis.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        trajectories = {row["trajectory_id"]: row for row in csv.DictReader(handle)}
    labels: dict[tuple[str, int], dict[str, Any]] = {}
    experiments: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with (args.broad_criterion / "episode_labels.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            labels[(row["trajectory_id"], row["experiment_index"])] = row
            experiments[row["trajectory_id"]].append(row)
    with (args.broad_criterion / "broad_transitions.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        changes = [
            row
            for row in csv.DictReader(handle)
            if row["paradigm_change"] in ("1", "True", "true")
        ]

    def form(trajectory: str, index: int) -> str:
        return SHORTHAND.get(labels[(trajectory, index)]["objective_form"], "unknown")

    check("algorithm transitions", len(changes), PAPER_AUDIT["transitions"])
    affected = sorted({row["trajectory_id"] for row in changes})
    check("trajectories with an algorithm change", len(affected), PAPER_AUDIT["trajectories"])

    # --- the 35 transitions --------------------------------------------------
    # Normalized progress is the position of the arriving experiment within the
    # trajectory's own experiment sequence, on [0, 1], so it is comparable
    # across trajectories of different lengths.
    switch_counts = Counter(row["trajectory_id"] for row in changes)
    transition_rows: list[dict[str, Any]] = []
    first_progress: list[float] = []
    all_progress: list[float] = []
    seen: set[str] = set()
    for row in sorted(changes, key=lambda r: (r["trajectory_id"], int(r["to_experiment"]))):
        trajectory = row["trajectory_id"]
        arriving = int(row["to_experiment"])
        total = len(experiments[trajectory])
        progress = arriving / (total - 1) if total > 1 else 0.0
        all_progress.append(progress)
        is_first = trajectory not in seen
        if is_first:
            first_progress.append(progress)
            seen.add(trajectory)
        meta = trajectories[trajectory]
        transition_rows.append(
            {
                "trajectory_id": trajectory,
                "agent_framework": FRAMEWORK[meta["harness_family"]],
                "benchmark": meta["benchmark"],
                "base_model": meta["base_model"],
                "from_experiment": int(row["from_experiment"]),
                "to_experiment": arriving,
                "from_algorithm": form(trajectory, int(row["from_experiment"])),
                "to_algorithm": form(trajectory, arriving),
                "returns_to_sft": form(trajectory, arriving) == "SFT",
                "is_first_switch": is_first,
                "normalized_progress": round(progress, 4),
            }
        )

    check(
        "transitions returning to SFT",
        sum(row["returns_to_sft"] for row in transition_rows),
        PAPER_AUDIT["return_to_sft"],
    )
    check(
        "median first-switch progress",
        round(median(first_progress), 2),
        PAPER_AUDIT["median_first_switch"],
    )
    check(
        "median switch progress",
        round(median(all_progress), 2),
        PAPER_AUDIT["median_all_switches"],
    )

    # --- the 16 trajectories -------------------------------------------------
    trajectory_rows: list[dict[str, Any]] = []
    for trajectory in affected:
        meta = trajectories[trajectory]
        recognized = [
            row
            for row in sorted(experiments[trajectory], key=lambda r: r["experiment_index"])
            if row["objective_form"] not in UNRECOGNIZED
        ]
        sequence = [SHORTHAND.get(row["objective_form"], "unknown") for row in recognized]
        trajectory_rows.append(
            {
                "trajectory_id": trajectory,
                "agent_framework": FRAMEWORK[meta["harness_family"]],
                "benchmark": meta["benchmark"],
                "base_model": meta["base_model"],
                "n_experiments": len(experiments[trajectory]),
                "n_algorithm_changes": switch_counts[trajectory],
                "begins_with_sft": sequence[0] == "SFT" if sequence else False,
                "oscillates": switch_counts[trajectory] >= 2,
                "algorithm_sequence": " ".join(sequence),
                "in_table_6": any(
                    trajectory.startswith(case["case"]) for case in PAPER_TABLE_6
                ),
            }
        )

    check(
        "trajectories beginning with SFT",
        sum(row["begins_with_sft"] for row in trajectory_rows),
        PAPER_AUDIT["begin_with_sft"],
    )
    check(
        "trajectories switching at least twice",
        sum(row["oscillates"] for row in trajectory_rows),
        PAPER_AUDIT["switch_at_least_twice"],
    )

    # --- Table 6 -------------------------------------------------------------
    objective_pass = args.annotations.parent / "objective_level" / "trajectory_annotations.jsonl"
    with objective_pass.open(encoding="utf-8") as handle:
        annotated = {
            json.loads(line)["trajectory_id"] for line in handle if line.strip()
        }
    case_rows: list[dict[str, Any]] = []
    for case in PAPER_TABLE_6:
        matches = [t for t in affected if t.startswith(case["case"])]
        if len(matches) != 1:
            raise AssertionError(
                f"case {case['case']}: matched {len(matches)} of the 16 trajectories, expected 1"
            )
        trajectory = matches[0]
        if trajectory not in annotated:
            raise AssertionError(
                f"case {case['case']}: {trajectory} is absent from {objective_pass.name}"
            )
        meta = trajectories[trajectory]
        check(f"{case['case']} benchmark", meta["benchmark"], case["benchmark"])
        check(f"{case['case']} base model", meta["base_model"], case["base_model"])
        check(
            f"{case['case']} framework",
            FRAMEWORK[meta["harness_family"]],
            case["agent_framework"],
        )
        directions = {
            f"{row['from_algorithm']}->{row['to_algorithm']}"
            for row in transition_rows
            if row["trajectory_id"] == trajectory
        }
        if case["change"] not in directions:
            raise AssertionError(
                f"case {case['case']}: {case['change']} not among its transitions {sorted(directions)}"
            )
        case_rows.append(
            {
                "case": case["case"],
                "trajectory_id": trajectory,
                "benchmark": case["benchmark"],
                "base_model": case["base_model"],
                "agent_framework": case["agent_framework"],
                "change": case["change"],
                "observation": case["observation"],
                "interpretation": case["interpretation"],
                "observation_source": "trajectory log, not redistributed",
                "annotation_reference": (
                    "analysis/annotations/objective_level/trajectory_annotations.jsonl"
                    f" :: {trajectory}"
                ),
            }
        )

    write_csv(args.output / "algorithm_change_trajectories.csv", trajectory_rows)
    write_csv(args.output / "algorithm_transitions.csv", transition_rows)
    write_csv(args.output / "table6_cases.csv", case_rows)
    print(
        f"Wrote 3 tables to {args.output}: {len(trajectory_rows)} trajectories, "
        f"{len(transition_rows)} transitions, {len(case_rows)} cases; "
        "all paper values reproduced."
    )


if __name__ == "__main__":
    main()

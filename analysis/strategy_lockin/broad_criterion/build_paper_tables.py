#!/usr/bin/env python3
"""Rebuild the paper's strategy-change tables from the released audit output.

`build_broad_transitions.py` needs the pipeline's `intermediate/` tree, which is
too large to redistribute.  This script needs only files that ship with the
repository -- `output/broad_transitions.csv`, `output/episode_labels.jsonl` and
the strategy-level annotation table -- so every number in Tables 1, 4 and 5 can
be recomputed from a checkout rather than taken on trust.

Outputs (output/tables/):
  framework_by_benchmark.csv    Table 4: 7 benchmarks x 3 agent frameworks
  strategy_change_partition.csv Table 5: the 74 changes by changed dimension

Every value the paper prints is asserted against, so a drift in the released
annotations fails the run instead of silently producing a different table.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent

# The corpus is grouped by `harness_family`; the paper groups those five
# families into three agent frameworks.  GLM-X and Qwen3Max are Claude Code
# configurations driven by a different agent model, so they pool into it.
FRAMEWORK = {
    "Claude": "Claude Code",
    "GLM-X": "Claude Code",
    "Qwen3Max": "Claude Code",
    "Codex": "Codex CLI",
    "OpenCode": "OpenCode",
}
FRAMEWORKS = ("Claude Code", "Codex CLI", "OpenCode")
BENCHMARKS = (
    "AIME 2025",
    "ArenaHardWriting",
    "BFCL",
    "GPQA Main",
    "GSM8K",
    "HealthBench",
    "HumanEval",
)
METHODS = ("full_sft", "peft_sft", "rl", "preference", "distillation")
METHOD_LABELS = {
    "full_sft": "Full SFT",
    "peft_sft": "PEFT",
    "rl": "RL",
    "preference": "Preference optimization",
    "distillation": "Distillation",
}
# `initial_strategy_family` sentinels.  `no_parameter_update` means the
# trajectory never trained and never stated a plan; `other_unknown` means no
# complete state could be resolved.  Both are excluded from the 814.
INITIAL_SENTINELS = ("no_parameter_update", "other_unknown")

# The mechanical pass flags stage-structure candidates for author review rather
# than accepting them (a re-launch after a crash looks like a stage change).
# Two were flagged; one was accepted on review and one rejected as a restart.
# See report.md and docs/annotation-protocol.md#reconciling-73-vs-74.
ADJUDICATED_STAGE_CHANGE = "c8fd5fbb5f110a978afb"
REJECTED_STAGE_CANDIDATE = "de3168aa0c59fecdd925"

UNRECOGNIZED_OBJECTIVE = {None, "", "objective_unknown", "unknown"}

# Table 4 as printed, keyed by (framework, benchmark):
#   final metric, n scored, initial-strategy count / denominator, changes / pairs
PAPER_TABLE_4: dict[tuple[str, str], tuple[float, int, int, int, int, int]] = {
    ("Claude Code", "AIME 2025"): (0.049, 33, 19, 31, 14, 132),
    ("Claude Code", "ArenaHardWriting"): (0.135, 34, 27, 30, 19, 174),
    ("Claude Code", "BFCL"): (0.860, 44, 33, 51, 0, 171),
    ("Claude Code", "GPQA Main"): (0.279, 36, 17, 27, 4, 171),
    ("Claude Code", "GSM8K"): (0.556, 38, 24, 31, 8, 187),
    ("Claude Code", "HealthBench"): (0.281, 36, 22, 28, 1, 179),
    ("Claude Code", "HumanEval"): (0.480, 40, 24, 33, 8, 189),
    ("Codex CLI", "AIME 2025"): (0.009, 43, 40, 42, 3, 120),
    ("Codex CLI", "ArenaHardWriting"): (0.109, 39, 30, 40, 11, 159),
    ("Codex CLI", "BFCL"): (0.573, 44, 44, 45, 0, 67),
    ("Codex CLI", "GPQA Main"): (0.277, 46, 42, 46, 0, 152),
    ("Codex CLI", "GSM8K"): (0.443, 47, 36, 43, 0, 198),
    ("Codex CLI", "HealthBench"): (0.231, 42, 37, 43, 0, 106),
    ("Codex CLI", "HumanEval"): (0.332, 47, 45, 47, 1, 141),
    ("OpenCode", "AIME 2025"): (0.018, 38, 25, 41, 1, 196),
    ("OpenCode", "ArenaHardWriting"): (0.091, 34, 27, 39, 1, 235),
    ("OpenCode", "BFCL"): (0.372, 28, 23, 36, 0, 195),
    ("OpenCode", "GPQA Main"): (0.172, 36, 25, 42, 0, 213),
    ("OpenCode", "GSM8K"): (0.381, 36, 24, 40, 2, 219),
    ("OpenCode", "HealthBench"): (0.219, 35, 29, 40, 1, 159),
    ("OpenCode", "HumanEval"): (0.263, 36, 31, 39, 0, 194),
}
# Table 4 `Overall` rows and Table 1: default count / 814 split, changes / pairs.
PAPER_OVERALL = {
    "Claude Code": ("full_sft", 166, 231, 54, 1203),
    "Codex CLI": ("peft_sft", 274, 306, 15, 943),
    "OpenCode": ("full_sft", 184, 277, 5, 1411),
}
PAPER_CORPUS = (624, 814, 74, 3557)
# Table 5.
PAPER_TABLE_5 = {"algorithm": 35, "data_source": 38, "stages": 1, "overall": 74}
# Appendix A.3.
PAPER_A3 = {"experiments": 5111, "recognized": 4378, "unrecognized": 733}


def check(label: str, observed: Any, expected: Any) -> None:
    if observed != expected:
        raise AssertionError(f"{label}: recomputed {observed!r}, paper reports {expected!r}")


def rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def is_true(value: str) -> bool:
    return value in ("1", "True", "true")


def load_inputs(annotations: Path, output: Path) -> tuple[list[dict[str, str]], list[dict[str, Any]], list[dict[str, str]]]:
    with (annotations / "tables" / "trajectory_analysis.csv").open(newline="", encoding="utf-8") as handle:
        trajectories = list(csv.DictReader(handle))
    with (output / "episode_labels.jsonl").open(encoding="utf-8") as handle:
        episodes = [json.loads(line) for line in handle if line.strip()]
    with (output / "broad_transitions.csv").open(newline="", encoding="utf-8") as handle:
        transitions = list(csv.DictReader(handle))
    return trajectories, episodes, transitions


def check_corpus_counts(episodes: list[dict[str, Any]], n_transitions: int) -> None:
    """Appendix A.3: 5,111 verified experiments, 4,378 recognized, 3,557 pairs.

    No table is emitted; these are the paper's own counts and this only asserts
    that the released annotations still reproduce them.
    """
    check("verified training experiments", len(episodes), PAPER_A3["experiments"])
    recognized = [e for e in episodes if e.get("objective_form") not in UNRECOGNIZED_OBJECTIVE]
    check("recognized algorithms", len(recognized), PAPER_A3["recognized"])
    check("unrecognized", len(episodes) - len(recognized), PAPER_A3["unrecognized"])
    check("recognized adjacent pairs", n_transitions, PAPER_CORPUS[3])


def build_framework_by_benchmark(
    trajectories: list[dict[str, str]],
    transitions: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Table 4, plus the `Overall` row that is also Table 1's switch-rate column."""
    meta = {
        row["trajectory_id"]: (FRAMEWORK[row["harness_family"]], row["benchmark"])
        for row in trajectories
    }
    pairs: Counter[tuple[str, str]] = Counter()
    mechanical: Counter[tuple[str, str]] = Counter()
    adjudicated: Counter[tuple[str, str]] = Counter()
    for row in transitions:
        cell = meta[row["trajectory_id"]]
        pairs[cell] += 1
        if is_true(row["broad_change_mechanical"]):
            mechanical[cell] += 1
    adjudicated[meta[ADJUDICATED_STAGE_CHANGE]] += 1

    rows: list[dict[str, Any]] = []
    for framework in FRAMEWORKS:
        for benchmark in BENCHMARKS:
            cell = (framework, benchmark)
            selected = [row for row in trajectories if meta[row["trajectory_id"]] == cell]
            trained = [
                row for row in selected if float(row["training_experiment_count"] or 0) > 0
            ]
            scores = [
                float(row["final_metric"])
                for row in trained
                if row.get("final_metric") not in (None, "", "None")
            ]
            recognized = [
                row for row in selected if row["initial_strategy_family"] in METHODS
            ]
            distribution = Counter(row["initial_strategy_family"] for row in recognized)
            default, default_n = distribution.most_common(1)[0]
            changes = mechanical[cell] + adjudicated[cell]

            expected = PAPER_TABLE_4[cell]
            mean_score = sum(scores) / len(scores)
            if abs(mean_score - expected[0]) > 0.0006:
                raise AssertionError(
                    f"{cell} final metric: recomputed {mean_score:.4f}, paper reports {expected[0]}"
                )
            check(f"{cell} scored trajectories", len(scores), expected[1])
            check(f"{cell} default count", default_n, expected[2])
            check(f"{cell} recognized initial", len(recognized), expected[3])
            check(f"{cell} strategy changes", changes, expected[4])
            check(f"{cell} pairs", pairs[cell], expected[5])

            rows.append(
                {
                    "agent_framework": framework,
                    "benchmark": benchmark,
                    "n_trajectories": len(selected),
                    "n_scored": len(scores),
                    "mean_final_metric": round(mean_score, 4),
                    "default_strategy": METHOD_LABELS[default],
                    "default_strategy_count": default_n,
                    "n_recognized_initial": len(recognized),
                    "default_strategy_share": round(rate(default_n, len(recognized)), 4),
                    "strategy_changes": changes,
                    "changes_mechanical": mechanical[cell],
                    "changes_adjudicated": adjudicated[cell],
                    "recognized_pairs": pairs[cell],
                    "switch_rate": round(rate(changes, pairs[cell]), 4),
                }
            )

    for framework in FRAMEWORKS:
        cells = [(framework, benchmark) for benchmark in BENCHMARKS]
        selected = [row for row in trajectories if meta[row["trajectory_id"]][0] == framework]
        recognized = [row for row in selected if row["initial_strategy_family"] in METHODS]
        distribution = Counter(row["initial_strategy_family"] for row in recognized)
        default, default_n = distribution.most_common(1)[0]
        total_pairs = sum(pairs[cell] for cell in cells)
        total_changes = sum(mechanical[cell] + adjudicated[cell] for cell in cells)

        expected_default, expected_n, expected_den, expected_changes, expected_pairs = (
            PAPER_OVERALL[framework]
        )
        check(f"{framework} default strategy", default, expected_default)
        check(f"{framework} default count", default_n, expected_n)
        check(f"{framework} recognized initial", len(recognized), expected_den)
        check(f"{framework} strategy changes", total_changes, expected_changes)
        check(f"{framework} pairs", total_pairs, expected_pairs)

        rows.append(
            {
                "agent_framework": framework,
                "benchmark": "Overall",
                "n_trajectories": len(selected),
                "n_scored": "",
                "mean_final_metric": "",
                "default_strategy": METHOD_LABELS[default],
                "default_strategy_count": default_n,
                "n_recognized_initial": len(recognized),
                "default_strategy_share": round(rate(default_n, len(recognized)), 4),
                "strategy_changes": total_changes,
                "changes_mechanical": sum(mechanical[cell] for cell in cells),
                "changes_adjudicated": sum(adjudicated[cell] for cell in cells),
                "recognized_pairs": total_pairs,
                "switch_rate": round(rate(total_changes, total_pairs), 4),
            }
        )

    corpus_default = sum(int(row["default_strategy_count"]) for row in rows[-3:])
    corpus_initial = sum(int(row["n_recognized_initial"]) for row in rows[-3:])
    corpus_changes = sum(int(row["strategy_changes"]) for row in rows[-3:])
    corpus_pairs = sum(int(row["recognized_pairs"]) for row in rows[-3:])
    check("corpus default count", corpus_default, PAPER_CORPUS[0])
    check("corpus recognized initial", corpus_initial, PAPER_CORPUS[1])
    check("corpus strategy changes", corpus_changes, PAPER_CORPUS[2])
    check("corpus pairs", corpus_pairs, PAPER_CORPUS[3])
    return rows


def build_partition(transitions: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Table 5.  The three dimensions partition the 74 exactly."""
    algorithm = [row for row in transitions if is_true(row["paradigm_change"])]
    data_source = [row for row in transitions if is_true(row["data_change"])]
    both = [row for row in algorithm if is_true(row["data_change"])]
    if both:
        raise AssertionError(
            f"{len(both)} pairs change two dimensions; the paper states none do"
        )
    total_pairs = len(transitions)
    counts = {
        "Training algorithm": len(algorithm),
        "Data source": len(data_source),
        "Training stages": 1,
    }
    check("algorithm changes", counts["Training algorithm"], PAPER_TABLE_5["algorithm"])
    check("data-source changes", counts["Data source"], PAPER_TABLE_5["data_source"])
    overall = sum(counts.values())
    check("overall changes", overall, PAPER_TABLE_5["overall"])

    rows = [
        {
            "changed_dimension": dimension,
            "pairs": count,
            "rate": round(rate(count, total_pairs), 4),
            "basis": basis,
        }
        for (dimension, count), basis in zip(
            counts.items(),
            (
                "mechanical, from the objective form on both sides",
                "mechanical, over the 1,401 pairs labelled on both sides",
                f"author-adjudicated: {ADJUDICATED_STAGE_CHANGE} accepted, "
                f"{REJECTED_STAGE_CANDIDATE} rejected as a restart",
            ),
        )
    ]
    rows.append(
        {
            "changed_dimension": "Overall",
            "pairs": overall,
            "rate": round(rate(overall, total_pairs), 4),
            "basis": "disjoint union; no pair changes more than one dimension",
        }
    )
    return rows


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
        help="Directory holding tables/trajectory_analysis.csv.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=HERE / "output",
        help="The released audit output; also where tables/ is written.",
    )
    args = parser.parse_args()

    trajectories, episodes, transitions = load_inputs(args.annotations, args.output)
    check("trajectories", len(trajectories), 1338)

    tables = args.output / "tables"
    check_corpus_counts(episodes, len(transitions))
    write_csv(
        tables / "framework_by_benchmark.csv",
        build_framework_by_benchmark(trajectories, transitions),
    )
    write_csv(tables / "strategy_change_partition.csv", build_partition(transitions))
    print(f"Wrote 2 tables to {tables}; all paper values reproduced.")


if __name__ == "__main__":
    main()

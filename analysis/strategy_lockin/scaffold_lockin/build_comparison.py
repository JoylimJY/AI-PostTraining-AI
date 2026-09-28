#!/usr/bin/env python3
"""Build the supplementary cross-scaffold comparison for the Pilot Study.

The canonical Pilot analysis merges full-parameter SFT and PEFT under the
same supervised-likelihood objective. This audit reuses the archived v3
method-family labels to compare update mechanisms without redefining an
objective change as a method change.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


# The matched lock-in contrast is Claude vs. Codex.  The controlled-task
# coverage tables additionally report every harness family in the corpus.
SCAFFOLDS = ("Claude", "Codex")
ALL_SCAFFOLDS = ("Claude", "Codex", "GLM-X", "OpenCode", "Qwen3Max")
PILOT_BENCHMARKS = (
    "AIME 2025",
    "ArenaHardWriting",
    "BFCL",
    "GPQA Main",
    "GSM8K",
    "HealthBench",
    "HumanEval",
)
CONTROLLED_BENCHMARKS = ("AIME 2025", "GSM8K", "HumanEval")
METHODS = ("full_sft", "peft_sft", "rl", "preference", "distillation")
METHOD_LABELS = {
    "full_sft": "Full SFT",
    "peft_sft": "LoRA/PEFT",
    "rl": "RL",
    "preference": "Preference optimization",
    "distillation": "Distillation",
}
RESOURCE_LABEL = "1x NVIDIA H100 80GB"

# --- the paper's Table 1 ---------------------------------------------------
# The tables above group by `harness_family` and score the *executed* commands
# of trajectories that trained.  Table 1 is a different quantity: it groups the
# five harness families into three agent frameworks, and its denominator is the
# 814 recognized initial strategies -- which includes trajectories that stated
# a strategy without ever launching it.  Both are reported; see
# ../README.md#two-denominators.
FRAMEWORK = {
    "Claude": "Claude Code",
    "GLM-X": "Claude Code",
    "Qwen3Max": "Claude Code",
    "Codex": "Codex CLI",
    "OpenCode": "OpenCode",
}
FRAMEWORKS = ("Claude Code", "Codex CLI", "OpenCode")
# `no_parameter_update` marks a trajectory that never trained and never stated a
# plan; `other_unknown` marks one whose state could not be resolved.  Excluding
# both is what produces the 814.
INITIAL_SENTINELS = ("no_parameter_update", "other_unknown")
# Table 1 as printed: default strategy, its count, the framework's share of the
# 814, strategy changes, and recognized pairs.
PAPER_TABLE_1 = {
    "Claude Code": ("full_sft", 166, 231, 54, 1203),
    "Codex CLI": ("peft_sft", 274, 306, 15, 943),
    "OpenCode": ("full_sft", 184, 277, 5, 1411),
}
PAPER_TABLE_1_OVERALL = (624, 814, 74, 3557)
# One of the two flagged stage-structure candidates was accepted on review; the
# mechanical pass in broad_criterion/ does not include it.
ADJUDICATED_STAGE_CHANGE = "c8fd5fbb5f110a978afb"


def parse_int(value: Any) -> int:
    if value in (None, "", "None"):
        return 0
    return int(float(value))


def parse_float(value: Any) -> float | None:
    if value in (None, "", "None"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def mean(values: Iterable[float]) -> float | None:
    values = list(values)
    return sum(values) / len(values) if values else None


def dominant(counts: Counter[str]) -> tuple[str, int]:
    if not counts:
        return "", 0
    method = max(METHODS, key=lambda item: (counts[item], -METHODS.index(item)))
    return method, counts[method]


def is_training_method_episode(episode: dict[str, Any]) -> bool:
    return (
        episode.get("executed") is True
        and "training" in episode.get("action_categories", [])
        and episode.get("method_family") in METHODS
    )


def summarize_group(
    scaffold: str,
    benchmark: str,
    rows: list[dict[str, str]],
    episodes_by_trajectory: dict[str, list[dict[str, Any]]],
    *,
    score_is_comparable: bool = True,
) -> dict[str, Any]:
    trained = [row for row in rows if parse_int(row.get("training_experiment_count")) > 0]
    identified_initial = [
        row for row in trained if row.get("initial_strategy_family") in METHODS
    ]
    initial_counts = Counter(row["initial_strategy_family"] for row in identified_initial)

    command_counts: Counter[str] = Counter()
    for row in trained:
        for episode in episodes_by_trajectory.get(row["trajectory_id"], []):
            if is_training_method_episode(episode):
                command_counts[episode["method_family"]] += 1

    dominant_initial, dominant_initial_n = dominant(initial_counts)
    dominant_command, dominant_command_n = dominant(command_counts)
    verified_commands = sum(parse_int(row.get("training_experiment_count")) for row in trained)
    identified_commands = sum(command_counts.values())
    valid_pairs = sum(parse_int(row.get("valid_objective_pair_count")) for row in trained)
    objective_switches = sum(parse_int(row.get("objective_change_count")) for row in trained)
    trajectories_with_switch = sum(
        parse_int(row.get("objective_change_count")) > 0 for row in trained
    )
    final_scores = [
        score
        for row in trained
        if (score := parse_float(row.get("final_metric"))) is not None
    ]
    best_scores = [
        score
        for row in trained
        if (score := parse_float(row.get("best_metric"))) is not None
    ]
    base_models = sorted({row.get("base_model", "") for row in rows if row.get("base_model")})
    budgets = sorted(
        {
            value
            for row in rows
            if (value := parse_float(row.get("budget_hours"))) is not None
        }
    )

    result: dict[str, Any] = {
        "scaffold": scaffold,
        "benchmark": benchmark,
        "base_model_count": len(base_models),
        "base_models": "; ".join(base_models),
        "budget_hours": budgets[0] if len(budgets) == 1 else "mixed",
        "resource": RESOURCE_LABEL,
        "n_trajectories": len(rows),
        "n_trained_trajectories": len(trained),
        "n_initial_method_identified": len(identified_initial),
        "initial_method_identification_coverage": safe_rate(
            len(identified_initial), len(trained)
        ),
        "dominant_initial_method": dominant_initial,
        "dominant_initial_method_count": dominant_initial_n,
        "dominant_initial_method_share_among_identified": safe_rate(
            dominant_initial_n, len(identified_initial)
        ),
        "verified_training_commands": verified_commands,
        "n_training_commands_method_identified": identified_commands,
        "training_command_method_identification_coverage": safe_rate(
            identified_commands, verified_commands
        ),
        "dominant_training_command_method": dominant_command,
        "dominant_training_command_count": dominant_command_n,
        "dominant_training_command_share_among_identified": safe_rate(
            dominant_command_n, identified_commands
        ),
        "objective_switches": objective_switches,
        "valid_objective_pairs": valid_pairs,
        "objective_switch_rate": safe_rate(objective_switches, valid_pairs),
        "n_trajectories_with_objective_switch": trajectories_with_switch,
        "n_final_scores": len(final_scores) if score_is_comparable else "",
        "mean_final_score": mean(final_scores) if score_is_comparable else "",
        "mean_best_score": mean(best_scores) if score_is_comparable else "",
        "score_scope": (
            "trained trajectories with a valid final metric; compare within benchmark only"
            if score_is_comparable
            else "not pooled across benchmarks"
        ),
        "mean_training_commands_per_trained_trajectory": safe_rate(
            verified_commands, len(trained)
        ),
        "mean_evaluation_commands_per_trained_trajectory": safe_rate(
            sum(parse_int(row.get("evaluation_count")) for row in trained), len(trained)
        ),
    }
    for method in METHODS:
        result[f"initial_{method}_count"] = initial_counts[method]
        result[f"command_{method}_count"] = command_counts[method]
    return result


def build_cell_consistency(
    trajectories: list[dict[str, str]],
    benchmarks: tuple[str, ...],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for benchmark in benchmarks:
        base_models = sorted(
            {
                row["base_model"]
                for row in trajectories
                if row["benchmark"] == benchmark
            }
        )
        for base_model in base_models:
            cell: dict[str, Any] = {
                "benchmark": benchmark,
                "base_model": base_model,
            }
            rates: dict[tuple[str, str], float | None] = {}
            for scaffold in SCAFFOLDS:
                selected = [
                    row
                    for row in trajectories
                    if row["benchmark"] == benchmark
                    and row["base_model"] == base_model
                    and row["harness_family"] == scaffold
                    and parse_int(row.get("training_experiment_count")) > 0
                    and row.get("initial_strategy_family") in METHODS
                ]
                counts = Counter(row["initial_strategy_family"] for row in selected)
                for method in ("full_sft", "peft_sft"):
                    rates[(scaffold, method)] = safe_rate(counts[method], len(selected))
                    cell[f"{scaffold.lower()}_{method}_count"] = counts[method]
                    cell[f"{scaffold.lower()}_{method}_share"] = rates[(scaffold, method)]
                cell[f"{scaffold.lower()}_identified_initial_n"] = len(selected)

            claude_full = rates[("Claude", "full_sft")]
            codex_full = rates[("Codex", "full_sft")]
            claude_peft = rates[("Claude", "peft_sft")]
            codex_peft = rates[("Codex", "peft_sft")]
            cell["claude_more_full_sft"] = (
                claude_full is not None and codex_full is not None and claude_full > codex_full
            )
            cell["codex_more_peft"] = (
                claude_peft is not None and codex_peft is not None and codex_peft > claude_peft
            )
            cell["full_sft_share_gap_claude_minus_codex"] = (
                claude_full - codex_full
                if claude_full is not None and codex_full is not None
                else None
            )
            cell["peft_share_gap_codex_minus_claude"] = (
                codex_peft - claude_peft
                if claude_peft is not None and codex_peft is not None
                else None
            )
            rows.append(cell)
    return rows


def build_framework_lockin(
    trajectories: list[dict[str, str]],
    transitions: list[dict[str, str]] | None,
) -> list[dict[str, Any]]:
    """Table 1: default-strategy concentration and switch rate per framework.

    `kappa` is computed over the recognized initial strategies, *not* over the
    trajectories that trained -- an agent that commits to a strategy and then
    fails to execute it has still made the strategy-level decision, and dropping
    those runs would bias the concentration toward the agents that get further.

    The switch-rate columns are filled only when the broad-criterion transition
    table is available; it ships with the repository, so the default path
    resolves in a checkout.
    """
    rows: list[dict[str, Any]] = []
    framework_of = {
        row["trajectory_id"]: FRAMEWORK[row["harness_family"]] for row in trajectories
    }
    pairs: Counter[str] = Counter()
    changes: Counter[str] = Counter()
    if transitions is not None:
        for row in transitions:
            framework = framework_of[row["trajectory_id"]]
            pairs[framework] += 1
            if row["broad_change_mechanical"] in ("1", "True", "true"):
                changes[framework] += 1
        changes[framework_of[ADJUDICATED_STAGE_CHANGE]] += 1

    def recognized_initial(framework: str) -> list[dict[str, str]]:
        return [
            row
            for row in trajectories
            if framework_of[row["trajectory_id"]] == framework
            and row["initial_strategy_family"] in METHODS
        ]

    for framework in FRAMEWORKS + ("Overall",):
        if framework == "Overall":
            selected = trajectories
            recognized = [row for name in FRAMEWORKS for row in recognized_initial(name)]
            # kappa pools each agent's own modal mass.  Taking the corpus mode
            # instead would hide that the two defaults differ, which is the
            # finding.
            default = "per-agent modal strategy"
            default_n = sum(
                Counter(
                    row["initial_strategy_family"] for row in recognized_initial(name)
                ).most_common(1)[0][1]
                for name in FRAMEWORKS
            )
        else:
            selected = [
                row for row in trajectories if framework_of[row["trajectory_id"]] == framework
            ]
            recognized = recognized_initial(framework)
            counts = Counter(row["initial_strategy_family"] for row in recognized)
            default, default_n = counts.most_common(1)[0]
        n_pairs = sum(pairs.values()) if framework == "Overall" else pairs[framework]
        n_changes = sum(changes.values()) if framework == "Overall" else changes[framework]

        expected = (
            PAPER_TABLE_1_OVERALL
            if framework == "Overall"
            else PAPER_TABLE_1[framework][1:]
        )
        observed = (default_n, len(recognized), n_changes, n_pairs)
        if transitions is None:
            expected, observed = expected[:2], observed[:2]
        if observed != tuple(expected):
            raise ValueError(
                f"Table 1 mismatch for {framework}: recomputed {observed}, "
                f"paper reports {tuple(expected)}"
            )

        rows.append(
            {
                "agent_framework": framework,
                "n_trajectories": len(selected),
                "n_recognized_initial": len(recognized),
                "default_strategy": METHOD_LABELS.get(default, default),
                "default_strategy_count": default_n,
                "kappa": safe_rate(default_n, len(recognized)),
                "strategy_changes": n_changes if transitions is not None else "",
                "recognized_pairs": n_pairs if transitions is not None else "",
                "rho": safe_rate(n_changes, n_pairs) if transitions is not None else "",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows generated for {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def pct(value: Any) -> str:
    if value in (None, ""):
        return "--"
    return f"{100 * float(value):.1f}%"


def score(value: Any) -> str:
    if value in (None, ""):
        return "--"
    return f"{float(value):.3f}"


def method_with_share(row: dict[str, Any], prefix: str) -> str:
    method = row[f"dominant_{prefix}_method"]
    share_key = (
        "dominant_initial_method_share_among_identified"
        if prefix == "initial"
        else "dominant_training_command_share_among_identified"
    )
    share = row[share_key]
    return f"{METHOD_LABELS.get(method, method)} ({pct(share)})"


def build_report(
    comparison: list[dict[str, Any]],
    aggregate: list[dict[str, Any]],
    cells: list[dict[str, Any]],
    detailed_cells: list[dict[str, Any]],
) -> str:
    by_scaffold = {row["scaffold"]: row for row in aggregate}
    claude = by_scaffold["Claude"]
    codex = by_scaffold["Codex"]
    n_full_direction = sum(bool(row["claude_more_full_sft"]) for row in cells)
    n_peft_direction = sum(bool(row["codex_more_peft"]) for row in cells)
    mean_full_gap = mean(
        float(row["full_sft_share_gap_claude_minus_codex"]) for row in cells
    )
    mean_peft_gap = mean(
        float(row["peft_share_gap_codex_minus_claude"]) for row in cells
    )
    qwen_cells = [
        row
        for row in detailed_cells
        if row["base_model"] == "Qwen3-1.7B-Base"
    ]
    qwen_command_totals = {
        scaffold: sum(
            int(row["n_training_commands_method_identified"])
            for row in qwen_cells
            if row["scaffold"] == scaffold
        )
        for scaffold in SCAFFOLDS
    }
    qwen_method_totals = {
        "Claude": sum(
            int(row["command_full_sft_count"])
            for row in qwen_cells
            if row["scaffold"] == "Claude"
        ),
        "Codex": sum(
            int(row["command_peft_sft_count"])
            for row in qwen_cells
            if row["scaffold"] == "Codex"
        ),
    }

    lines = [
        "# Pilot Study: cross-scaffold method audit",
        "",
        "## Core finding",
        "",
        (
            "Across all seven shared benchmarks, all four shared base models, and the "
            "same 10-hour single-H100 budget, the two scaffolds do not converge on the "
            "same supervised fine-tuning implementation."
        ),
        (
            f"Among Claude's identifiable initial methods, Full SFT accounts for "
            f"{claude['initial_full_sft_count']}/{claude['n_initial_method_identified']} "
            f"({pct(safe_rate(claude['initial_full_sft_count'], claude['n_initial_method_identified']))}); "
            f"among Codex's identifiable initial methods, LoRA/PEFT accounts for "
            f"{codex['initial_peft_sft_count']}/{codex['n_initial_method_identified']} "
            f"({pct(safe_rate(codex['initial_peft_sft_count'], codex['n_initial_method_identified']))})."
        ),
        (
            f"The direction is consistent: in {n_full_direction}/{len(cells)} matched cells "
            f"Claude leans towards Full SFT, and in {n_peft_direction}/{len(cells)} cells "
            f"Codex leans towards PEFT; the mean gaps are "
            f"{100 * mean_full_gap:.1f} and {100 * mean_peft_gap:.1f} percentage points respectively."
        ),
        (
            f"In the Qwen3-1.7B-Base slice, the one closest to our controlled baseline, "
            f"Claude's Full SFT commands are "
            f"{qwen_method_totals['Claude']}/{qwen_command_totals['Claude']} "
            f"({pct(safe_rate(qwen_method_totals['Claude'], qwen_command_totals['Claude']))}), "
            f"and Codex's PEFT commands are {qwen_method_totals['Codex']}/{qwen_command_totals['Codex']} "
            f"({pct(safe_rate(qwen_method_totals['Codex'], qwen_command_totals['Codex']))})."
        ),
        "",
        "## Cross-scaffold comparison",
        "",
        (
            "| Scaffold | Benchmark | Final accuracy (n) | Dominant initial method | "
            "Initial label coverage | Method-labelled training commands | "
            "Dominant command method | Objective switches |"
        ),
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in comparison:
        lines.append(
            "| {scaffold} | {benchmark} | {score} ({n_score}) | {initial} | "
            "{initial_coverage} | {known}/{total} ({coverage}) | {command} | "
            "{switches}/{pairs} ({switch_rate}) |".format(
                scaffold=row["scaffold"],
                benchmark=row["benchmark"],
                score=score(row["mean_final_score"]),
                n_score=row["n_final_scores"],
                initial=method_with_share(row, "initial"),
                initial_coverage=pct(row["initial_method_identification_coverage"]),
                known=row["n_training_commands_method_identified"],
                total=row["verified_training_commands"],
                coverage=pct(row["training_command_method_identification_coverage"]),
                command=method_with_share(row, "training_command"),
                switches=row["objective_switches"],
                pairs=row["valid_objective_pairs"],
                switch_rate=pct(row["objective_switch_rate"]),
            )
        )
    lines.extend(
        [
            "",
            "Final accuracy is the mean over trajectories that trained and produced a valid "
            "final accuracy. It is interpretable only within a benchmark: it is not aggregated "
            "across benchmarks and is not a causal estimate of the scaffold's effect. The "
            "denominator of the dominant-method share is the set of identifiable methods, so the "
            "table also reports method-labelled commands / verified training commands coverage.",
            "",
            "## Interpretation",
            "",
            "The result separates two layers. At the objective layer both scaffolds concentrate "
            "heavily on supervised likelihood; at the update-mechanism layer they concentrate on "
            "Full SFT and LoRA/PEFT respectively. If task demand alone determined the reasonable "
            "strategy, matched task cells should push both scaffolds towards the same implementation "
            "mechanism. The stable opposing preferences we observe are therefore not consistent with "
            "that simple account, and are better predicted by scaffold-specific priors or default "
            "tooling habits.",
            "",
            "This evidence remains observational rather than causally identified: agent model, "
            "interface, prompt and scaffold are not independently randomised, and the method labels "
            "do not cover every training command. The conclusion should be stated as `inconsistent "
            "with a task-demand-only account` or `suggestive of scaffold-specific priors`, not as "
            "`proves scaffold causality`.",
            "",
            "## Measurement layers",
            "",
            "- `Dominant initial method`: the first identifiable method-family label in each trajectory that trained.",
            "- `Dominant command method`: training episodes that contain a training action and whose method family is identifiable.",
            "- `Objective switches`: switches between adjacent identified experiments at the canonical objective layer. Full SFT and PEFT are both supervised likelihood, so swapping one for the other is not an objective switch.",
            "- `Final accuracy`: the mean over trajectories that trained and produced a valid final accuracy, reported per benchmark.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pilot-root",
        type=Path,
        default=Path("analysis/annotations/strategy_level"),
        help="Directory holding trajectory_analysis.csv and episode_annotations.jsonl.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("analysis/strategy_lockin/scaffold_lockin/output"),
        help="Output directory for supplementary tables and report.",
    )
    parser.add_argument(
        "--broad-transitions",
        type=Path,
        default=Path(
            "analysis/strategy_lockin/broad_criterion/output/broad_transitions.csv"
        ),
        help=(
            "Released broad-criterion pair table, used for Table 1's switch-rate "
            "columns. Those columns are left empty if it is absent."
        ),
    )
    args = parser.parse_args()

    trajectory_path = args.pilot_root / "tables" / "trajectory_analysis.csv"
    episode_path = args.pilot_root / "episode_annotations.jsonl"
    if not episode_path.exists():  # layout of a locally regenerated pilot run
        episode_path = args.pilot_root / "annotations" / "episode_annotations.jsonl"
    with trajectory_path.open(newline="", encoding="utf-8") as handle:
        trajectories = list(csv.DictReader(handle))
    with episode_path.open(encoding="utf-8") as handle:
        episodes = [json.loads(line) for line in handle if line.strip()]

    episodes_by_trajectory: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for episode in episodes:
        episodes_by_trajectory[episode["trajectory_id"]].append(episode)

    observed_benchmarks = {row["benchmark"] for row in trajectories}
    if observed_benchmarks != set(PILOT_BENCHMARKS):
        raise ValueError(
            "Pilot benchmark mismatch: "
            f"expected {sorted(PILOT_BENCHMARKS)}, observed {sorted(observed_benchmarks)}"
        )
    comparison: list[dict[str, Any]] = []
    for scaffold in SCAFFOLDS:
        for benchmark in PILOT_BENCHMARKS:
            selected = [
                row
                for row in trajectories
                if row["harness_family"] == scaffold and row["benchmark"] == benchmark
            ]
            comparison.append(
                summarize_group(
                    scaffold,
                    benchmark,
                    selected,
                    episodes_by_trajectory,
                )
            )

    aggregate: list[dict[str, Any]] = []
    for scaffold in ALL_SCAFFOLDS:
        selected = [
            row
            for row in trajectories
            if row["harness_family"] == scaffold
            and row["benchmark"] in PILOT_BENCHMARKS
        ]
        aggregate.append(
            summarize_group(
                scaffold,
                "All seven Pilot benchmarks",
                selected,
                episodes_by_trajectory,
                score_is_comparable=False,
            )
        )

    controlled_aggregate: list[dict[str, Any]] = []
    for scaffold in ALL_SCAFFOLDS:
        selected = [
            row
            for row in trajectories
            if row["harness_family"] == scaffold
            and row["benchmark"] in CONTROLLED_BENCHMARKS
        ]
        controlled_aggregate.append(
            summarize_group(
                scaffold,
                "AIME 2025 + GSM8K + HumanEval",
                selected,
                episodes_by_trajectory,
                score_is_comparable=False,
            )
        )

    cells = build_cell_consistency(trajectories, PILOT_BENCHMARKS)
    controlled_cells = build_cell_consistency(trajectories, CONTROLLED_BENCHMARKS)
    detailed_cells: list[dict[str, Any]] = []
    for benchmark in PILOT_BENCHMARKS:
        for base_model in sorted(
            {
                row["base_model"]
                for row in trajectories
                if row["benchmark"] == benchmark
            }
        ):
            for scaffold in ALL_SCAFFOLDS:
                selected = [
                    row
                    for row in trajectories
                    if row["harness_family"] == scaffold
                    and row["benchmark"] == benchmark
                    and row["base_model"] == base_model
                ]
                row = summarize_group(
                    scaffold,
                    benchmark,
                    selected,
                    episodes_by_trajectory,
                )
                row["base_model"] = base_model
                detailed_cells.append(row)
    controlled_detailed_cells: list[dict[str, Any]] = []
    for benchmark in CONTROLLED_BENCHMARKS:
        for base_model in sorted(
            {
                row["base_model"]
                for row in trajectories
                if row["benchmark"] == benchmark
            }
        ):
            for scaffold in ALL_SCAFFOLDS:
                selected = [
                    row
                    for row in trajectories
                    if row["harness_family"] == scaffold
                    and row["benchmark"] == benchmark
                    and row["base_model"] == base_model
                ]
                row = summarize_group(
                    scaffold,
                    benchmark,
                    selected,
                    episodes_by_trajectory,
                )
                row["base_model"] = base_model
                controlled_detailed_cells.append(row)
    transitions: list[dict[str, str]] | None = None
    if args.broad_transitions.exists():
        with args.broad_transitions.open(newline="", encoding="utf-8") as handle:
            transitions = list(csv.DictReader(handle))
    write_csv(
        args.output / "tables" / "framework_lockin.csv",
        build_framework_lockin(trajectories, transitions),
    )
    write_csv(args.output / "tables" / "cross_scaffold_comparison.csv", comparison)
    write_csv(args.output / "tables" / "all_seven_task_summary.csv", aggregate)
    write_csv(args.output / "tables" / "all_cell_consistency.csv", cells)
    write_csv(
        args.output / "tables" / "all_seven_task_by_base_model.csv",
        detailed_cells,
    )
    write_csv(
        args.output / "tables" / "matched_three_task_summary.csv",
        controlled_aggregate,
    )
    write_csv(
        args.output / "tables" / "matched_cell_consistency.csv",
        controlled_cells,
    )
    write_csv(
        args.output / "tables" / "matched_three_task_by_base_model.csv",
        controlled_detailed_cells,
    )
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.md").write_text(
        build_report(comparison, aggregate, cells, detailed_cells), encoding="utf-8"
    )


if __name__ == "__main__":
    main()

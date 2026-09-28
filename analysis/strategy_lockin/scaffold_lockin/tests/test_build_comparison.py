import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "build_comparison.py"
SPEC = importlib.util.spec_from_file_location("build_comparison", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ScaffoldComparisonTest(unittest.TestCase):
    def test_summary_uses_identified_denominators_and_objective_switches(self):
        trajectories = [
            {
                "trajectory_id": "a",
                "training_experiment_count": "2",
                "initial_strategy_family": "full_sft",
                "valid_objective_pair_count": "1",
                "objective_change_count": "0",
                "final_metric": "0.5",
                "best_metric": "0.6",
                "base_model": "m1",
                "budget_hours": "10",
                "evaluation_count": "3",
            },
            {
                "trajectory_id": "b",
                "training_experiment_count": "3",
                "initial_strategy_family": "other_unknown",
                "valid_objective_pair_count": "2",
                "objective_change_count": "1",
                "final_metric": "",
                "best_metric": "",
                "base_model": "m1",
                "budget_hours": "10",
                "evaluation_count": "2",
            },
        ]
        episodes = {
            "a": [
                {
                    "executed": True,
                    "action_categories": ["training"],
                    "method_family": "full_sft",
                },
                {
                    "executed": True,
                    "action_categories": ["evaluation"],
                    "method_family": "peft_sft",
                },
            ],
            "b": [
                {
                    "executed": True,
                    "action_categories": ["training"],
                    "method_family": "other_unknown",
                }
            ],
        }

        result = MODULE.summarize_group(
            "Claude", "GSM8K", trajectories, episodes
        )

        self.assertEqual(result["n_trained_trajectories"], 2)
        self.assertEqual(result["n_initial_method_identified"], 1)
        self.assertEqual(result["dominant_initial_method_share_among_identified"], 1.0)
        self.assertEqual(result["verified_training_commands"], 5)
        self.assertEqual(result["n_training_commands_method_identified"], 1)
        self.assertEqual(result["objective_switches"], 1)
        self.assertEqual(result["valid_objective_pairs"], 3)
        self.assertEqual(result["mean_final_score"], 0.5)


class FrameworkLockinTest(unittest.TestCase):
    """Table 1 reproduces from the released annotations, or fails loudly."""

    ANNOTATIONS = (
        Path(__file__).parents[3]
        / "annotations"
        / "strategy_level"
        / "tables"
        / "trajectory_analysis.csv"
    )
    TRANSITIONS = (
        Path(__file__).parents[2]
        / "broad_criterion"
        / "output"
        / "broad_transitions.csv"
    )

    def _load(self):
        import csv

        with self.ANNOTATIONS.open(newline="", encoding="utf-8") as handle:
            trajectories = list(csv.DictReader(handle))
        with self.TRANSITIONS.open(newline="", encoding="utf-8") as handle:
            transitions = list(csv.DictReader(handle))
        return trajectories, transitions

    def test_reproduces_paper_table_1(self):
        trajectories, transitions = self._load()
        rows = {
            row["agent_framework"]: row
            for row in MODULE.build_framework_lockin(trajectories, transitions)
        }

        self.assertEqual(rows["Claude Code"]["default_strategy_count"], 166)
        self.assertEqual(rows["Claude Code"]["n_recognized_initial"], 231)
        self.assertEqual(rows["Codex CLI"]["default_strategy"], "LoRA/PEFT")
        self.assertEqual(rows["Codex CLI"]["default_strategy_count"], 274)
        self.assertEqual(rows["OpenCode"]["default_strategy_count"], 184)
        self.assertEqual(rows["Overall"]["n_recognized_initial"], 814)
        self.assertEqual(rows["Overall"]["default_strategy_count"], 624)
        self.assertEqual(rows["Overall"]["strategy_changes"], 74)
        self.assertEqual(rows["Overall"]["recognized_pairs"], 3557)
        for framework, kappa in (
            ("Claude Code", 0.719),
            ("Codex CLI", 0.895),
            ("OpenCode", 0.664),
            ("Overall", 0.767),
        ):
            self.assertAlmostEqual(rows[framework]["kappa"], kappa, places=3)

    def test_switch_columns_are_optional(self):
        trajectories, _ = self._load()
        rows = MODULE.build_framework_lockin(trajectories, None)
        self.assertTrue(all(row["rho"] == "" for row in rows))
        self.assertEqual(rows[-1]["n_recognized_initial"], 814)

    def test_drift_in_the_annotations_fails(self):
        trajectories, transitions = self._load()
        mutated = [dict(row) for row in trajectories]
        for row in mutated:
            if row["initial_strategy_family"] == "full_sft":
                row["initial_strategy_family"] = "rl"
                break
        with self.assertRaises(ValueError):
            MODULE.build_framework_lockin(mutated, transitions)


if __name__ == "__main__":
    unittest.main()

# Pilot Study v3: objective-level annotation

This directory contains the full-corpus measurement layer for the Pilot Study.
The canonical strategy label is the optimization objective used by an
executed parameter-update experiment. Full-parameter and parameter-efficient
supervised training share one label. Data construction, hyperparameter
tuning, debugging, evaluation, and checkpoint operations do not constitute a
strategy change.

Run from the repository root:

```bash
python analysis/pilot_study/run_pilot.py \
  --input data/PostTrainBench-Trajectories \
  --output analysis/pilot_study \
  --config analysis/pilot_study/config.json
```

The parser keeps every task-level trajectory, including duplicate directories,
failed runs, missing metrics, and unavailable traces. A training launch must
have a command-boundary training script or an explicit update call. Inspection,
installation, data preparation, testing, process control, and checkpoint merge
commands are excluded.

Objective evidence is read from the executed training script whenever possible.
The labels are `supervised_likelihood`, `reward_optimization`,
`preference_optimization`, `on_policy_distillation`, and
`objective_unknown`. Later strategy statistics count a change only where both
objective forms are known; `objective_unknown` is never imputed to a class. A
proposed or unexecuted change is not counted.

The output files that define the current annotation are:

- `intermediate/experiment_episodes.jsonl` and `intermediate/objective_states.jsonl`;
- `intermediate/objective_transitions.csv`;
- `tables/trajectory_analysis.csv`;
- `tables/rq1_initial_strategy.csv`;
- `tables/rq2_online_development.csv`;
- `tables/rq4_outcome_by_strategy.csv`;
- `annotations/consistency_check_log.jsonl`.

The superseded family-level plotting code and ambiguous `strategy_*`
compatibility aliases have been removed. Use the explicit `objective_*` paths
above for objective-family measurements; the broader data-source and stage
audit lives in `analysis/strategy_lockin/broad_criterion/`.

Run the focused tests with:

```bash
python -m unittest discover -s analysis/pilot_study/tests -v
```

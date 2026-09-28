# Strategy Lock-In

Three audits that test whether the low objective-change rate measured by the
main annotation pass is an artifact of a narrow definition, whether the
individual changes survive being read one by one, and whether the strategy an
agent commits to is explained by the task or by the agent's own priors.

## `broad_criterion/`

Widens the definition of a strategy change from *training algorithm only* to
*algorithm ∪ data source ∪ stage structure* — that is, from `p` alone to any
component of `s = (p, d, g)` — over the same denominator of 3,557 recognized
adjacent experiment pairs.

Result: 2.05% (73/3,557) under the broad criterion versus 0.98% (35/3,557)
under the algorithm criterion. Widening the definition roughly doubles the rate
and leaves the conclusion intact. The paper reports 74/3,557 (2.08%); the extra
change is one adjudicated stage-structure candidate, explained in
[`../../docs/annotation-protocol.md`](../../docs/annotation-protocol.md#reconciling-73-vs-74).

See [`broad_criterion/report.md`](broad_criterion/report.md), which also records
the two earlier rule sets that were tried and rejected, and why.

`broad_criterion/build_paper_tables.py` derives two of the tables the paper
prints from that pass, and asserts each printed figure rather than recomputing
it silently:

| Table | What it settles |
|---|---|
| [`output/tables/strategy_change_partition.csv`](broad_criterion/output/tables/strategy_change_partition.csv) | the 74 changes split 35 / 38 / 1 across `p`, `d`, `g`, and which two stage candidates were adjudicated |
| [`output/tables/framework_by_benchmark.csv`](broad_criterion/output/tables/framework_by_benchmark.csv) | default strategy and switch rate per framework × benchmark, including Claude Code's 10.6% on AIME 2025 and 0% on BFCL |

## `algorithm_audit/`

Narrows the criterion the other way, to training algorithm alone, and reads the
result by hand: **16** trajectories ever change algorithm, over **35**
transitions. The point of the audit is that the 35 overstate exploration — 15 of
them return to SFT, 11 of the 16 oscillate, and the median first switch lands at
0.40 of the way through the run. It also rebuilds the five trace-level case
studies of Table 6.

See [`algorithm_audit/README.md`](algorithm_audit/README.md).

## `scaffold_lockin/`

Holds benchmark, base model, and compute budget fixed and varies only the
scaffold. If task demand alone determined the reasonable strategy, matched cells
should push different scaffolds towards the same implementation.

Result: they do not. The paper's default-strategy concentrations `κ_a`, over
the 814 trajectories with a recognized initial strategy and the three-framework
grouping, are:

| Agent framework (#Traj.) | Default strategy | `κ_a` |
|---|---|---:|
| Claude Code (575) | Full SFT | 166 / 231 = **71.9%** |
| Codex CLI (369) | PEFT | 274 / 306 = **89.5%** |
| OpenCode (394) | Full SFT | 184 / 277 = **66.4%** |
| Overall (1,338) | — | 624 / 814 = **76.7%** |

That is Table 1, rebuilt by `build_comparison.py` into
[`scaffold_lockin/output/tables/framework_lockin.csv`](scaffold_lockin/output/tables/framework_lockin.csv),
which carries `κ_a` and `ρ_a` in the same row so the two halves of the claim —
agents agree on an opening, then do not revise it — are read off one table.

The direction holds in all 28 matched cells: Claude Code has the higher full-SFT
share and Codex CLI the higher PEFT share in every benchmark × base-model
combination. All three frameworks nonetheless concentrate on
`supervised_likelihood` at the objective layer — the divergence is at the
update-mechanism layer.

The checked-in [`scaffold_lockin/output/report.md`](scaffold_lockin/output/report.md)
is the **earlier two-scaffold pass** and reports 163/202 (80.7%) for Claude and
268/299 (89.6%) for Codex. Those are not the same quantity as `κ_a`: the
denominator there is initial methods identifiable from executed training
commands under the five raw harness families, whereas `κ_a` is computed over
the 814 recognized initial strategies under the three-framework grouping, and
includes trajectories that state a planned strategy without launching training.
The report is released as it ran rather than retroactively recomputed.

All three audits are **observational**. Agent model, interface, prompt and
scaffold are not independently randomised, and method labels do not cover every
training command. The reports state the admissible claim explicitly.

## Running them

Only the first step needs the pipeline's `intermediate/` tree, which is not
redistributed (~2 GB); regenerate it with `analysis/pilot_study/run_pilot.py`
first:

```bash
python analysis/strategy_lockin/broad_criterion/build_broad_transitions.py
```

The remaining three read released files only — the annotation tables and the
`output/` of the step above — so they run against this repository as cloned:

```bash
python analysis/strategy_lockin/broad_criterion/build_paper_tables.py
python analysis/strategy_lockin/algorithm_audit/build_algorithm_audit.py
python analysis/strategy_lockin/scaffold_lockin/build_comparison.py
```

The `output/` directories in this repository hold the results of the runs the
paper reports.

Tests: `python -m unittest discover -s analysis/strategy_lockin/scaffold_lockin/tests -v`

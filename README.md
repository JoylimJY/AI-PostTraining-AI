# What is Missing from AI Post-Training AI: An Empirical Analysis

<div align="center">

[![License](https://img.shields.io/badge/License-MIT-red.svg)](LICENSE)

</div>

Code and data for **What is Missing from AI Post-Training AI: An Empirical Analysis**.

## Overview

We give coding agents a base language model, a benchmark, one GPU, and ten hours, and ask them to
post-train the model. Repeating this 1,338 times, we find that agents are strong *executors* and
weak *strategists*.

The paper separates two capabilities that discussions of AI-for-AI tend to conflate:

- **Execution level** — iterating inside a selected strategy: constructing data, tuning
  hyperparameters, shaping rewards, selecting checkpoints, debugging the implementation.
- **Strategy level** — revising the high-level judgment itself: switching the training paradigm,
  adding or removing a stage, redirecting the remaining budget.

Agents configure trainers, fit models onto a single card, and recover from crashes reliably. But
the strategy they commit to — training paradigm, data source, stage structure — is fixed in the
planning phase, before any code is written or any experiment is run, and is almost never revised
afterwards, even when the agent's own recorded evidence says it should be. We call this **strategy
lock-in**.

The analyzed trajectories are publicly released PostTrainBench runs, spanning seven benchmarks,
four base models, and five agent scaffolds; the controlled experiments are our own. This
repository contains the harness that ran them, the annotations behind the paper's numbers, and ten
archived agent runs covering all three conditions.

## Findings

**Agents are competent executors.** A trajectory averages 3.8 training runs and 13.8 evaluations.
Nearly every agent completes the pipeline from data preparation through training, evaluation, and
checkpoint submission, and every benchmark shows an average gain over the base model. The repairs
are technically meaningful — realigning generation templates, concentrating a data mixture on the
target format, fixing EOS handling — so execution is not the binding constraint.

**The strategy tracks the agent, not the task.** 80.7% of Claude Code trajectories anchor on
full-parameter SFT; 89.6% of Codex CLI trajectories anchor on parameter-efficient fine-tuning —
on the same tasks, under the same budget. Once training starts, the budget is spent inside that
choice: 2.1% of adjacent training pairs ever probe an alternative, and the rest are denser local
search over learning rates, data mixtures, and chat templates.

**Neither experience, guidance, nor reasoning compute reopens the choice.**

| Intervention | Effect on execution | Effect on strategy |
| --- | --- | --- |
| Experience-driven framework | +12.6 on GSM8K, +40.8 on HumanEval | unchanged — the agent adopts every execution-level suggestion the evaluator makes, and none of the strategy-level ones |
| Human review of the plan before training | starting strategy is redirected, and the agent extends it on its own initiative | the run falls back into local adjustment once training begins |
| Several times the inference tokens | large gains on the easier benchmarks | no gain on the hardest one |

The strategy is plastic only within a short window before the first training run. Once that window
closes, the same channels stop working. What is missing is not a resource but a mechanism for
spontaneously reopening a committed choice during execution.

## Controlled Experiments

Qwen3-1.7B-Base on three benchmarks of increasing difficulty, ten hours per run on four A800 GPUs,
three independent runs per configuration, with the system prompt, base model, hardware, and
evaluation protocol held fixed within each comparison. Scores are pass@1, except AIME 2025, which
has only 30 problems and is scored pass@8.

| Setting | GSM8K | HumanEval | AIME 2025 |
| --- | --- | --- | --- |
| Base model | 10.84% | 5.48% | 0.00% |
| Autonomous — Claude Code (Opus 4.6) | 64.70% | 22.00% | 3.33% |
| Autonomous — Codex CLI (GPT-5.2) | 43.44% | 13.41% | 0.00% |
| Experience-driven framework | **77.30%** | **62.80%** | **5.56%** |

Mean over three runs. Human guidance is evaluated on AIME 2025 only, where its best run reaches
13.33% pass@8; since a one-problem difference on AIME lies within evaluation variance, that column
is read qualitatively, alongside the trajectories.

## Repository Structure

```
├── framework/       the experience-driven scaffold
│   ├── journal/       experiment journal: plan / lesson / reflection schemas
│   ├── evaluator/     evaluator agent: predict → evaluate → analyze
│   └── skills/        agent-authored skills, and the reference wiki they draw on
├── experiments/     agent prompts, configs, and launchers, per benchmark
├── evaluation/      AIME 2025 / GSM8K / HumanEval scoring harnesses
├── analysis/        trajectory parsing pipeline, lock-in analyses, and the annotations
├── trajectories/    ten agent runs: framework, baseline, and human-guided
└── docs/            framework design, annotation protocol, metric definitions
```

Each directory has its own `README.md`.

The scaffold's three components map onto the first three subdirectories. The **experiment journal**
persists plans, results, observations, and lessons across iterations, so evidence from an early
experiment survives into a later decision. The **skill library** distills recipes, configurations,
and known failure modes from widely used training frameworks into references the agent consults
while building and debugging its pipeline. The **evaluator agent** runs whenever the main agent
requests an evaluation: it forms an expectation, invokes the original scoring script, inspects both
the scores and the model outputs, and returns a diagnosis with concrete suggestions — which the
main agent is free to ignore, and at the strategy level does.

## Installation

```bash
git clone --recurse-submodules <repository-url>
cd AI-PostTraining-AI
pip install -r requirements.txt
```

The analysis code runs on the standard library alone. The pinned versions matter for the training
and evaluation harnesses, where `torch` and `vllm` may need to be matched to your CUDA stack.

The submodules pin the upstream post-training libraries the agents read from, at the commits they
actually saw. They are only needed to regenerate the wiki source pages — drop
`--recurse-submodules` to skip them.

## Usage

Reproduce the lock-in numbers from the released annotations:

```bash
python analysis/strategy_lockin/scaffold_lockin/build_comparison.py
```

The broader data-source and stage audit
(`analysis/strategy_lockin/broad_criterion/build_broad_transitions.py`) additionally reads the
pipeline's `intermediate/` tree, which is too large to redistribute; regenerate it first with
`analysis/pilot_study/run_pilot.py`.

Read a trajectory the way the analysis does:

```python
from pathlib import Path
from analysis.pipeline.parse_claude import parse_claude_records

records, stats = parse_claude_records(
    Path("trajectories/experience_aime2025_c247e78e/trajectory.jsonl").read_text()
)
```

For the decision-level view, read `experiment.jsonl` in the same directory instead — it holds the
agent's own account of what it planned, what it expected, and what it concluded.

Re-running the full extraction (`python -m analysis.pipeline.run_pipeline --config
analysis/pipeline/config.json`) requires the raw logs, which are terabyte-scale and not released.
The ten included runs are complete enough to exercise every parser on real input; they cover
both stream formats the pipeline handles.

## Data

`analysis/annotations/` holds two independent annotation passes over the same trajectories:
`objective_level/` labels the training objective of each experiment, and `strategy_level/` labels
the full strategy state — training strategy, data source, and stage structure.

A *training experiment* is counted only when an executed command launches a parameter update;
writing training scripts, constructing data, installing packages, running evaluations, and saving
checkpoints do not count as independent experiments. A transition between adjacent experiments is
a *strategy change* only when it alters the training paradigm, the data-source type, or the stage
structure; everything else — learning rates, data reformatting, reward shaping within a paradigm,
checkpoint selection, bug fixes — is an execution change.

Labels are assigned from executed evidence only, never from stated intent, and missing labels are
never imputed. Every label carries a reference back to the exact line of the source trajectory.

## Documentation

- [`docs/framework.md`](docs/framework.md) — the experience-driven scaffold and the run loop
- [`docs/annotation-protocol.md`](docs/annotation-protocol.md) — label definitions and coverage
- [`docs/metrics.md`](docs/metrics.md) — metric definitions and cohorts

## Citation

Citation details are withheld for anonymous review.

## License

[MIT](LICENSE).

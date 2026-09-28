# What is Missing from AI Post-Training AI: An Empirical Analysis

<div align="center">

[![Paper](https://img.shields.io/badge/📄-Paper-blue)](https://arxiv.org/abs/2608.19072)
[![License](https://img.shields.io/badge/License-MIT-red.svg)](LICENSE)

</div>

Code and data for **[What is Missing from AI Post-Training AI: An Empirical Analysis](https://arxiv.org/abs/2608.19072)**.

## Overview

We give coding agents a base language model, a benchmark, one GPU, and ten hours, and ask them to
post-train the model. Repeating this 1,338 times, we find that agents are strong *executors* and
weak *strategists*.

The paper separates two capabilities that discussions of recursive self-improvement (RSI) tend to
conflate. Every training experiment decomposes into a **strategy** `s = (p, d, g)` — training
algorithm, data source, stage structure — and an **execution configuration** `x`:

- **Execution-level capability** — moving within `x` while holding `s` fixed: formatting data,
  tuning hyperparameters, shaping rewards, selecting checkpoints, debugging the implementation.
- **Strategy-level capability** — moving within `s`: switching the training algorithm, changing
  the data source, adding or removing a training stage, as experimental evidence accumulates.

The two levels partition the headroom of a run. For a trajectory locked into its initial strategy
`s₁`, with `V(s, x)` the benchmark score, `V⋆(s) = maxₓ V(s, x)` and `V⋆ = maxₛ V⋆(s)`:

```
V⋆ − V(τ)   =   V⋆ − V⋆(s₁)   +   V⋆(s₁) − V(τ)
 total gap      strategy-level gap    execution-level gap
```

Agents configure trainers, fit models onto a single card, and recover from crashes reliably, so
the **execution-level gap shrinks steadily**. But the strategy they commit to is fixed before any
experimental evidence arrives, and is almost never revised afterwards — even when the agent's own
recorded evidence says it should be. The **strategy-level gap is therefore frozen at `t = 1`**. We
call this **strategy lock-in**.

The analyzed trajectories are publicly released PostTrainBench runs, spanning seven benchmarks,
four base models, and three agent frameworks (Claude Code, Codex CLI, OpenCode) across 20
agent-model configurations; the controlled experiments are our own. This repository contains the
harness that ran them, the annotations behind the paper's numbers, and thirteen archived agent runs
covering all three conditions.

What the agent turns out to lack is neither the ability to carry out a different strategy nor a
resource, but **the decision to reopen a committed strategy and try another one**.

## Findings

**Finding 1 — agents are reliable executors.** A trajectory averages 3.82 training runs and 13.80
evaluations. Nearly every agent completes the pipeline from data preparation through training,
evaluation, and checkpoint submission, and every benchmark shows an average gain over the base
model. The repairs are technically meaningful — realigning generation templates, concentrating a
data mixture on the target format, fixing EOS handling — so execution is not the binding
constraint.

**Finding 2 — agents lock into a default strategy, and the default follows the agent, not the
task.** Each agent commits to a default before any experimental evidence arrives, and different
agents commit to different defaults on the same tasks under the same budget. Writing `κ_a` for the
mass an agent's initial-strategy distribution places on its modal strategy, and `ρ_a` for its
pooled switch rate over adjacent training pairs:

| Agent (#Traj.) | Default strategy (`κ_a`) | Switch rate (`ρ_a`) |
| --- | --- | --- |
| Claude Code (575) | Full SFT — 166/231 = **71.9%** | 54/1,203 = 4.5% |
| Codex CLI (369) | PEFT — 274/306 = **89.5%** | 15/943 = 1.6% |
| OpenCode (394) | Full SFT — 184/277 = **66.4%** | 5/1,411 = 0.4% |
| Overall (1,338) | 624/814 = **76.7%** | 74/3,557 = **2.1%** |

The divergence is systematic: in every one of the 28 benchmark × base-model combinations, Claude
Code shows a higher full-SFT share and Codex CLI a higher PEFT share. Once training starts, the
budget is spent inside that choice — only 74 of 3,557 adjacent training pairs ever probe an
alternative, and the rest are denser local search over learning rates, data mixtures, and chat
templates. The rate stays low even where the default nearly fails: on AIME 2025 final scores
remain near zero, yet the highest per-agent switch rate is 10.6%.

**What unlocks the strategy level?** Revising a committed strategy needs the *experience* to
recognize it is failing, the *reasoning* to weigh an alternative, and the *decision* to act. We
test each in turn.

| Probe | Effect on execution | Effect on strategy |
| --- | --- | --- |
| Experience — journal, skill library, evaluator agent | closes **75.1%** of the base-to-instruct gap vs. 48.6% for the same agent autonomously (+12.6 GSM8K, +30.8 HumanEval) | unchanged — the agent adopts **22/22** execution-level suggestions from the evaluator and **0/21** strategy-level ones |
| Reasoning compute — 1.8–9.2× the agent tokens | front-loaded gains on the easier benchmarks (3.7M tokens per point on GSM8K, 0.9M on HumanEval) | none on the hardest — on AIME 2025 roughly 14M extra tokens buy one extra problem, within evaluation variance |
| Decision — human review *before* training | the starting strategy is redirected, and the agent implements and even extends it on its own initiative | changes *which* strategy the agent locks into, not *whether* it locks in |
| Decision — a single instruction to switch *mid-run* | — | **reopens the committed strategy**: forked from the same checkpoint under the same remaining budget, the guided branch wins on all three benchmarks, by up to **17.44 points** |

Two controls matter for reading that last row. Human review at the initial decision does not keep
the agent from locking in: the AIME 2025 runs peak early (best 3/30 pass@8) and then tune
hyperparameters back and forth inside the *new* strategy without recovering the peak. And when a
fork is given an instruction to *reconsider* its strategy without naming an alternative, the agent
reaffirms its current strategy in every case and proceeds much as its recorded continuation did.

So what is missing is not the ability to carry out a different strategy, and not a resource:
experience and reasoning compute both improve execution without moving the strategy. It is **the
decision to reopen a committed strategy and try another one**. Human guidance works precisely
because it makes that decision on the agent's behalf; nothing we supplied leads the agent to make
it on its own.

### What this implies for RSI

RSI assumes a loop that closes globally — propose a strategy, run experiments, interpret results,
revise the strategy, repeat. What we observe closes only at the execution level:

```
assumed: globally closed            observed: locally iterative, globally linear

  Strategy → Execute → Evaluate       Strategy → Execute → Evaluate
      ↑__________________|                          ↑________|
          revise strategy                          repair & retry
                                              (revision not taken)
```

Two consequences. Scaling execution-level autonomy deepens the loop that already closes and leaves
the open one untouched — the quality of the *initial* strategy, not the iteration count or the
compute, sets a run's upper bound. And measuring RSI progress needs strategy-level metrics
alongside the final score: two agents with the same score may differ in exactly the capability RSI
depends on. See [`docs/metrics.md`](docs/metrics.md) for the three we propose.

## Controlled Experiments

Qwen3-1.7B-Base on three benchmarks of increasing difficulty, ten hours per run on four A800 GPUs,
three independent runs per configuration, with the system prompt, base model, hardware, and
evaluation protocol held fixed within each comparison. Scores are pass@1, except AIME 2025, which
has only 30 problems and is scored pass@8. All interventions build on Claude Code with Opus 4.6,
which preliminary runs found more reliable on this setting than Opus 4.8, Opus 5 and Fable 5 —
the newer models either vary widely across runs or contaminate training data (train-on-test).

Mean ± one standard deviation over three runs. `Gap Closed` is
`(Avg − Avg_base) / (Avg_instruct − Avg_base)`: the fraction of the distance from the base model to
the official instruct model that the run recovers.

| Setting | GSM8K | HumanEval | AIME 2025 | Avg. | Gap Closed |
| --- | --- | --- | --- | --- | --- |
| Base model | 10.84 | 5.48 | 0.00 | 5.44 | 0.0% |
| Official instruct model | 88.70 | 66.46 | 33.33 | 62.83 | 100.0% |
| Autonomous — Opus 4.6 (Claude Code) | 64.70 ±9.6 | 32.00 ±10.4 | 3.33 ±0.0 | 33.34 | 48.6% |
| Autonomous — GLM-5.2 (Claude Code) | 49.51 ±7.2 | 44.51 ±9.8 | 3.33 ±0.0 | 32.45 | 47.1% |
| Autonomous — GPT-5.2 (Codex CLI) | 43.44 ±4.1 | 13.41 ±8.7 | 0.00 ±0.0 | 18.95 | 23.5% |
| **Experience-driven (Opus 4.6)** | **77.30 ±3.8** | **62.80 ±6.1** | **5.56 ±1.6** | **48.55** | **75.1%** |
| — w/o experiment journal | 74.50 ±4.5 | 50.20 ±7.4 | 4.44 ±1.6 | 43.05 | 65.5% |
| — w/o skill library | 73.10 ±5.2 | 54.50 ±6.8 | 3.33 ±0.0 | 43.64 | 66.6% |
| — w/o evaluator agent | 68.20 ±6.0 | 42.60 ±8.2 | 3.33 ±0.0 | 38.04 | 56.8% |

All three components contribute; the evaluator agent matters most (−18.3 points of gap closed when
removed). Note that every ablation still closes more of the gap than any autonomous baseline, and
none of them lifts AIME 2025 past a single problem.

Human guidance is evaluated separately, at two decision points. A **human review before training**
runs on AIME 2025: the reviewer redirects the initial strategy from SFT to RL, the agent implements
and even extends the new strategy — and then locks into it, reaching its best score of 3/30 (10.0%
pass@8) early and iterating on hyperparameters for the rest of the budget. A **single mid-run
instruction to switch strategy**, issued at a forked checkpoint of a completed autonomous run and
compared against that run's own recorded continuation under the same remaining budget, beats the
continuation on all three benchmarks:

| Benchmark | Agent's own continuation | Guided branch | Δ |
| --- | --- | --- | --- |
| GSM8K (pass@1) | 47.76% | 65.20% | **+17.44** |
| HumanEval (pass@1) | 52.00% * | 62.80% | +10.80 |
| AIME 2025 (pass@8) | 0.00% | 6.67% | +6.67 |

Forking each of those checkpoints with an instruction that asks the agent to *reconsider* its
strategy without naming an alternative produces no switch: in every such fork the agent reaffirms
what it is already doing.

The three recorded continuations are archived as `autonomous_{gsm8k,humaneval,aime2025}_*` in
[`trajectories/`](trajectories/). (* The HumanEval continuation reached 58.54% at its highest, but
that checkpoint showed data contamination and is excluded.)

## Repository Structure

```
├── framework/       the experience-driven scaffold
│   ├── journal/       experiment journal: plan / lesson / reflection schemas
│   ├── evaluator/     evaluator agent: predict → evaluate → analyze
│   └── skills/        the skill library the agent consults, and the wiki it is distilled from
├── experiments/     agent prompts, configs, and launchers, per benchmark
├── evaluation/      AIME 2025 / GSM8K / HumanEval scoring harnesses
├── analysis/        trajectory parsing pipeline, lock-in analyses, and the annotations
├── trajectories/    thirteen agent runs: framework, baseline, and human-guided
└── docs/            framework design, annotation protocol, metric definitions
```

Each directory has its own `README.md`.

The scaffold's three components map onto the first three subdirectories. The **experiment journal**
persists plans, results, observations, and lessons across iterations, so evidence from an early
experiment survives into a later decision. The **skill library** distills recipes, configurations,
and known failure modes from widely used training frameworks into references the agent consults
while building and debugging its pipeline; it is compiled before the campaign, not written during
it. The **evaluator agent** runs whenever the main agent
requests an evaluation: it forms an expectation, invokes the original scoring script, inspects both
the scores and the model outputs, and returns a diagnosis with concrete suggestions — which the
main agent is free to ignore, and at the strategy level does.

## Installation

```bash
git clone --recurse-submodules https://github.com/JoylimJY/AI-PostTraining-AI.git
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
The thirteen included runs are complete enough to exercise every parser on real input; they cover
both stream formats the pipeline handles.

## Data

`analysis/annotations/` holds two independent annotation passes over the same trajectories:
`objective_level/` labels the training objective of each experiment, and `strategy_level/` labels
the full strategy state `s = (p, d, g)` — training algorithm, data source, and stage structure.

A *training experiment* is counted only when an executed command launches a parameter update;
writing training scripts, constructing data, installing packages, running evaluations, and saving
checkpoints do not count as independent experiments. A transition between adjacent experiments is
a *strategy change* only when it alters the training algorithm `p`, the data-source type `d`, or
the stage structure `g`; everything else — learning rates, data reformatting, reward shaping within
an algorithm, checkpoint selection, bug fixes — is an execution change.

Of the 5,111 verified experiments the training algorithm is recognized for 4,378; the other 733
are left unlabelled and never imputed. Switch rates are computed over the 3,557 recognized
adjacent training pairs.

Labels are assigned from executed evidence only, never from stated intent, and missing labels are
never imputed. Every label carries a reference back to the exact line of the source trajectory.

## Documentation

- [`docs/framework.md`](docs/framework.md) — the experience-driven scaffold and the run loop
- [`docs/annotation-protocol.md`](docs/annotation-protocol.md) — label definitions and coverage
- [`docs/metrics.md`](docs/metrics.md) — metric definitions and cohorts

## Citation

```bibtex
@misc{lim2026missingaiposttrainingai,
      title={What is Missing from AI Post-Training AI: An Empirical Analysis},
      author={Joy Jia Yin Lim and Xin Huang and Hao Peng and Yaxi Lu and Xin Cong and Zhong Zhang and Maosong Sun and Yankai Lin},
      year={2026},
      eprint={2608.19072},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2608.19072},
}
```

## License

[MIT](LICENSE).

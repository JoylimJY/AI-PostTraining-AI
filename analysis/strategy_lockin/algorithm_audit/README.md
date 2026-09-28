# Training-algorithm change audit

Of the 1,338 trajectories, **16** ever change training algorithm, over **35**
transitions. That is small enough to read by hand, and the paper's audit and its
five trace-level case studies come from doing so. This directory rebuilds the
mechanical part of that audit from the released annotations.

```bash
python analysis/strategy_lockin/algorithm_audit/build_algorithm_audit.py
```

Inputs are all redistributed: the strategy-level trajectory table and the
broad-criterion pass's `episode_labels.jsonl` / `broad_transitions.csv`. Every
number the paper prints is asserted, so drift in the annotations fails the run
rather than quietly producing a different audit.

| Output | What it is |
|---|---|
| `output/algorithm_change_trajectories.csv` | the 16, with their full algorithm sequence |
| `output/algorithm_transitions.csv` | the 35 transitions, with direction and position |
| `output/table6_cases.csv` | the 5 case studies of Table 6 |

## What the audit found

| Statistic | Value |
|---|---:|
| Trajectories that change algorithm | 16 |
| Algorithm transitions | 35 |
| Trajectories beginning with SFT | 14 / 16 |
| Trajectories switching at least twice | 11 / 16 |
| Transitions arriving back at SFT | 15 / 35 |
| Median normalized progress, first switch | 0.40 |
| Median normalized progress, all switches | 0.67 |

Two of these matter for how the count of 35 should be read. Most trajectories
that change at all **oscillate** rather than commit — `algorithm_sequence` shows
runs like `SFT SFT DPO SFT DPO SFT SFT` — and the single most common transition
is a **retreat to SFT**. A raw change count therefore overstates genuine
strategic exploration. And agents that revise do so **late**: by the median
first switch, 40% of the experiment sequence is already spent inside the initial
algorithm.

Normalized progress is the arriving experiment's position within the
trajectory's own experiment sequence, on [0, 1], so it is comparable across
trajectories of different lengths.

Full SFT and PEFT share the supervised-likelihood objective form, so swapping
one for the other is an execution change and does not appear here. That is why
this audit covers 35 pairs while the strategy-change total is 74 — the other 39
are data-source and stage-structure changes, decomposed in
[`../broad_criterion/output/tables/strategy_change_partition.csv`](../broad_criterion/output/tables/strategy_change_partition.csv).

## The five case studies

`output/table6_cases.csv` reproduces Table 6. The cases were chosen to show
both directions of outcome: an alternative algorithm sometimes helps and
sometimes regresses.

| Case | Setting | Change | Observation | Reading |
|---|---|---|---|---|
| `3fd3ea0b` | ArenaHardWriting, SmolLM3-3B, Codex CLI | SFT→DPO | held-out 256-pair proxy 66.0% → 66.8% | positive, +0.8pp |
| `c92715d6` | ArenaHardWriting, Gemma-3-4B, Claude Code | SFT→DPO | benchmark win rate ~8% → 16.7% | positive, ≈2× |
| `50c64287` | ArenaHardWriting, Qwen3-4B, Codex CLI | SFT→DPO | same 8-prompt local proxy 7.14% → 7.69% | positive, small sample |
| `860ceacd` | AIME 2025, Qwen3-1.7B, Claude Code | SFT→GRPO | 30-problem eval 0% → 3.3% (1/30) | positive, high variance |
| `8226f786` | ArenaHardWriting, SmolLM3-3B, Codex CLI | SFT→DPO | external proxy 0.539 → 0.478, internal DPO reward accuracy 0.713 → 0.727 | counterexample, metric mismatch |

**What is and is not reproducible here.** The `Observation` column quotes each
run's own comparator and sample size, read out of trajectory logs that are not
redistributed; those strings are carried as constants in the script and marked
`observation_source = trajectory log, not redistributed`. Everything around them
is checked against the released annotations: that the case is one of the 16,
that it sits in the stated benchmark / base model / framework cell, that it is
present in the objective-level pass, and that it really does change algorithm in
the stated direction. Each row carries an `annotation_reference` back to that
record.

The observations deliberately keep each log's original comparator rather than
being restated on a common scale. They are not comparable across rows, and none
of them is a controlled measurement of the algorithm change — the agent changed
other things at the same time. They show what evidence the agent itself had in
front of it when it judged the switch, which is the point: `8226f786` is the
case where the agent's internal metric improved while the external one fell.

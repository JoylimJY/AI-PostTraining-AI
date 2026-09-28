# Metric definitions

Three metrics carry the paper's argument: an **execution** metric that shows agents are competent,
and two **strategy** metrics that show they do not revise. This document defines all three, states
the cohorts they are computed over, and points at the released files that reproduce them.

---

## Cohorts

Not every trajectory can answer every question. A trajectory that crashed in its first ten minutes
has behavior worth counting but no checkpoint to score; a trajectory whose training configuration
cannot be resolved cannot contribute a strategy label. Rather than silently dropping rows per
statistic, the pipeline materializes named cohorts and each result states which one it uses.

| Cohort | Size | Admission criterion |
|---|---:|---|
| `all_inventory` | 1,338 | Every trajectory in the corpus |
| `behavior_cohort` | 1,300 | Trajectory produced a parseable event stream |
| `artifact_ready` | 992 | Produced at least one durable artifact (checkpoint, dataset, or score) |
| `objective_ready` | 792 | Carries a resolved training-objective label |
| `strategy_ready` | 792 | Carries a complete strategy state `s = (p, d, g)` |
| `strategy_outcome_ready` | 654 | Complete strategy state **and** a scored outcome |
| `matched_cell` | 1,338 | Belongs to one of the 28 matched (scaffold × model × benchmark) cells |

The cohorts nest: `strategy_outcome_ready` ⊂ `strategy_ready` ⊆ `objective_ready` ⊂
`artifact_ready` ⊂ `behavior_cohort` ⊂ `all_inventory`. `matched_cell` is a separate partition of
the full inventory into 28 cells, run over 47 batches, used for like-for-like scaffold comparisons.

`filter_cohorts.py` in `analysis/pipeline/` defines these; the cohort of each trajectory is a
column in the released annotation tables, so any statistic can be re-scoped.

---

## Execution: per-strategy success rate

For a scaffold and a training strategy, the success rate is the fraction of launched experiments
that complete and produce a usable checkpoint:

```
success_rate = (experiments that completed and produced a checkpoint) / (experiments launched)
```

This is deliberately generous. It asks only "did the job run and yield something scoreable," not
"did it help." That is the point: it isolates mechanical competence from judgment.

| Scaffold | Algorithm | Success rate |
|---|---|---|
| Claude | Full supervised fine-tuning | **163 / 202 = 80.7%** |
| Codex | Parameter-efficient fine-tuning | **268 / 299 = 89.6%** |

Agents configure distributed trainers, fit models onto a single 80GB card, convert datasets into
the right on-disk schema, and recover from crashes, at rates in the eighties and nineties. Nothing
in the corpus suggests execution is the bottleneck.

> These are **completion rates of launched experiments**, computed over the five original harness
> families and their method-labelled training commands. They are not the default-strategy
> concentrations `κ_a` below, which have similar-looking values but a different question, a
> different denominator, and the three-framework grouping.

---

## Strategy: default-strategy concentration `κ_a`

How much do independent agents agree on where to start? For an agent `a`, let
`π_a(s) := Pr[s₁ = s | a]` be the distribution of its **initial** strategy state. The
default-strategy concentration is the mass that distribution places on its modal strategy:

```
κ_a  =  max   π_a(s)
       s ∈ S
```

`κ_a` is the share of an agent's runs taking its single most common opening move. It ranges from
`1/|S|` (the agent spreads evenly over the strategy space) to `1` (every run opens identically).

`κ_a` is computed over the **814 trajectories with a recognized initial strategy**, which includes
trajectories that never launch training but state a planned strategy — so the denominator is not
the 900 that launch training, nor the 792 of `strategy_ready`.

| Agent framework (#Traj.) | Default strategy | `κ_a` |
|---|---|---:|
| Claude Code (575) | Full SFT | 166 / 231 = **71.9%** |
| Codex CLI (369) | PEFT | 274 / 306 = **89.5%** |
| OpenCode (394) | Full SFT | 184 / 277 = **66.4%** |
| Overall (1,338) | — | 624 / 814 = **76.7%** |

A high `κ_a` is not by itself a defect. If one opening is genuinely best, agreeing on it is
correct. What makes it a lock-in rather than a consensus is that the default **follows the agent
rather than the task**: on the same benchmark and the same base model, Claude Code concentrates on
full SFT while Codex CLI concentrates on PEFT, in all 28 matched cells. And it is only evidence in
combination with the next metric: converging on an opening *and then never revising it*.

---

## Strategy: switch rate `ρ`

For a trajectory `τ` with `T ≥ 2` training experiments, the switch rate is the fraction of adjacent
experiment pairs that change the strategy state:

```
               1     T−1
ρ(τ)  =  ───────────  Σ   1[ s_{t+1} ≠ s_t ]
            T − 1    t=1
```

We write `ρ̄` for the pooled rate over all recognized adjacent pairs in the corpus, and `ρ_a` for
the same pooled rate restricted to agent `a`'s pairs. A trajectory with `ρ(τ) = 0` is **completely
locked in**: its strategy-level gap is fixed at `t = 1`.

Of the 5,111 verified experiments the algorithm is recognized for 4,378, and the recognized
adjacent pairs number 3,557.

Over the full corpus:

| Quantity | Value |
|---|---:|
| Recognized adjacent experiment pairs | 3,557 |
| Strategy changes | 74 |
| `ρ̄` | **2.1%** |
| Persistence `1 − ρ̄` | **97.9%** |
| Trajectories contributing ≥1 change | 44 of 792 |

Per agent framework:

| Agent framework | `ρ_a` |
|---|---:|
| Claude Code | 54 / 1,203 = 4.5% |
| Codex CLI | 15 / 943 = 1.6% |
| OpenCode | 5 / 1,411 = 0.4% |

Decomposed by which component of `s = (p, d, g)` moved:

| Component | Changes | Rate |
|---|---:|---:|
| Training algorithm `p` | 35 | 0.98% |
| Data source `d` | 38 | 1.07% |
| Stage structure `g` | **1** | **0.03%** |
| Overall | 74 | 2.08% |

**No pair changes more than one dimension**, so the three rows partition the 74 exactly. The
data-source dimension is scoped to the 4,344 experiments with a supervised objective, of which
provenance is identifiable for 1,801 (1,327 curated, 424 self-generated, 50 mixed), spanning 1,401
recognized pairs.

The stage-structure figure is the sharpest result in the paper. Across 1,338 trajectories, ten
hours each, 5,111 launched experiments, agents altered the *shape* of their training pipeline
exactly once. Whatever pipeline an agent commits to in its first hour is, with one exception, the
pipeline it dies with.

Nor does a low `ρ̄` mean the strategy never *nearly* fails. On AIME 2025, where final scores stay
close to zero, the highest per-agent switch rate is still only 10.6%. Switch rates vary mildly with
the task — Claude Code reaches about 11% on AIME 2025 but 0% on BFCL — yet no benchmark elicits
systematic search over `S`.

### What `ρ` is not measuring

`ρ` is defined over the strategy state only. It is deliberately blind to hyperparameter edits,
data-volume changes, checkpoint selection, and prompt-format fixes — all of which agents do
constantly and competently. The 97.9% persistence figure does **not** say agents are idle between
experiments. It says the thing they change is never the strategy.

Nor is it a measure of *correct* revision. It counts changes, not improvements. A change is
counted whether it helped or hurt; the paper's claim is about the near-total absence of changes,
which no accounting of their quality can explain away.

---

## Three strategy-level metrics for RSI benchmarks

Current RSI benchmarks tend to report only a final score. Under that measure two agents with the
same score may differ in exactly the capability RSI depends on: one chooses the right strategy for
the task, the other holds a default that happens to suit it and will fail once the task changes.
The paper therefore proposes reporting these three alongside the final score:

| Metric | Definition | Where it is computed here |
|---|---|---|
| **Switch rate** `ρ` | fraction of adjacent experiment pairs that change `s` | this document; [`../analysis/strategy_lockin/`](../analysis/strategy_lockin/) |
| **Adoption rate of strategy-level suggestions** | of the suggestions that depart from the current strategy, the fraction the agent implements | 0/21 in the controlled runs, against 22/22 at the execution level (Table 7) |
| **Strategy-level gap** | score of a switched branch forked from a mid-run checkpoint, minus the agent's own continuation under the same remaining budget | up to +17.44 points (GSM8K); see the controlled experiments in the top-level README |

The third is the only one of the three that estimates what the lock-in *costs*, because it holds
the prefix, the checkpoint, and the remaining budget fixed and varies only the decision.

---

## Recomputing these numbers

```bash
# κ_a and ρ_a per framework — Table 1 — from the released annotations
python analysis/strategy_lockin/scaffold_lockin/build_comparison.py

# The 35/38/1 partition and the per-benchmark rates — Tables 4 and 5
python analysis/strategy_lockin/broad_criterion/build_paper_tables.py

# The 16 algorithm-changing trajectories and the five cases of Table 6
python analysis/strategy_lockin/algorithm_audit/build_algorithm_audit.py

# Objective transitions and evaluation events; needs the regenerated intermediate/ tree
python analysis/strategy_lockin/broad_criterion/build_broad_transitions.py
```

The first three read released files only and run against this repository as cloned; each asserts
the figures the paper prints, so annotation drift fails the run instead of quietly producing a
different table. Only the last needs `analysis/pilot_study/intermediate/`, which is not
redistributed; regenerate it with `run_pilot.py` first. Note that
`broad_criterion/report.md` reports 73 changes over 43 trajectories rather than 74 over 44; that
gap is one adjudicated stage-structure candidate and is explained in
[`annotation-protocol.md`](annotation-protocol.md#reconciling-73-vs-74).

To recompute cohorts and tables from raw trajectory logs:

```bash
python -m analysis.pipeline.run_pipeline --config analysis/pipeline/config.json
```

This requires the raw logs, which are terabyte-scale and not released. The thirteen runs in
`trajectories/` are complete enough to run the parsers end-to-end and verify the extraction stages
against real input, in both of the stream formats the pipeline accepts.

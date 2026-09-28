# Broad-Criterion Strategy-Change Audit

- **Script**: `build_broad_transitions.py`
- **Input**: the objective-layer annotation intermediates (read-only; not
  redistributed — see [`../../annotations/README.md`](../../annotations/README.md))
- **Output**: `output/`

## Purpose

The paper defines a *strategy change* as a change along any of three axes:
training paradigm, data-source type, or stage structure. The main annotation
pipeline measures only the paradigm (objective) axis. This audit fills in the
other two axes over the **same denominator of 3,557 adjacent experiment pairs**
and reports the resulting broad-criterion statistics.

## Method

**Data-source axis** (rule-based; supervised and preference experiments only —
for RL, on-policy rollout is intrinsic to the paradigm and is not counted as a
separate axis):

1. A data file referenced by the training script whose name matches generation
   markers (`rejection`, `generated`, `synthetic`, `teacher`, `distill`, …) is
   labelled `self_generated`.
2. **File provenance propagation.** The whole trajectory is scanned: a data file
   produced by a generation command (vLLM, `.generate(`, sampling — where the
   command explicitly names the file) is marked *self*; one produced by a hub
   download or conversion command is marked *curated*. At training time the most
   recent mark for that file is looked up.
3. Non-data JSON (configs, tokenizers) is excluded, and isolated vLLM/eval
   sampling is not accepted as evidence.

The change decision is binary — `curated` vs *self-involved*
(`self_generated` ∪ `mixed`) — and a pair enters the denominator only when both
sides carry an identifiable label.

**Stage-structure axis**: only candidates are emitted (the initialisation source
switches between the base model and an in-run checkpoint). They are handed to
the authors for review and are not included in the mechanical totals.

## Results (third pass, 2026-08-19)

| Criterion | Pairs | Rate |
|---|---:|---:|
| Paradigm change (original criterion) | 35 / 3,557 | 0.98% |
| Data-source change (1,401 pairs labelled on both sides) | 38 / 3,557 | 1.07% |
| **Broad criterion (paradigm ∪ data source)** | **73 / 3,557** | **2.05%** |
| Stage-structure candidates (pending review) | 2 | — |

- Trajectories with ≥1 broad-criterion change: 43 / 792 (16 under the paradigm
  criterion alone).
- Label coverage: 1,801 of 4,344 supervised experiments have an identifiable
  data source (41.5%); 1,327 `curated`, 424 `self_generated`, 50 `mixed`.
- Broad-criterion change rate by harness: Claude 53/1,132 (4.7%), Codex 14/943
  (1.5%), OpenCode 5/1,411 (0.4%), GLM-X 1/3, Qwen3Max 0/68. Data-source changes
  are concentrated in the Claude family (35/38), consistent with its
  data-intensive behaviour.

  > **Mapping to the paper's Table 1.** The paper groups these five harness
  > families into three *agent frameworks*: GLM-X and Qwen3Max are Claude Code
  > configurations, so Claude Code is 53 + 1 + 0 = 54 changes over
  > 1,132 + 3 + 68 = 1,203 pairs (4.5%), against Codex CLI 14/943 and OpenCode
  > 5/1,411. Codex CLI's Table 1 figure is 15/943 rather than 14/943: the extra
  > change is the adjudicated stage-structure candidate below, which this
  > mechanical pass does not include. This note is editorial; the numbers above
  > are the script's output, left as it ran.
- Direction: `curated`→`self` 18, `self`→`curated` 12, `mixed`↔`curated` 8.
  Changes are round-trips rather than one-way, at most 4 in a single trajectory.

## Quality-control record

- **Pass 1** (any vLLM/generate call inside the window counts as evidence)
  produced 225 data-source changes. Spot checks showed most were false positives
  from the evaluation service's vLLM. **Discarded.**
- **Pass 2** (evidence from inside the training script only) produced 0
  data-source changes, but coverage was only 18% and `config.json` was being
  matched by mistake. **Judged too strict.**
- **Pass 3** (provenance propagation + non-data JSON excluded) reached 41.5%
  coverage; all 10 spot-checked data-source changes were genuine data-regime
  switches — e.g. `train_data.jsonl <- load_dataset('gsm8k')` followed by
  `train_data_v2.jsonl <- vLLM`. **Adopted.**

## Limitations

- Data-source labels are rule-based. Under the paper's protocol they require
  author spot-check review before being used in the text;
  `output/episode_labels.jsonl` retains the full evidence string for each label.
- 58.5% of supervised experiments have an unidentifiable data source (the script
  references a local file with no provenance information). Those pairs cannot
  contribute a data-source change, so the broad-criterion rate remains a **lower
  bound**.
- At adjacent-pair granularity the stage axis is almost entirely absorbed by
  paradigm boundaries — only 2 candidates, listed in
  `output/stage_candidates_review.csv`.

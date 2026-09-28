# Archived Trajectories

Sixteen runs. Ten are our own controlled experiments — the ones the paper's
qualitative claims point at. Six are supplementary: three further autonomous
runs recorded by the PostTrainBench harness, and three *fork* runs that continue
each of those three from a chosen point in its trajectory. Each directory is the
agent's working directory as it stood when the run ended, minus the artifacts
that cannot be redistributed.

Directories are named `{setting}_{benchmark}_{id}`. The setting is the condition
the agent ran under — `experience` (the experience-driven framework: experiment
journal, skill library, evaluator agent), `autonomous` (no framework, the
baseline), `human` (a human reviews the agent's plan before the autonomous
phase), or `fork` (the workspace of an archived autonomous run restored to a
chosen node of its trajectory, then continued autonomously under a fresh budget
with a one-line hint; see [Supplementary runs](#supplementary-runs)). The id is
the first 8 hex characters of a manifest digest over the
released directory: `sha256` of the sorted `<relative path>\0<sha256 of file>`
lines for every file it contains. It depends only on released content, so it can
be recomputed from a checkout.

| Run | Setting | Scaffold | Benchmark | Wall clock | Journal entries | Evaluations | Score |
|---|---|---|---|---:|---:|---:|---:|
| [`experience_aime2025_c247e78e/`](experience_aime2025_c247e78e/) | experience | Claude Code | AIME 2025 | 6h 09m | 35 | 5 | 0.033 |
| [`experience_gsm8k_855100f4/`](experience_gsm8k_855100f4/) | experience | Claude Code | GSM8K | 4h 50m | 74 | 11 | 0.773 |
| [`experience_humaneval_d26cfb40/`](experience_humaneval_d26cfb40/) | experience | Claude Code | HumanEval | 7h 12m | 72 | 14 | 0.628 |
| [`human_aime2025_14ce9dfd/`](human_aime2025_14ce9dfd/) | human | Claude Code | AIME 2025 | 8h 57m | 59 | 9 | 0.067 |
| [`autonomous_aime2025_250c7e3e/`](autonomous_aime2025_250c7e3e/) | autonomous | Claude Code | AIME 2025 | 8h 53m | — | — | — |
| [`autonomous_gsm8k_42890926/`](autonomous_gsm8k_42890926/) | autonomous | Claude Code | GSM8K | 10h 06m | — | — | — |
| [`autonomous_humaneval_fc9a969e/`](autonomous_humaneval_fc9a969e/) | autonomous | Claude Code | HumanEval | 10h 06m | — | — | — |
| [`autonomous_aime2025_c7c4a0c4/`](autonomous_aime2025_c7c4a0c4/) | autonomous | Codex | AIME 2025 | 7h 24m | — | — | 0.000 |
| [`autonomous_gsm8k_5dcf0c73/`](autonomous_gsm8k_5dcf0c73/) | autonomous | Codex | GSM8K | 3h 02m | — | — | 0.537 |
| [`autonomous_humaneval_832f94ce/`](autonomous_humaneval_832f94ce/) | autonomous | Codex | HumanEval | 5h 33m | — | — | 0.134 |
| [`autonomous_aime2025_99ac2f89/`](autonomous_aime2025_99ac2f89/) | autonomous | Claude Code | AIME 2025 | 9h 45m | — | — | 0.000 |
| [`autonomous_gsm8k_886c6165/`](autonomous_gsm8k_886c6165/) | autonomous | Claude Code | GSM8K | 9h 56m | — | — | 0.478 |
| [`autonomous_humaneval_e55852d6/`](autonomous_humaneval_e55852d6/) | autonomous | Claude Code | HumanEval | 7h 48m | — | — | 0.585 |
| [`fork_aime2025_b10da191/`](fork_aime2025_b10da191/) | fork | Claude Code | AIME 2025 | 4h 47m | — | — | 0.033 |
| [`fork_gsm8k_4c81c492/`](fork_gsm8k_4c81c492/) | fork | Claude Code | GSM8K | 6h 51m | — | — | 0.466 |
| [`fork_humaneval_af9d89f6/`](fork_humaneval_af9d89f6/) | fork | Claude Code | HumanEval | 5h 06m | — | — | 0.299 |

All sixteen runs post-train Qwen3-1.7B-Base on 4 GPUs; every Claude Code run
uses `claude-opus-4-6` as the agent, the Codex runs `gpt-5.2`. The thirteen
`experience`, `human` and `autonomous` runs have a 10-hour budget. The three
`fork` runs have a fresh budget of 5, 7 and 5 hours that starts at the fork
point, which sat about 4h48m, 2h51m and 5h14m into the source run; the wall
clock above counts only the continuation. `run_metadata.json` in each directory
records the exact start/end times and configuration. Several runs ended before
their budget; where they did, the reason is in the stream's closing records.

**The score column is not a controlled comparison.** It has four different
meanings. The four framework and human runs report the in-run metric produced by
our own evaluator agent, one sample per problem. The three Codex runs report the
benchmark harness's final evaluation of the model the agent submitted. The three
Claude Code autonomous runs have no official score: the harness's final
evaluation never started for that batch, so nothing was recorded. What those
three do have is the agent's own evaluations — 7, 5 and 9 of them, condensed
into `evals/eval_log_summary.json`, run on subsets the agent chose for itself
(20 to 150 problems) and ending at 0.000 on AIME 2025, 0.647 on GSM8K and 0.050
on HumanEval. Those are the agent's own view of its progress, not benchmark
results; the HumanEval agent's best subset score along the way was 0.35, and it
finished below it. The six supplementary runs report the PostTrainBench
harness's final evaluation of the submitted model (`metrics.json`), with one
exception: in `fork_aime2025_b10da191/` the harness's automatic final evaluation
could not start a vLLM server on `final_model` (the GPUs were shared with
another user's processes), so the same evaluation was re-run by hand on the
submitted weights; it scored 1/30, matching the agent's own last two
evaluations of those weights. A fork run's score is comparable only to its own
source run — its starting point is that run's state at the fork node, not the
base model.

If you want the autonomous condition held to the same scaffold as the framework
runs, use the Claude Code rows: the Codex runs differ from everything else
here in scaffold as well as in setting. The paper's quantitative claims rest on
the annotated corpus in [`../analysis/annotations/`](../analysis/annotations/),
not on these ten runs. The post-hoc pass@8 numbers for the AIME comparison are in
[`../experiments/human_guidance/pass8_results.json`](../experiments/human_guidance/pass8_results.json).

## What each directory contains

The framework and human runs came out of our own harness
([`../experiments/`](../experiments/)):

| Path | What it is |
|---|---|
| `trajectory.jsonl` | the training agent's full Claude Code stream (`--output-format stream-json`) — every message, tool call, and result |
| `eval_trajectory.jsonl` | the evaluator agent's stream |
| `experiment.jsonl` | the Experiment Journal — both agents append here (schema: [`../framework/journal/`](../framework/journal/)) |
| `run_metadata.json` | start/end, elapsed seconds, exit code, config |
| `program.md` | the prompt this run was given |
| `.claude/skills/` | the skill library as seeded into this workspace |
| `eval_agent_logs/` | per-checkpoint evaluator logs |
| `logs/`, `outputs/` | training logs and generation dumps, where the run produced them |
| `*.py`, `*.sh` | **agent-authored** training scripts, reward functions, and data preparation |
| `.eval_queue`, `.eval_processed`, `.timer` | the evaluation-request queue and the budget watchdog's state |

`human_aime2025_14ce9dfd/` additionally has `planning_trajectory.jsonl` (the
planning agent's stream), `human_plan_iteration_{1,2}.md` (the two proposed
plans), `human_guidance.jsonl` and `.human_decision_{1,2}.json` (the reviewer's
verdicts and stated reasons). The human reviewer rejected iteration 1 for
over-weighting SFT and accepted iteration 2; the 10-hour budget starts only
after acceptance, and the 793 s of human wait time is excluded from it.

The six autonomous runs of the controlled set came out of the benchmark
harness instead, so their layout is different and deliberately sparser — none of the framework's machinery
is present, which is the point of the condition:

| Path | What it is |
|---|---|
| `trajectory.jsonl` | the agent's stream as the harness recorded it |
| `program.md` | the prompt this run was given |
| `run_metadata.json` | elapsed, start/end, base model, budget, how the run ended, and final metrics where any exist |
| `metrics.json` | the harness's final evaluation of the submitted model — Codex runs only |
| `scripts/` | **agent-authored** data preparation, training and evaluation scripts |
| `logs/` | the training and evaluation logs the agent produced |
| `evals/` | the agent's own evaluation results, and `eval_log_summary.json` condensing its full evaluation logs |
| `*.md` | the agent's own notes, where it wrote any |
| `contamination_judgement.txt`, `disallowed_model_judgement.txt` | the harness's compliance verdicts on the run |
| `timer.sh` | the budget watchdog the agent could call |

There is no journal, no skill library, no evaluator agent, and no queue — an
autonomous agent has only its own context. `autonomous_aime2025_c7c4a0c4/` kept
no evaluation results at all; it submitted a model scoring 0.000.

Checkpoints, training data and generation dumps are excluded from every
directory (see below), so `scripts/` records what the agent wrote rather than
what it produced.

## Supplementary runs

The six remaining directories were recorded by the PostTrainBench harness in
September 2026, after the controlled set, and were reorganized into the layout
above. `autonomous_aime2025_99ac2f89/`, `autonomous_gsm8k_886c6165/` and
`autonomous_humaneval_e55852d6/` are three more autonomous Claude Code runs,
same prompt, same agent, same 10-hour budget. `fork_aime2025_b10da191/`,
`fork_gsm8k_4c81c492/` and `fork_humaneval_af9d89f6/` each continue one of
them: the workspace was restored to the state it was in at a chosen node of the
source trajectory — the agent's scripts, `summary.md`, evaluation outputs,
training logs, and a verbatim transcript of its own session up to that point,
but no weights, no training data and no inspect-ai dumps — the prompt was
extended with a continuation notice stating what was and was not restored, a
fresh budget, and the single hint *"Please evaluate whether the current
strategy needs adjustment."*, and the agent then ran autonomously.

| Run | Forked from | Fork node | Fresh budget |
|---|---|---|---:|
| `fork_aime2025_b10da191/` | `autonomous_aime2025_99ac2f89/`, line 5434 | Step 6 (`step_006_sft_v5_cont`) and its full 30-problem evaluation, ~4h48m in | 5h |
| `fork_gsm8k_4c81c492/` | `autonomous_gsm8k_886c6165/`, line 1234 | Run 2 (`step_002_sft_rawtext`, 42% on 50 samples) and its checkpoint, ~2h51m in | 7h |
| `fork_humaneval_af9d89f6/` | `autonomous_humaneval_e55852d6/`, line 4687 | Run 8 (`step_008_final_train`, full SFT on 17.4K thinking-augmented samples) and its first full 164-problem evaluation, ~5h14m in | 5h |

Their layout follows the autonomous table above, with these differences:

| Path | What it is |
|---|---|
| `trajectory.jsonl` | the agent's stream as PostTrainBench recorded it — for a fork run, **the continuation only** |
| `program.md` | the prompt; for a fork run, the source prompt plus local environment notes and the continuation notice |
| `run_metadata.json` | as above, plus `agent_config`, the harness's exit codes as `harness_validation`, and for a fork run a `fork` block (source archive, node, cut line, restored files, hint) |
| `metrics.json` | the harness's final evaluation of the submitted model (manual re-run for `fork_aime2025_b10da191/`, see above) |
| `evals/`, `logs/`, `scripts/` | as above; in a fork run they hold both what was restored from the source run and what the agent produced afterwards, named `<step directory>_<file>`. `fork_source/fork_manifest.json` says which is which |
| `data_manifests/` | `fork_aime2025_b10da191/` only: the agent's record of each generated dataset (size, sources, contamination hits); the data itself is removed |
| `summary.md` | the agent's own notes, restored at the fork and appended to afterwards |
| `fork_source.md`, `fork_source/` | fork runs only: the harness's description of the fork; `fork_manifest.json` (exactly what was restored, excluded or could not be replayed), `source_run_metadata.json`, `trajectory_until_fork.jsonl` (the prefix of the source run's stream that defines the fork state), and the restore tool's log |
| `fork_provenance/transcript_until_fork.md` | fork runs only: the human-readable rendering of that prefix, placed in the agent's workspace and pointed to by the prompt |

Two things the reference layout has and these do not. PostTrainBench writes no
`contamination_judgement.txt` / `disallowed_model_judgement.txt`; the checks it
does run — agent, final-evaluation, final-model and summary validation — are
recorded as exit codes under `harness_validation` in `run_metadata.json`, not
invented as verdict files. And it stamps no wall-clock times into the stream, so
`start` is `timer.sh`'s `CREATION_DATE` (for a fork run, the moment the fresh
budget began), `end` is the last write to the stream file, and `elapsed` is
their difference; the time the source run spent before the fork is not
included.

## What was removed

| Removed | Why |
|---|---|
| `checkpoints/`, `final_model/`, `sft_output*/` | model weights, up to 331 GB per run |
| `data/`, `train_data*.jsonl`, `tokenized_data*/` | agent-generated training data, up to 97 GB per run |
| `pass8_eval/` | 16 GB of post-hoc generation dumps |
| `judge_output.*`, `task/logs/` | per-sample judging and evaluation dumps, up to 150 MB per run; the scores in them survive in `evals/eval_log_summary.json` |
| `templates/` | chat templates supplied by the task environment, not written by the agent |
| `solve_parsed.txt`, `system_monitor.log`, harness console logs | derived from the stream, or machine-level telemetry |
| `ANALYSIS.md` | our own post-run notes, not part of the run |
| `.eval_session_id` | agent session identifier, no analytic value |
| `__pycache__/` | build artifacts |
| `workspace_checkpoints/`, `artifact_inventory.tsv`, `artifact_sizes.txt`, `base_model_manifest.tsv`, `run_status.md`, `*_exit_code.txt`, `workspace/logs/*.json` | PostTrainBench bookkeeping, step snapshots (up to 758 GB) and inspect-ai per-sample dumps in the six supplementary runs; the exit codes survive in `run_metadata.json`, the scores in `evals/eval_log_summary.json` |

Everything else is byte-for-byte as the run left it, with three exceptions:

**1. Skill renaming.** Three skills were named after the specific trainer used
in our runs and are released under the generic names used in the paper. The
rename is applied to directory names *and* to every reference inside
`trajectory.jsonl`, `eval_trajectory.jsonl`, the evaluator logs, and the skill
files themselves, so the archives stay internally consistent:

| Original | Here |
|---|---|
| `verl-known-pitfalls` | `posttraining-known-pitfalls` |
| `verl-parquet-schema` | `data-parquet-schema` |
| `grpo-lora-verl` | `grpo-lora-config` |

Only the identifier changed; skill contents are untouched. The third skill was
authored in an earlier AIME run and does not appear in these archives, and the
autonomous runs carry no skills at all.

**2. Redactions.** Three kinds, all mechanical:

*Credentials.* Each Codex run's stream opens with the harness echoing the agent
provider and its API key. That one token per file is replaced with
`sk-[REDACTED]`. The other seven runs contain none.

*Account balances.* Our API provider returns `403` quota errors whose message
text quotes the account balance. In
`experience_humaneval_d26cfb40/trajectory.jsonl` the four such messages are
replaced wholesale with
`403 pre-charge authorization failed (insufficient account balance)` — this is
why that run terminated at turn 411 rather than on its time budget. Elsewhere
only the figures are replaced, with `$[REDACTED]`, leaving the message
otherwise intact: 36 figures across 12 files, being `trajectory.jsonl` and
`eval_trajectory.jsonl` for `experience_aime2025_c247e78e` and
`experience_gsm8k_855100f4` plus their per-checkpoint evaluator logs, and 4 more
in `autonomous_aime2025_250c7e3e/trajectory.jsonl`, where the same error ended
the run at 8h 53m. Error types, timings and turn counts are unchanged
throughout.

**3. One trimmed retry loop.** In `autonomous_humaneval_e55852d6/` the agent's
last productive invocation ended about 7h08m in with a `Prompt is too long`
API error. The harness's resume loop then re-invoked it 61 more times over the
next 40 minutes; every attempt failed immediately with an HTTP 403 rate-limit
error, producing a `system`/`init` record, an error `result` and the harness's
resume notice, with no assistant content and no tool call. Those 61
invocations (lines 5658–6024 of the recorded stream) are removed;
`trajectory.jsonl` ends at line 5657, the `result` of the 20th invocation, and
lines 1–5657 are byte-for-byte as recorded. `run_metadata.json` documents the
cut under `stream_trimmed`. Before the cut this directory's id was `7d7f21b3`;
`fork_humaneval_af9d89f6/` was forked from that release at line 4687, inside
the kept part, so its `fork_source/` files still name the source archive
`autonomous_humaneval_7d7f21b3`, and its `trajectory_until_fork.jsonl` holds
the same records as lines 1–4693 of the trimmed file, differing only in the
44 lines where the restore tool rewrote the source workspace path to the fork's
own.

*Host paths.* `experience_aime2025_c247e78e/trajectory.jsonl` contains a
directory listing of a shared model store in which three symlink targets carry
our cluster account name; those are rewritten to `/home/user`. The autonomous
runs reference the base model by its absolute path on the same store, rewritten
the same way — 36, 24 and 79 occurrences in the Codex runs, 35, 55 and 66 in the
Claude Code ones. Container-internal paths (`/workspace/AI4AI/...`,
`/home/ben/task/...`) are left alone — the evaluator log filenames encode them,
so rewriting them would desynchronize the archive from itself.

The six supplementary runs ran on a different cluster account:
`/home/test/test12/huangxin` for the three autonomous runs,
`/home/test/test06/huangx` for the three fork runs. Both are rewritten to
`/home/user`, in path form and in the slugified form Claude Code uses for
session directories (`-home-test-…` → `-home-user`); in the fork runs the shared
HuggingFace cache `/home/test/.cache` is rewritten to `/home/user/.cache` as
well. Fragments of these paths remain inside `input_json_delta` records where
the streaming API split them across token boundaries (in
`autonomous_aime2025_99ac2f89/` and in the three fork runs — 17, 7 and 5
fragments); rewriting a fragment would desynchronize the deltas from the tool
input they reassemble into, so they are left as they are. None of the six
streams contains credentials or account balances.

## Reading a trajectory

[`../analysis/pipeline/`](../analysis/pipeline/) has a parser for each stream
format. Both return `(records, stats)` and take file *contents*, not a path.

For the framework and human runs, `trajectory.jsonl` is one JSON object per line
in Claude Code's stream format — `system` init, then alternating `assistant` /
`user` records carrying tool calls and their results, then a final `result`
record:

```python
from pathlib import Path
from analysis.pipeline.parse_claude import parse_claude_records

records, stats = parse_claude_records(
    Path("trajectories/experience_aime2025_c247e78e/trajectory.jsonl").read_text()
)
```

The three Claude Code autonomous runs of the controlled set carry the same
records, but as the benchmark harness wrote them: every JSON line is prefixed with a wall-clock
stamp, `[2026-06-09T06:26:38Z] {...}`, and the container's startup banner
occupies the first 15 lines. `parse_claude_records` reads them as they are — it
scans past any prefix to the first `{` and skips lines that hold no JSON object,
reporting them in `stats["warnings"]`.

The six supplementary runs carry the same Claude Code records with no timestamp
prefix — PostTrainBench does not stamp its stream — and again open with the
container banner. Each is a single `session_id`, but the harness re-invokes the
agent in that session whenever it returns before the budget is spent, and every
invocation adds a `system`/`init` and a `result` record: 2 in
`fork_gsm8k_4c81c492/`, 3 in `fork_humaneval_af9d89f6/` and
`autonomous_aime2025_99ac2f89/`, and 20 in `autonomous_humaneval_e55852d6/`
(see the trimming note below). No single `duration_ms` is the run's wall
clock. A fork run's `fork_source/trajectory_until_fork.jsonl` parses the same
way.

The Codex runs keep that harness's own event format instead, stamped the same
way, with `thread.started`, `turn.*` and `item.*` events in place of Claude's
message records:

```python
from analysis.pipeline.parse_codex import parse_codex_records

records, stats = parse_codex_records(
    Path("trajectories/autonomous_gsm8k_5dcf0c73/trajectory.jsonl").read_text()
)
```

These are the same formats, and the same parsers, that the pipeline uses for the
wider corpus — `config.json` lists `solve_out.txt` and `trace.txt` as the two
stream sources, and the autonomous files here are the former, renamed.

One archive does not end on a clean JSON line. When our watchdog reaches the
wall-clock budget it kills the agent process, and the shell's `Killed` notice is
teed into the stream: `human_aime2025_14ce9dfd/trajectory.jsonl` line 1003 is
exactly that. Parsers must skip lines that fail to decode — the ones in
`analysis/pipeline/` do — and that line is also how you tell a budget-exhausted
run from one that stopped on its own.

For the decision-level view of a framework run, read `experiment.jsonl` instead
— it is two orders of magnitude smaller and holds the agent's own account of
what it planned, what it expected, and what it concluded. The autonomous runs
have no equivalent; that absence is the finding.

## Scope

The ten controlled runs are the controlled arm of the study; the six
supplementary runs were recorded later, on a different cluster, and are not
part of any of the paper's numbers. The broader corpus the
statistics in the paper are computed over — 1,338 trajectories across 5 agent
harnesses, 7 benchmarks and 4 base models — is not redistributed here; its
annotations are in [`../analysis/annotations/`](../analysis/annotations/). The
autonomous runs were recorded by the same benchmark harness that produced that
corpus, which is why the pipeline's parsers read them unchanged, but they are
separate local runs and are not among the 1,338.

The AIME campaign ran nine times under the framework. The ninth, with all three
components in place, is the one archived here; the additional ten skills in
[`../framework/skills/skills/`](../framework/skills/skills/) were written by the
agent during runs 3, 4, 6 and 7, which are not included.

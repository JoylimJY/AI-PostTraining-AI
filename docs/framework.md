# The experience-driven framework

The paper compares two conditions: a **bare agent**, which is given a base model, a benchmark, a
GPU, and ten hours; and a **scaffolded agent**, which is given the same thing plus an
experience-driven framework. This document describes that framework, the run loop it sits in, and
where each piece lives in this repository.

Adding the framework is worth **+12.6 points on GSM8K** and **+30.8 points on HumanEval** over the
same agent running autonomously, closing **75.1%** of the gap to the official instruct model
against **48.6%** autonomous. It makes the agent a better *executor* — fewer wasted hours, fewer
repeated crashes, tighter experiment hygiene. It does not make the agent a better *strategist*:
scaffolded trajectories lock in on their first strategy at essentially the same rate as bare ones.
The agent adopts **22 of 22** execution-level suggestions from the evaluator and **0 of 21**
strategy-level ones. That gap is the paper's central finding, and this framework is the strongest
scaffold we could build that still fails to close it.

Both agents run Claude Code with Opus 4.6. Preliminary runs on this setting found Opus 4.6 more
reliable than Opus 4.8, Opus 5 and Fable 5: the newer models either varied widely across runs or
contaminated the training data (train-on-test), which is outside the scope of this study.

---

## Three components

### 1. Experiment journal — `framework/journal/`

An append-only log the agent writes to as it works. It is the agent's only durable memory across
the run: context is compacted, but the journal is not.

Five entry types carry the analysis, each written as a JSON object:

| Type | Written by | Written when | Required fields |
|---|---|---|---|
| `plan` | training agent | Before launching a training experiment | `hypothesis`, `success_criteria`, `abort_criteria` |
| `observation` | training agent | On anything unexpected | free-form |
| `lesson` | training agent | After reading an evaluation result | what happened, what it means, what to do differently |
| `eval_result` | evaluator agent | After scoring a checkpoint | raw score, invalid rate, error breakdown |
| `eval_analysis` | evaluator agent | After reading the per-problem log | predicted vs. actual, gap reason, recommendations |

`program.md` offers two further types the agent may use at its discretion, `reflection` and
`skill_created`; the full schemas are in
[`framework/journal/README.md`](../framework/journal/README.md). `skill_created` is never written
in any released run — see the skill library below.

The `plan` schema is the load-bearing one. Requiring `success_criteria` **and** `abort_criteria`
*before* a job launches is what makes strategy revision measurable at all: it commits the agent
in advance to a condition under which it would abandon the current approach. The paper's finding
is that agents write abort criteria faithfully and then, when those criteria are met, revise
hyperparameters rather than strategy. The journal records the evidence plainly — on HumanEval it
carries the agent's own "SFT plateau confirmed" and the evaluator's "ABANDON FURTHER SFT: v5
proves diminishing returns" — and the run continues with more SFT variants regardless.

### 2. Skill library — `framework/skills/`

Two layers:

The library is built by distillation, before the campaign, in three compressions: 908 documents
(≈937K words) scraped from the documentation, training recipes and issue threads of verl, TRL,
OpenRLHF, NeMo-RL and slime → a 60-page wiki (≈20K words) → one `SKILL.md` per topic (≈1.2K words
each).

**`framework/skills/skills/`** — 15 skills, each a directory containing a `SKILL.md` with YAML
frontmatter (`name`, `description`) and a procedural body. Skills are loaded by name on demand,
so the library can grow past what fits in context.

| Skill | Covers |
|---|---|
| `create-skill` | The meta-skill: how to write a new skill from a lesson |
| `rl-experiment-discipline` | One variable at a time; log before launch; never trust an unevaluated checkpoint |
| `sft-cold-start-gate` | When SFT is a prerequisite for RL and when it is a detour |
| `escalate-rl-algorithm` | Moving up the algorithm ladder when a simpler method plateaus |
| `grpo-defaults`, `ppo-defaults` | Known-good starting configurations |
| `grpo-lora-config` | GRPO combined with low-rank adaptation |
| `tune-rl-memory-throughput` | Batch size, sequence length, and offload trade-offs on one 80GB GPU |
| `monitor-rl-training` | What to watch during a run and when to intervene |
| `diagnose-silent-rl-failures` | Runs that complete cleanly and learn nothing |
| `triage-training-collapse` | Loss spikes, reward collapse, degenerate outputs |
| `fix-train-infer-mismatch` | Divergence between training-time and inference-time behavior |
| `rl-chat-tokenizer-pitfalls` | Chat templates, special tokens, and masking errors |
| `posttraining-known-pitfalls` | Cross-cutting failure modes seen across the corpus |
| `data-parquet-schema` | The on-disk schema the training data must conform to |

Five of the fifteen are the **seed skills** the agent starts every run with —
`posttraining-known-pitfalls`, `diagnose-silent-rl-failures`, `data-parquet-schema`,
`monitor-rl-training`, `create-skill` — covering crash and silent-failure diagnosis, generic RL
triage, data formatting, runtime health, and the persistence of new experience. The other ten are
additional distilled knowledge the agent **consulted** during the AIME campaign runs 3, 4, 6 and 7.

**No skill in this library was authored by an agent.** Despite the `create-skill` meta-skill being
present and the library being heavily read — the agent consults skills 18 times per run on GSM8K,
20 on HumanEval and 60 on AIME 2025 — *the agent creates no new skill in any run*: no `Write` or
`Edit` call in any stream of any released run targets a path inside `skills/`. The asymmetry
between consuming knowledge and producing it mirrors the adoption gap between execution-level and
strategy-level suggestions. (In the AIME 2025 runs with human guidance at the initial decision,
consultation drops to about twice per run: once the strategy is handed to it, the agent stops
looking things up.)

Three skills were named after the specific library used in our runs, and are released under
generic names matching the paper's terminology:

| Original name | Released as |
|---|---|
| `verl-known-pitfalls` | `posttraining-known-pitfalls` |
| `verl-parquet-schema` | `data-parquet-schema` |
| `grpo-lora-verl` | `grpo-lora-config` |

Two skills reference names that no released skill provides (`async-rl-escalation`,
`design-verifiable-reward`). These dangling references are left in place rather than repaired, so
that what the agent read is what is released.

**`framework/skills/wiki/`** — a reference wiki the agent reads but does not train on: 11
`entities/` pages (libraries, models, benchmarks), 21 `concepts/` pages (algorithms, objectives,
failure modes), 20 `experience/` pages (accumulated findings), and 8 `sources/` pages summarizing
upstream post-training libraries. `AGENT.md` tells the agent how to navigate it; `index.md` and
`log.md` are the entry point and change log.

The upstream repositories the `sources/` pages summarize are pinned as git submodules under
`framework/skills/wiki/sources/upstream/` — verl, TRL, OpenRLHF, NeMo-RL, slime, and Miles — at
the commits the agents actually read. The 908 raw scraped documents behind those summaries are not
released.

### 3. Evaluator agent — `framework/evaluator/`

A second agent, running in its own process against the same workspace, that owns benchmark
scoring. Separating it from the training agent does two things: it keeps GPU-bound evaluation off
the training agent's critical path, and it prevents the training agent from grading its own work.

Its loop is three steps per checkpoint, defined in each experiment's `eval_program.md`:

1. **Predict** — before scoring, write down the expected result and why. This turns every
   evaluation into a falsifiable test rather than a lookup.
2. **Evaluate** — run the benchmark harness (`evaluation/<benchmark>/evaluate.py`) and record the
   score.
3. **Analyze** — compare the prediction to the outcome, and write the delta back to the journal
   as a `lesson` if they disagree.

Each step emits a JSON object against a fixed schema, which is what makes the 2,034 evaluation
points in the corpus machine-readable.

The analysis step is where the framework's limit shows. Classifying every recommendation the
evaluator makes in one representative run per benchmark, by whether it departs from the committed
strategy:

| Benchmark | Eval cycles | Execution suggestions (adopted) | Strategy suggestions (adopted) |
|---|---:|---:|---:|
| GSM8K | 11 | 6 / 6 | **0 / 7** |
| HumanEval | 14 | 11 / 11 | **0 / 11** |
| AIME 2025 | 5 | 5 / 5 | **0 / 3** |
| Total | 30 | **22 / 22** | **0 / 21** |

On HumanEval, 11 of the 14 cycles recommend RL; the agent writes GRPO scripts and launches 14 SFT
variants and no RL training. On AIME 2025 the evaluator proposes an SFT warm-up three times and
the agent continues GRPO-only. The evaluator is not being ignored — every suggestion it makes
*within* the strategy is implemented. Only the ones that would leave it are declined.

---

## The run loop

```
  training agent                          evaluator agent
  ──────────────                          ───────────────
  read journal + skills + wiki
  write `plan` entry
  launch training job  ──────►  checkpoint
                                   │
                                   ├─► append to .eval_queue
                                   │
  poll .eval_processed  ◄──────────┼──  predict
        │                          │    evaluate  (evaluation/<bench>/evaluate.py)
        │                          │    analyze
        │                          └──  append to .eval_processed
        ▼
  write `lesson` / `reflection`
  may write a skill (`create-skill`) — never exercised in any released run
  next experiment  ────────────────►  (repeat until .timer expires)
```

The two agents communicate through the filesystem, not a message bus: `.eval_queue` is a
checkpoint request queue, `.eval_processed` carries results back, and `.timer` holds the run
deadline. This is deliberately crude — it survives either agent crashing and restarting, which
happens over a ten-hour unattended run.

The **polling protocol** matters more than it looks. An agent that blocks on evaluation burns its
budget waiting; an agent that never checks trains blind. `program.md` specifies that the training
agent must poll between experiments and must not launch a follow-up experiment that depends on an
unreturned evaluation.

### Which part of the loop actually closes

The loop above is designed to close at both levels: evidence from an evaluation is supposed to
feed back into either a repair or a revision. In practice only one arrow is ever taken.

```
assumed: globally closed            observed: locally iterative, globally linear

  Strategy → Execute → Evaluate       Strategy → Execute → Evaluate
      ↑__________________|                          ↑________|
          revise strategy                          repair & retry
                                              (revision not taken)
```

Everything in this document — the journal, the wiki, the seeded skills, the separate evaluator —
makes the inner arrow tighter and better informed. None of it causes the outer arrow to be taken.

### Harness

Trajectories are produced by driving a coding agent CLI non-interactively. For the Claude Code
condition:

- Claude Code **2.1.150**, agent model `claude-opus-4-6`
- `--output-format stream-json`, streamed to `trajectory.jsonl` — this file is the raw record the
  entire analysis pipeline consumes
- `--allowedTools` scoped to exactly the tools the run needs, so the trajectory is a closed system
- one base model, one benchmark, 10 hours wall clock, 1× H100 80GB, no human in the loop

The analyzed PostTrainBench corpus spans **20 agent-model configurations across three agent
frameworks** — Claude Code, Codex CLI and OpenCode — driven equivalently. (The GLM-X and Qwen3-Max
configurations in the released tables run under Claude Code, and are pooled into it; the raw
`harness_family` column in `analysis/annotations/` keeps them separable.) Their trajectory formats
differ, which is why `analysis/pipeline/` carries a parser per format (`parse_claude.py`,
`parse_codex.py`, `parse_trace.py`).

---

## Where things are

| Component | Prompts / config | Released trajectory |
|---|---|---|
| Training agent | `experiments/<benchmark>/program.md`, `config.yaml`, `start.sh` | `trajectories/<benchmark>/run_*/` |
| Evaluator agent | `experiments/<benchmark>/eval_program.md`, `start_eval.sh`, `request_eval.sh` | `trajectories/<benchmark>/run_*/eval_agent_logs/` |
| Journal | schemas in `program.md` | `trajectories/<benchmark>/run_*/` journal files |
| Skill library | `framework/skills/skills/` | `trajectories/<benchmark>/run_*/.claude/skills/` |
| Wiki | `framework/skills/wiki/` | — |
| Scoring | `evaluation/<benchmark>/evaluate.py` | `trajectories/<benchmark>/run_*/outputs/` |

---

## Human guidance: the two decision points

The `human_guidance` condition is the one exception to the no-human rule, and it is the paper's
probe for whether lock-in is a capability limit or a decision limit. It intervenes at two
different points, and they do not behave the same way.

**Before training — a human review of the initial strategy.** The agent proposes its strategy as a
complete research plan; the reviewer returns a fixed-format JSON decision that either approves it
or requests a revision with an explicit rationale, iterating until approval. On AIME 2025 the
agent proposes an SFT pipeline, the reviewer asks that the main budget go to RL, and the agent
then inspects the base model, finds the required output format already reachable without SFT, and
*skips the warm-up entirely* — implementing and extending a strategy that was not its own. It then
locks into that strategy exactly as it locks into its defaults: best score of 3/30 (10.0% pass@8)
reached early, and the rest of the budget spent tuning hyperparameters back and forth and
re-deriving how to resume from an earlier checkpoint. **A review before training changes *which*
strategy the agent locks into, not *whether* it locks in.** The prompts and the JSON decision
schema are in `experiments/human_guidance/`; a complete run with its two recorded decisions is in
`trajectories/human_aime2025_14ce9dfd/`.

**Mid-run — a single instruction to switch.** Forking a completed autonomous run at a mid-run
checkpoint and instructing the agent to switch strategy beats that run's own recorded continuation
under the same remaining budget on all three benchmarks, by up to 17.44 points on GSM8K. The
shared prefix has already secured the prerequisites of the alternative — format compliance from
the early SFT — so the switch is well primed at the branch point, while the agent's own
continuation keeps refining a strategy whose returns have flattened.

**The control that separates the two.** Forking the same checkpoints with an instruction merely to
*reconsider* the current strategy, without naming an alternative, produces no switch in any fork:
the agent reaffirms what it is doing and proceeds as its recorded continuation does. So what is
missing is not the prompt to deliberate, and not the ability to execute something else. It is the
decision itself.

This is also the paper's proposed training signal: the "continue" and "switch" branches from one
checkpoint under one remaining budget are a controlled comparison of a strategy-level decision,
generated automatically from runs that already happened.

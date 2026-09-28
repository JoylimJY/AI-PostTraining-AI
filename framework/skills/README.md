# Skill Library

Two layers:

| Layer | Directory | What it is |
|---|---|---|
| Skills | [`skills/`](skills/) | 15 procedural entries, each a `SKILL.md` with a `name`/`description` front matter block. Loaded by name when the agent hits a matching problem. |
| Wiki | [`wiki/`](wiki/) | The knowledge base the skills were distilled from: entities, concepts, experience notes, and per-source summaries of six open-source post-training frameworks. |

Both were built by us, before the experiment campaign, in three successive
compressions: **908 documents (≈937K words)** scraped from the documentation,
training recipes, and issue threads of verl, TRL, OpenRLHF, NeMo-RL and slime
→ a **60-page wiki (≈20K words)** → one **`SKILL.md` per topic (≈1.2K words)**.

## Skills

Five skills (`create-skill`, `diagnose-silent-rl-failures`,
`monitor-rl-training`, `posttraining-known-pitfalls`, `data-parquet-schema`)
are the **seeds**: every run starts with these in `.claude/skills/`. They cover
crash and silent-failure diagnosis, generic RL triage, data formatting, runtime
health, and the persistence of new experience.

The other ten are further distilled knowledge that the agent **consulted**
during the AIME campaign runs 3, 4, 6 and 7. They record what it read, not what
it wrote.

### No skill here was written by an agent

The prompt does instruct the agent to create or update a skill whenever it
writes a `lesson` involving a configuration change, a fix, or a non-obvious
finding, and to **empty** a skill that gave bad advice. The `create-skill`
meta-skill is present in every run, and the agent does draw on the library
unprompted: **18 times per run on GSM8K, 20 on HumanEval and 60 on AIME 2025**
(Appendix C.2).

Nevertheless, **the agent creates no new skills in any released run**, and no
`skill_created` journal entry appears anywhere in the corpus — no `Write` or
`Edit` call in any stream of any run ever targets a path inside `skills/`. The
asymmetry between consuming existing knowledge and producing reusable knowledge
parallels the adoption gap between execution-level and strategy-level
suggestions: the agent uses what is handed to it and does not extend it.

In the AIME 2025 runs with human guidance at the initial decision, the agent
consults the library only about twice per run: once the strategy is handed to
it, it stops looking things up.

### Renaming

Three skills were named after the specific trainer used in our runs. They are
released under the generic names used in the paper. The rename is applied
consistently to directory names, front matter, cross-references, and to the
copies archived under [`../../trajectories/`](../../trajectories/):

| Original name | Released as |
|---|---|
| `verl-known-pitfalls` | `posttraining-known-pitfalls` |
| `verl-parquet-schema` | `data-parquet-schema` |
| `grpo-lora-verl` | `grpo-lora-config` |

Skill *contents* are otherwise unmodified. Two cross-references
(`async-rl-escalation`, `design-verifiable-reward`) point at skills that no
released skill provides. They are left in place rather than repaired, so that
what the agent read is exactly what is released.

## Wiki

`wiki/AGENT.md` is the schema and maintenance protocol the agent follows.
`wiki/index.md` and `wiki/log.md` are its table of contents and ingestion log.

| Directory | Pages | Contents |
|---|---|---|
| `wiki/entities/` | 11 | frameworks, models, datasets |
| `wiki/concepts/` | 21 | algorithms and failure modes |
| `wiki/experience/` | 20 | cross-cutting lessons |
| `wiki/sources/` | 8 | one summary per ingested upstream source |

The raw ingested corpus (908 documents) is not redistributed. `wiki/sources/`
instead pins the upstream repositories as git submodules — see
[`wiki/sources/README.md`](wiki/sources/README.md).

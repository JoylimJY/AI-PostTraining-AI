# Experience-Driven Framework

The three components the paper adds on top of a stock coding agent, so that
experience accumulated inside one session survives context truncation and
carries across sessions.

| Component | Directory | Role |
|---|---|---|
| Experiment Journal | [`journal/`](journal/) | Append-only decision log the agent writes before and after every experiment |
| Skill Library | [`skills/`](skills/) | Reusable procedures, distilled from open-source post-training projects, that the agent reads when stuck |
| Evaluator Agent | [`evaluator/`](evaluator/) | A separate agent that predicts, measures, and analyses every checkpoint |

All three are *agent-facing*: they are specified in natural language in the
prompts, not enforced by code — which is precisely what makes the resulting
artifacts evidence about agent behaviour rather than about the harness.

They differ in where their contents come from. The **journal** is written by
the agent and the evaluator at run time. The **skill library** and its wiki are
compiled by us *before* the campaign and supplied read-only-by-convention: the
prompt invites the agent to extend them, and it never does (see
[`skills/README.md`](skills/README.md)).

The journals and evaluator logs produced during the runs analysed in the paper
are archived under [`../trajectories/`](../trajectories/); the skill library and
wiki checked in under `skills/` are the state at the end of the experiment
campaign, which is also their state at the beginning.

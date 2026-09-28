# Pilot Study: cross-scaffold method audit

## Core finding

Across all seven shared benchmarks, all four shared base models, and the same 10-hour single-H100 budget, the two scaffolds do not converge on the same supervised fine-tuning implementation.
Among Claude's identifiable initial methods, Full SFT accounts for 163/202 (80.7%); among Codex's identifiable initial methods, LoRA/PEFT accounts for 268/299 (89.6%).
The direction is consistent: in 28/28 matched cells Claude leans towards Full SFT, and in 28/28 cells Codex leans towards PEFT; the mean gaps are 71.7 and 72.9 percentage points respectively.
In the Qwen3-1.7B-Base slice, the one closest to our controlled baseline, Claude's Full SFT commands are 123/148 (83.1%), and Codex's PEFT commands are 300/349 (86.0%).

## Cross-scaffold comparison

| Scaffold | Benchmark | Final accuracy (n) | Dominant initial method | Initial label coverage | Method-labelled training commands | Dominant command method | Objective switches |
|---|---|---:|---:|---:|---:|---:|---:|
| Claude | AIME 2025 | 0.047 (31) | Full SFT (76.0%) | 75.8% | 67/158 (42.4%) | Full SFT (70.1%) | 12/124 (9.7%) |
| Claude | ArenaHardWriting | 0.142 (32) | Full SFT (93.1%) | 80.6% | 86/204 (42.2%) | Full SFT (72.1%) | 3/164 (1.8%) |
| Claude | BFCL | 0.877 (42) | Full SFT (80.5%) | 95.3% | 133/207 (64.3%) | Full SFT (75.9%) | 0/157 (0.0%) |
| Claude | GPQA Main | 0.283 (34) | Full SFT (64.0%) | 64.1% | 92/213 (43.2%) | LoRA/PEFT (52.2%) | 0/163 (0.0%) |
| Claude | GSM8K | 0.544 (35) | Full SFT (88.5%) | 66.7% | 76/219 (34.7%) | Full SFT (80.3%) | 3/177 (1.7%) |
| Claude | HealthBench | 0.281 (36) | Full SFT (78.6%) | 75.7% | 83/216 (38.4%) | Full SFT (79.5%) | 0/169 (0.0%) |
| Claude | HumanEval | 0.487 (37) | Full SFT (82.1%) | 71.8% | 84/233 (36.1%) | Full SFT (72.6%) | 0/178 (0.0%) |
| Codex | AIME 2025 | 0.009 (43) | LoRA/PEFT (97.5%) | 90.9% | 176/220 (80.0%) | LoRA/PEFT (95.5%) | 3/120 (2.5%) |
| Codex | ArenaHardWriting | 0.109 (39) | LoRA/PEFT (74.4%) | 88.6% | 168/215 (78.1%) | LoRA/PEFT (84.5%) | 10/159 (6.3%) |
| Codex | BFCL | 0.573 (44) | LoRA/PEFT (97.7%) | 95.6% | 216/237 (91.1%) | LoRA/PEFT (98.1%) | 0/67 (0.0%) |
| Codex | GPQA Main | 0.277 (46) | LoRA/PEFT (91.1%) | 97.8% | 231/267 (86.5%) | LoRA/PEFT (92.2%) | 0/152 (0.0%) |
| Codex | GSM8K | 0.443 (47) | LoRA/PEFT (83.7%) | 87.8% | 211/309 (68.3%) | LoRA/PEFT (78.7%) | 0/198 (0.0%) |
| Codex | HealthBench | 0.231 (42) | LoRA/PEFT (85.7%) | 97.7% | 164/193 (85.0%) | LoRA/PEFT (94.5%) | 0/106 (0.0%) |
| Codex | HumanEval | 0.332 (47) | LoRA/PEFT (95.7%) | 95.9% | 314/334 (94.0%) | LoRA/PEFT (96.5%) | 0/141 (0.0%) |

Final accuracy is the mean over trajectories that trained and produced a valid final accuracy. It is interpretable only within a benchmark: it is not aggregated across benchmarks and is not a causal estimate of the scaffold's effect. The denominator of the dominant-method share is the set of identifiable methods, so the table also reports method-labelled commands / verified training commands coverage.

## Interpretation

The result separates two layers. At the objective layer both scaffolds concentrate heavily on supervised likelihood; at the update-mechanism layer they concentrate on Full SFT and LoRA/PEFT respectively. If task demand alone determined the reasonable strategy, matched task cells should push both scaffolds towards the same implementation mechanism. The stable opposing preferences we observe are therefore not consistent with that simple account, and are better predicted by scaffold-specific priors or default tooling habits.

This evidence remains observational rather than causally identified: agent model, interface, prompt and scaffold are not independently randomised, and the method labels do not cover every training command. The conclusion should be stated as `inconsistent with a task-demand-only account` or `suggestive of scaffold-specific priors`, not as `proves scaffold causality`.

## Measurement layers

- `Dominant initial method`: the first identifiable method-family label in each trajectory that trained.
- `Dominant command method`: training episodes that contain a training action and whose method family is identifiable.
- `Objective switches`: switches between adjacent identified experiments at the canonical objective layer. Full SFT and PEFT are both supervised likelihood, so swapping one for the other is not an objective switch.
- `Final accuracy`: the mean over trajectories that trained and produced a valid final accuracy, reported per benchmark.

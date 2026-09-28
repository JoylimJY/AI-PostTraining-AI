# PostTrainBench trajectory summary

## Run metadata

- Benchmark: gsm8k
- Base model: /home/user/models/Qwen3-1.7B-Base
- Hardware: 4 x Nvidia A800 (80GB each)
- Original time budget: 10 hours (run started 2026-09-02T00:50:51+0800)
- **Fork continuation**: Forked from Run 2 (step_002, 42% on 50 samples) on 2026-09-25
- **Continuation budget**: 7 hours fresh (started ~2026-09-25T00:59+0800)
- Agent: Claude Code / claude-opus-4-6
- Key packages: transformers 4.57.3, trl 0.27.2, peft 0.18.1, torch 2.8.0, vllm 0.11.0, flash_attn 2.8.3
- Note: Model weights from prior steps were not preserved in fork; scripts and configs were. Retraining from base model.

## Step-by-step training log

### Step 0: Baseline evaluation
- Timestamp: 2026-09-02T00:52:00+0800
- Goal: Evaluate base model on GSM8K to establish baseline
- Status: COMPLETED
- Command: `python evaluate.py --model-path /home/user/models/Qwen3-1.7B-Base --limit 50`
- Result: accuracy=0.200, stderr=0.057
- Next decision: Train SFT model on GSM8K train data

### Step 1: SFT training with chat messages format
- Timestamp: 2026-09-02T01:15:00+0800
- Goal: Full-parameter SFT on GSM8K train data using chat message format
- Input checkpoint: /home/user/models/Qwen3-1.7B-Base
- Data: GSM8K train (29,892 samples in chat messages format)
- Hyperparameters: lr=2e-5, epochs=3, batch=4, grad_accum=4, max_seq_len=2048, warmup=0.05, cosine schedule
- Output: artifacts/steps/step_001_sft_gsm8k_full/output
- Training loss: 0.6 -> 0.13 over 1404 steps (~81 min)
- Status: COMPLETED (training), FAILED (evaluation)
- Evaluation: accuracy=0.000 on 50 samples
- Diagnosis: Model generates continuously without stopping at <|im_end|>. The SFTTrainer "messages" format doesn't match eval template.
- Next decision: Retrain with raw text format

### Step 2: SFT training with raw text format
- Timestamp: 2026-09-02T02:50:00+0800
- Goal: Full-parameter SFT with properly formatted raw text including chat template tokens
- Input checkpoint: /home/user/models/Qwen3-1.7B-Base
- Data: GSM8K train (29,892 samples: 7473 no-fewshot + 7473 fewshot + 14946 repeated)
- Hyperparameters: lr=2e-5, epochs=3, batch=4, grad_accum=4, max_seq_len=2048, warmup=0.05, cosine schedule
- Output: artifacts/steps/step_002_sft_rawtext/output
- Training loss: ~0.6 -> ~0.13 over 1404 steps (~81 min)
- Status: COMPLETED
- Evaluation: accuracy=0.420, stderr=0.071 on 50 samples
- Analysis: Big improvement from 20% baseline! Model now properly stops at <|im_end|>. Output tokens reasonable (9k vs 100k).
- Next decision: Try more focused training - only fewshot-format data, more epochs, try different LR

### Step 3: Diverse math SFT (continuation run)
- Timestamp: 2026-09-25T01:00:00+0800
- Goal: Large-scale SFT with diverse math data (GSM8K 4x oversampled + OpenMathInstruct-2 + NuminaMath-CoT + orca-math)
- Input checkpoint: /home/user/models/Qwen3-1.7B-Base (fresh, prior weights lost in fork)
- Data: artifacts/training_data/train_v4.jsonl (104,892 samples)
  - GSM8K train x4: 29,892
  - OpenMathInstruct-2 (gsm8k+augmented_gsm8k): 40,000
  - NuminaMath-CoT (orca_math+gsm8k+cn_k12+synthetic_math): 20,000
  - orca-math-word-problems: 15,000
- Hyperparameters: lr=2e-5, epochs=2, batch=4/gpu, grad_accum=4, effective_batch=64, max_seq_len=2048, warmup=0.03, cosine schedule
- Command: `torchrun --nproc_per_node=4 train_sft_v3.py --output-dir artifacts/steps/step_003_diverse_sft/output`
- Status: COMPLETED (training), FAILED (evaluation)
- Output: artifacts/steps/step_003_diverse_sft/output
- Training: 3278 steps, 115 min, final train_loss=0.312, mean_token_accuracy=0.912
- Evaluation: accuracy=0.080 (4/50) on 50 samples, stderr=0.039
- Diagnosis: (a) Training data had NO few-shot system message, but eval ALWAYS prepends
  a 10-shot system message. Model therefore generates repeated problems and never stops
  after the first answer. (b) Diverse datasets (OpenMathInstruct/Numina/orca) taught the
  wrong reasoning style; eval expects raw GSM8K `<<calc>>`-annotated reasoning.
  Direct greedy test with the eval prompt DOES stop correctly and formats ANSWER: right,
  confirming the issue is few-shot distribution mismatch + sampling, not base capability.
- Next decision: Build data that EXACTLY mirrors the eval prompt (10-shot system message,
  same user template, raw GSM8K calculator reasoning); drop off-distribution datasets.

### Step 4: Few-shot-aligned GSM8K SFT
- Timestamp: 2026-09-25T20:05:00+0800
- Goal: Fix the distribution mismatch. Train on prompts that exactly mirror the eval prompt
  (10-shot system message + exact user template + raw GSM8K reasoning with <<calc>>).
- Input checkpoint: /home/user/models/Qwen3-1.7B-Base
- Data: artifacts/training_data/train_v5.jsonl (22,419 samples; GSM8K train only)
  - exact_eval_fewshot: 7,473 (system msg = exact eval 10-shot set, shuffle seed 42)
  - random_fewshot: 7,473 (random 10-shot system message per sample)
  - no_fewshot: 7,473
- Rationale: run 2 (42%) had few-shot data; run 3 (8%) did not and never stopped generating.
  Verified the exact eval few-shot system message is reproducible (byte-identical, 5872 chars).
- Hyperparameters: lr=2e-5, epochs=3, batch=4/gpu, grad_accum=4, effective_batch=64, max_seq_len=3072, warmup=0.03, cosine
- Command: `torchrun --nproc_per_node=4 train_sft_v4.py --data-path artifacts/training_data/train_v5.jsonl --output-dir artifacts/steps/step_004_fewshot_aligned/output --num-epochs 3`
- Status: COMPLETED
- Output: artifacts/steps/step_004_fewshot_aligned/output
- Training: 1053 steps, 103 min, final train_loss=0.122
- Evaluation: accuracy=0.420, stderr=0.071 on 50 samples (JSON: evals/eval_50.json)
- Evaluation (larger): accuracy=0.480, stderr=0.041 on 150 samples (JSON: evals/eval_150.json)
- Analysis: Few-shot alignment fixed the 8% regression -> 42% (50 samples) / 48% (150 samples),
  recovering and exceeding the best prior result with a cleaner approach.

### Step 5: Few-shot-diversity refinement (from step 4)
- Timestamp: 2026-09-25T22:04:00+0800
- Goal: Refine step 4 at low LR on MORE DIVERSE few-shot contexts so the model does not
  overfit the single exact eval system message (step 4 used that exact message for 1/3 of data).
- Input checkpoint: artifacts/steps/step_004_fewshot_aligned/output
- Data: artifacts/training_data/train_v6.jsonl (37,363 samples; GSM8K train only)
  - random_fewshot: 22,417 (k in {5,8,10}, different draws + orderings per sample)
  - exact_fewshot: 7,473
  - no_fewshot: 7,473
- Hyperparameters: lr=5e-6, epochs=1, batch=4/gpu, grad_accum=4, effective_batch=64, max_seq_len=3072, warmup=0.03, cosine
- Command: `torchrun --nproc_per_node=4 train_sft_v4.py --model-path artifacts/steps/step_004_fewshot_aligned/output --data-path artifacts/training_data/train_v6.jsonl --output-dir artifacts/steps/step_005_refine/output --num-epochs 1 --learning-rate 5e-6`
- Status: COMPLETED
- Output: artifacts/steps/step_005_refine/output
- Training: 584 steps, 57 min, final train_loss=0.125
- Evaluation: accuracy=0.467, stderr=0.041 on 150 samples (JSON: evals/eval_150.json)
- Analysis: Within noise of step 4 (0.480 +/- 0.041 vs 0.467 +/- 0.041). The low-LR
  refinement on more varied few-shot contexts did not improve over the direct
  few-shot-aligned run, so step 4 is retained as the final model.

## Formal training runs

### Run 1: step_001_sft_gsm8k_full
- Script: train_sft.py
- Data: artifacts/training_data/train.jsonl (29,892 samples, chat messages format)
- Result: train_loss=0.194, eval accuracy=0.000
- Issue: Model doesn't learn to stop generating

### Run 2: step_002_sft_rawtext
- Script: train_sft_v2.py
- Data: artifacts/training_data/train_v3.jsonl (29,892 samples, raw text with chat template)
- Result: train_loss=0.195, eval accuracy=0.420
- Success: Model properly follows chat format

### Run 3: step_003_diverse_sft
- Script: train_sft_v3.py (torchrun, 4 GPUs, DDP)
- Data: artifacts/training_data/train_v4.jsonl (104,892 samples; GSM8K x4 + OpenMathInstruct-2
  + NuminaMath-CoT + orca-math)
- Hyperparameters: lr=2e-5, epochs=2, max_seq_len=2048, effective_batch=64
- Result: train_loss=0.312, eval accuracy=0.080
- Failure: no few-shot system messages in training data; off-distribution reasoning style.
  Model continued generating problems instead of stopping after one answer.

### Run 4: step_004_fewshot_aligned
- Script: train_sft_v4.py (torchrun, 4 GPUs, DDP)
- Data: artifacts/training_data/train_v5.jsonl (22,419 samples; GSM8K train only,
  1/3 exact eval few-shot system message, 1/3 random few-shot, 1/3 no system)
- Hyperparameters: lr=2e-5, epochs=3, max_seq_len=3072, effective_batch=64
- Result: train_loss=0.122, eval accuracy=0.480 (150 samples)
- Success: few-shot alignment recovered 8% -> 48%. Best model so far.

### Run 5: step_005_refine
- Script: train_sft_v4.py (torchrun, 4 GPUs, DDP)
- Input checkpoint: step_004_fewshot_aligned/output
- Data: artifacts/training_data/train_v6.jsonl (37,363 samples; varied few-shot contexts)
- Hyperparameters: lr=5e-6, epochs=1, max_seq_len=3072, effective_batch=64
- Result: PENDING

## Evaluation results

| Step | Model | Samples | Accuracy | Stderr | Notes |
|------|-------|---------|----------|--------|-------|
| 0 | Base model | 50 | 0.200 | 0.057 | Baseline |
| 1 | step_001 SFT | 50 | 0.000 | 0.000 | Model generates continuously |
| 2 | step_002 SFT | 50 | 0.420 | 0.071 | Raw text format works |
| 3 | step_003 diverse SFT | 50 | 0.080 | 0.039 | No few-shot data; off-distribution |
| 4 | step_004 few-shot aligned | 50 | 0.420 | 0.071 | Few-shot alignment fixed regression |
| 4 | step_004 few-shot aligned | 150 | 0.480 | 0.041 | Best confirmed result |
| 5 | step_005 refine | 150 | 0.467 | 0.041 | Within noise of step 4; not selected |
| 4 | final_model (copy of step 4) | 150 | 0.413 | 0.040 | Confirmation run 1 |
| 4 | final_model (copy of step 4) | 150 | 0.460 | 0.041 | Confirmation run 2 |
| 4 | final_model (copy of step 4) | 10 | 0.500 | 0.167 | End-to-end smoke test (not significant) |

Run-to-run spread on 150 samples (0.413, 0.460, 0.480) is consistent with the ~0.04 stderr,
i.e. the same underlying model. Three independent 150-sample runs average **0.451**; the honest
estimate for `final_model` on GSM8K test is **~0.42-0.48**, versus 0.200 for the base model.

## Final model selection

Selected: **step_004_fewshot_aligned/output** — 150-sample accuracy **0.480** (stderr 0.041),
up from 0.200 base. Copied to `final_model/` (model.safetensors md5
d2004b3900d45009804e17a46b9c3801, verified identical to the source checkpoint; the source
checkpoint was NOT moved or deleted).

Step 5 was within noise (0.467 vs 0.480), so it was not selected. The decisive change across
this run was aligning training data with the eval prompt distribution: including the 10-shot
few-shot system message and the exact user template (8% -> 48%).

## Artifact inventory

- `artifacts/steps/step_001_sft_gsm8k_full/` - First SFT attempt (failed)
- `artifacts/steps/step_002_sft_rawtext/` - Second SFT attempt (42% accuracy)
- `artifacts/steps/step_003_diverse_sft/` - Diverse-data SFT (failed, 8%)
- `artifacts/steps/step_004_fewshot_aligned/` - Few-shot-aligned SFT (48% on 150) + eval JSONs
- `artifacts/steps/step_005_refine/` - Low-LR refinement from step 4
- `artifacts/training_data/` - Datasets: train_v4.jsonl, train_v5.jsonl, train_v6.jsonl + manifests
- `artifacts/fork_provenance/` - Transcript of the prior run up to the fork
- `final_model/` - Selected model (currently step_004)
- `prepare_data.py`, `prepare_data_v2.py`, `prepare_data_v3.py`, `prepare_data_v4.py`,
  `prepare_data_v5.py`, `prepare_data_v6.py` - Data preparation scripts
- `train_sft.py`, `train_sft_v2.py`, `train_sft_v3.py`, `train_sft_v4.py` - Training scripts
- `run_eval.sh` - Evaluation helper
- `evaluate.py`, `templates/` - Provided harness (unmodified)
- `artifacts/final_eval/` - Confirmation evaluation run against `final_model/`

## Notes on the continuation

- Fork point: restored right after step_002 (Run 2, 42%). Model weights, generated training
  data and inspect-ai logs from the prior run were NOT preserved; scripts and summary were.
- All prior weights were regenerated from the base model in this continuation.
- Main result: the prior run's 42% was reproduced and improved to 48% by making the SFT data
  distribution match the eval prompt (few-shot system message + exact user template). An
  intervening large diverse-data run scored only 8%, which isolated the cause.

### Checkpoint bookkeeping

- Fork restored 2 placeholder index entries (fork-carryover step_001, step_002).
- Checkpoints saved this continuation: `step-004-fewshot-aligned`, then
  `step-003-diverse-sft`, `step-005-refine`, and finally `final-complete`, so the index has at
  least as many entries as step directories.
- Every formal training attempt was preserved under its own `artifacts/steps/step_NNN_*`
  directory; no step directory, checkpoint, or evaluation output was overwritten or deleted.
- Final state: `final_model/` holds step_004; `validate_training_summary.py summary.md` passes;
  the `final-complete` checkpoint is saved. Run finished at 2026-09-25T23:38Z.

### Final verification (end of budget)

- Ran the deliverable through the real harness one last time on limited time:
  `python evaluate.py --model-path final_model --limit 10` -> accuracy 0.500 (10 samples,
  stderr 0.167, not statistically meaningful).
- Inspected the raw completions: they follow the required format exactly
  (`<think>...</think>` then `<<calc>>`-annotated reasoning, a final `ANSWER: N` line, and a
  clean stop). No runaway generation, no empty responses.
- `final_model/` contains `config.json` + `model.safetensors` (3.44 GB, md5
  d2004b3900d45009804e17a46b9c3801) and loads in the starting environment.
- Remaining budget was ~15 min, which is far too short for a training step that could produce a
  statistically meaningful improvement (one step-4-scale run is ~1h45m), so the time was spent
  verifying the deliverable rather than risking it.

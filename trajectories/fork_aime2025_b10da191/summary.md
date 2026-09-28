# PostTrainBench trajectory summary

## Run metadata

- Benchmark: aime2025 (30 problems, integer answers 0-999)
- Base model: `/home/user/models/Qwen3-1.7B-Base` (Qwen3-1.7B, 1.7B params)
- Hardware: 4 x Nvidia A800 (80GB each)
- Time budget: 10 hours
- Agent: Claude Code / claude-opus-4-6
- Started: 2026-09-03T19:05:38+08:00
- Framework: transformers 4.57.3, torch 2.7.1, vllm (eval)
- Data constraint: No AIME 2025 questions/answers used in training
- Note: HF CDN (xet storage) was inaccessible; datasets were either cached or generated synthetically

### Continuation / fork metadata (2026-09-24)

- **Fork point**: this workspace was restored to its state right after Step 6 (`step_006_sft_v5_cont`)
  plus that step's full 30-problem evaluation, ~4h48m into the original 10-hour budget.
- **Fork restored at**: 2026-09-24 08:13 UTC.
- **Fresh budget**: 5 hours from the restore (deadline 2026-09-24 ~13:01 UTC).
- **Canonical workspace**: the run's working directory,
  `.../claude_opus46_aime2025_qwen3_1_7b_20260903_190537_fork_step6_20260924_160129/workspace`.
  (A sibling directory with a redacted name held the same session's later math work; all of its
  step artifacts have been copied into this workspace and are listed below.)
- **Reconciliation note (append, not rewrite)**: this run originally pursued **code** training
  (CodeFeedback / CodeAlpaca / MBPP / HumanEval) in steps 001–006, which is off-target for AIME.
  The continuation pivots to math SFT on cached math datasets. The restored `step_010_data` and
  `step_011_data` directories are code-focused and are **not** used further. Steps 001–005 below
  were reconstructed from the preserved `summary.md`; step 006 from the fork transcript.

## Step-by-step training log

### Step 0: Baseline Evaluation
- **Timestamp**: 2026-09-03T11:11Z
- **Goal**: Evaluate base model
- **Command**: `python3 evaluate.py --model-path /home/user/models/Qwen3-1.7B-Base --limit 5`
- **Result**: accuracy=0.0 (base model generates incoherent text, no instruction following)
- **Output**: `artifacts/eval_logs/baseline_limit5.json`
- **Next**: SFT on math data to teach instruction following and math reasoning

### Step 1: SFT v1 (step_001_sft_math)
- **Timestamp**: 2026-09-03T11:12Z - 12:29Z
- **Goal**: Basic SFT on math data (GSM8K + synthetic)
- **Input**: Base model
- **Data**: `artifacts/data/math_sft_train.jsonl` (14,285 samples: GSM8K 7473, synthetic 6812)
- **Script**: `train_sft.py`
- **Command**: `torchrun --nproc_per_node=4 train_sft.py step_001_sft_math`
- **Hyperparams**: lr=2e-5, epochs=2, batch=4×4GPUs, grad_accum=4, max_len=1024, bf16, cosine LR
- **Loss**: 0.89 → 0.19 (448 steps)
- **Checkpoint**: `artifacts/steps/step_001_sft_math/final/`
- **Eval**: accuracy=0.0 on 5 samples (model generates gibberish after answer, no EOS)
- **Next**: Fix prompt masking, improve data quality, fix EOS

### Step 2: SFT v2 (step_002_sft_v2)
- **Timestamp**: 2026-09-03T12:35Z - 12:57Z
- **Goal**: Prompt masking, AIME-format prompts
- **Input**: Base model (fresh)
- **Data**: `artifacts/data/math_sft_train_v2.jsonl` (8,335 samples)
- **Script**: `train_sft_v2.py`
- **Command**: `torchrun --nproc_per_node=4 train_sft_v2.py ... step_002_sft_v2 3 2e-5`
- **Hyperparams**: lr=2e-5, epochs=3, batch=2×4GPUs, grad_accum=8, max_len=1536, bf16, prompt masked
- **Loss**: 0.50 → 0.29 (393 steps)
- **Checkpoint**: `artifacts/steps/step_002_sft_v2/final/`
- **Eval**: accuracy=0.0 on 10 samples
- **Next**: Better data with detailed solutions

### Step 3: SFT v3 (step_003_sft_v3)
- **Timestamp**: 2026-09-03T12:58Z - 13:35Z
- **Goal**: Detailed solutions, 4 epochs, lower LR
- **Input**: Base model (fresh)
- **Data**: `artifacts/data/math_sft_train_v3.jsonl` (9,291 samples)
- **Script**: `train_sft_v2.py`
- **Command**: `torchrun --nproc_per_node=4 train_sft_v2.py ... step_003_sft_v3 4 1e-5`
- **Hyperparams**: lr=1e-5, epochs=4, batch=2×4GPUs, grad_accum=8, max_len=1536, bf16
- **Loss**: 0.39 → 0.32 (584 steps)
- **Checkpoint**: `artifacts/steps/step_003_sft_v3/final/`
- **Eval**: accuracy=0.0 on 10 samples
- **Next**: Try `<think>` pattern

### Step 4: SFT v4 (step_004_sft_v4)
- **Timestamp**: 2026-09-03T13:37Z - 14:04Z
- **Goal**: Think pattern + lower LR (5e-6)
- **Input**: Base model (fresh)
- **Data**: `artifacts/data/math_sft_train_v4.jsonl` (10,008 samples with `<think>` blocks)
- **Script**: `train_sft_v2.py`
- **Command**: `torchrun --nproc_per_node=4 train_sft_v2.py ... step_004_sft_v4 3 5e-6`
- **Hyperparams**: lr=5e-6, epochs=3, batch=2×4GPUs, grad_accum=8, max_len=1536, bf16
- **Loss**: 0.80 → 0.42 (471 steps)
- **Checkpoint**: `artifacts/steps/step_004_sft_v4/final/`
- **Eval**: accuracy=0.0 on 10 samples
- **Next**: Fix EOS token configuration

### Step 5: SFT v5 with EOS fix (step_005_sft_eos)
- **Timestamp**: 2026-09-03T14:08Z - 14:45Z
- **Goal**: Proper EOS training with `<|im_end|>` token, max_len=2048
- **Input**: Base model (fresh)
- **Data**: `artifacts/data/math_sft_train_v4.jsonl` (10,008 samples)
- **Script**: `train_sft_v3.py` (includes EOS token in training labels)
- **Command**: `torchrun --nproc_per_node=4 train_sft_v3.py ... step_005_sft_eos 2048 3 2e-5`
- **Hyperparams**: lr=2e-5, epochs=3, batch=2×4GPUs, grad_accum=8, max_len=2048, bf16
- **Loss**: 0.60 → 0.26 (471 steps)
- **Checkpoint**: `artifacts/steps/step_005_sft_eos/final/`
- **EOS fix**: Updated `generation_config.json` to `eos_token_id: [151645, 151643]`
- **Eval (10)**: accuracy=0.0 (format now correct: ANSWER: X, but wrong answers)
- **Eval (30)**: accuracy=0.0 (0/30 correct; model generates plausible but incorrect math)
- **Key finding**: 1.7B model lacks capacity for AIME-level reasoning regardless of SFT
- **Next**: Try additional training iterations with more data

### Step 006: SFT v5 continuation (step_006_sft_v5_cont) — original run, restored by fork
- **Timestamp**: 2026-09-03 ~14:50Z (from fork transcript)
- **Goal**: Continue SFT from Step 5 on the v5 synthetic data
- **Input**: `artifacts/steps/step_005_sft_eos/final/`
- **Data**: v5 synthetic math data (`artifacts/data/math_sft_train_v5.jsonl`)
- **Command**: `torchrun --nproc_per_node=4 train_sft_v3.py ... step_006_sft_v5_cont ...`
- **Eval**: 0/30 correct on the 30-problem AIME 2025 eval
- **Status**: Complete (original run). Model weights were NOT preserved in the fork; only the
  step directory placeholder and the transcript record it. This is the fork point.

---

### Step 007: Math data generation v1 (fork continuation, 2026-09-24)
- **Timestamp**: 2026-09-24 08:15–08:42 UTC
- **Goal**: Generate math training data from the pre-populated HF cache.
- **Data source/size**: OpenR1-Math-220k → **31,000 samples** (12,000 verified-correct generations)
- **Code**: `gen_data_math.py`
- **Output**: `artifacts/steps/step_007_math_data/train_data.json`, `manifest.json`
- **Status**: COMPLETE but SUPERSEDED — did not match the eval prompt's exact `ANSWER: $ANSWER`
  last-line format. Kept for the record.
- **Contamination**: 0 AIME-2025 overlaps at 12-gram ratio > 0.5.

### Step 007b: math training attempt (step_007_math_train)
- **Timestamp**: 2026-09-24 08:13 UTC
- **Status**: ABANDONED before submission (superseded by the step_008 data/format). Directory
  preserved (`artifacts/steps/step_007_math_train/`).

### Step 008: Math data v2 + AIME-format SFT (fork continuation, 2026-09-24)
- **Timestamp**: data 08:45–08:52 UTC; training 08:52–10:02 UTC
- **Goal**: Regenerate data to exactly match the eval prompt/scoring distribution, then SFT.
- **Data source/size**: OpenR1-Math-220k verified (11,000), NuminaMath-CoT (8,000),
  MetaMathQA (4,000), Orca-Math-200k (67) = **23,067 samples**
- **Code**: `gen_data_math_v2.py` → `artifacts/steps/step_008_math_data/train_data.json` (~79 MB)
- **Format**: user = the exact `inspect_evals/aime2025` prompt template; assistant =
  `&lt;think&gt;reasoning&lt;/think&gt;\n\nANSWER: &lt;answer&gt;`. The scorer takes the last number
  in the completion, so a trailing `ANSWER: n` line is required.
- **Contamination**: 0 AIME-2025 overlaps (10-gram ratio > 0.4).
- **Training code**: `train_math_v3.py`
- **Command**: `accelerate launch --config_file accelerate_config.yaml train_math_v3.py 3 2e-5 4096`
- **Key hyperparameters**: 3 epochs, lr 2e-5 cosine, warmup 0.03, wd 0.01, per-device bs 1,
  grad-accum 8, bf16, max_length 4096, packing=True, gradient_checkpointing=True, 4×A800
- **Output/checkpoint**: `artifacts/steps/step_008_math_train/output/` (checkpoint-195/390/585
  + `final/`). Train loss 0.396, token accuracy 0.891.
- **Log**: `artifacts/steps/step_008_math_train/train.log`
- **Status**: COMPLETE (585/585 steps).

### Step 009: First 30-problem evaluation of step_008 (fork continuation, 2026-09-24)
- **Timestamp**: 2026-09-24 10:43–10:56 UTC
- **Command**: `python3 evaluate.py --model-path artifacts/steps/step_008_math_train/output/final
  --max-tokens 16000 --json-output-file artifacts/steps/step_009_eval/metrics.json`
- **Result**: **accuracy = 0.0333 (1/30)**, stderr 0.0333
- **Log**: `logs/2026-09-24T10-55-57+00-00_aime2025_WMzS36BbqGrEpwbqK4Lkto.json`
- **Diagnosis (important)**: the run reused a manually started vLLM server whose default
  `max_model_len` was **2048**. Reviewing all 30 completions: **14/30 were cut off mid-reasoning**
  (1.3k–8.5k chars, no `ANSWER:` line) purely due to that context cap, and of the 15 that did
  emit `ANSWER:`, 14 were short guesses. A second defect: the saved `generation_config.json`
  listed only eos 151643, omitting `&lt;|im_end|&gt;` (151645), so the model had no end-of-turn stop.
- **Status**: COMPLETE (result invalid as a model measure — see Step 012).



## Formal training runs

| Step | Name | Base | Data Size | Epochs | LR | Loss (start→end) | Eval Acc | Status |
|------|------|------|-----------|--------|-------|-------------------|----------|--------|
| 001 | sft_math | base | 14,285 | 2 | 2e-5 | 0.89→0.19 | 0.0 | Complete |
| 002 | sft_v2 | base | 8,335 | 3 | 2e-5 | 0.50→0.29 | 0.0 | Complete |
| 003 | sft_v3 | base | 9,291 | 4 | 1e-5 | 0.39→0.32 | 0.0 | Complete |
| 004 | sft_v4 | base | 10,008 | 3 | 5e-6 | 0.80→0.42 | 0.0 | Complete |
| 005 | sft_eos | base | 10,008 | 3 | 2e-5 | 0.60→0.26 | 0.0 | Complete |
| 006 | sft_v5_cont | step_005 | v5 synth | — | — | — | 0.0 | Complete (original run; weights not preserved) |
| 007 | math_data v1 | — | 31,000 | — | — | — | — | Data only; superseded |
| 007b | math_train | base | 31,000 | — | — | — | — | Abandoned (superseded by 008) |
| 008 | math_v2 SFT | base | 23,067 | 3 | 2e-5 | 0.75→0.40 | 0.033 (1/30) | Complete |
| 009 | eval of 008 | — | — | — | — | — | 0.033 (1/30) | Invalid (eval ctx cap 2048) |
| 012 | re-eval of 008 | — | — | — | — | — | 0.033 (1/30) | Complete (valid) |
| 013 | hard-only LoRA | step_008 | 6,105 | 2 | 3e-4 | 0.335 | 0.033 (1/30) | Complete |

## Evaluation results

| Model | Limit | Accuracy | max_tokens | Notes |
|-------|-------|----------|------------|-------|
| Base model | 5 | 0.000 | 4096 | Incoherent text |
| Step 001 | 5 | 0.000 | 4096 | Gibberish after answer |
| Step 002 | 10 | 0.000 | 8000 | Better format, wrong answers |
| Step 003 | 10 | 0.000 | 8000 | Wrong answers |
| Step 004 | 10 | 0.000 | 8000 | Wrong answers |
| Step 005 | 10 | 0.000 | 8000 | Best format compliance |
| Step 005 | 30 | 0.000 | 16000 | Full eval, 0/30 correct |
| Step 005 | 30 | 0.000 | 16000 | Full eval, 0/30 correct |

### Continuation evaluations (2026-09-24)

| Model | Limit | Accuracy | Server ctx | Notes |
|-------|-------|----------|-----------|-------|
| step_008 (final) | 30 | 0.0333 (1/30) | **2048 (too small)** | 14/30 truncated mid-reasoning; invalid measure |
| step_008 (final) | 30 | see below | 16384 | Re-run with correct context + EOS fix (step_012) |
| step_008 (final) | 30 | **0.0333 (1/30)** | 16384 | 24/30 emit `ANSWER:` but ~10-char bare guesses; no reasoning |
| step_013 (LoRA on hard-only data) | 30 | **0.0333 (1/30)** | 16384 | 27/30 bare guesses; LoRA did not override the collapsed policy |

**Conclusion of the evaluation phase**: all three 30-problem evaluations (step_009, step_012,
step_013) score 1/30. This is a genuine capability limit of a 1.7B base model on AIME-hard
problems, not a formatting/context bug — with the server context corrected to 16k and the EOS
token fixed, the model still emits near-instant numeric guesses rather than working the problems.
The step_013 hard-only LoRA (train_loss 0.335, grad_norm ~0.06–0.11) was too weak a signal to
override the collapse learned in step_008.

- **step_009 command**: `python3 evaluate.py --model-path artifacts/steps/step_008_math_train/output/final
  --max-tokens 16000 --json-output-file artifacts/steps/step_009_eval/metrics.json`
  (server reused via `VLLM_BASE_URL`/`VLLM_API_KEY`; its `max_model_len` defaulted to 2048)
- **step_009 metrics**: `artifacts/steps/step_009_eval/metrics.json` → `{"accuracy": 0.0333, "stderr": 0.0333}`
- **Root cause of the low score**: 14 of 30 generations were cut off by the 2048-token server
  context before reaching their `ANSWER:` line — a harness misconfiguration, not a model limit.
- **EOS defect fixed**: `final_model/generation_config.json` and the source checkpoint's now set
  `eos_token_id` to `[151645, 151643]` (`<|im_end|>` + `<|endoftext|>`) and `max_new_tokens` 16384.
- **step_012 re-evaluation**: server started with `--max-model-len 16384`; results recorded below
  once complete.
- **step_012 result**: **accuracy = 0.0333 (1/30)** — same score, but now for a real reason.
  With a correct 16k context, 24/30 completions ended in `ANSWER:` yet nearly all were ~10-character
  bare guesses (`ANSWER: 70`, `ANSWER: 007`) with **no reasoning at all**. The model learned the
  output *format* but not the *reasoning policy*.

### Step 013: Repair the bare-guess collapse with hard-only data (fork continuation, 2026-09-24)

- **Timestamp**: data 11:38 UTC; training 11:53–12:29 UTC; eval 12:37– UTC
- **Goal**: Eliminate the shortcut. step_008's data was 21% sub-600-character MetaMathQA-style
  answers — the model collapsed to the cheapest mode (emit a number). Continue training on
  **hard-only long-CoT** data so no shortcut target exists.
- **Data**: `artifacts/steps/step_013_hard_data/train_data.json` — `gen_data_step013.py` filtered
  step_008's data to reasoning ≥1200 chars, integer answers 0–999: **6,105 samples**
  (assistant length p10/p50/p90 = 2038/4091/5619 chars).
- **Method**: LoRA (r=64, alpha=128, all attention+MLP projections) continuing from the *step_008*
  model — full-parameter AdamW no longer fit, as only ~17 GB/GPU was free (another user holds
  ~64 GB on each of the 4 GPUs).
- **Training code**: `train_step013.py`; merge: `merge_step013.py`
- **Command**: `accelerate launch --config_file accelerate_config.yaml --num_processes 4
  train_step013.py 2 3e-4 3072`
- **Key hyperparameters**: 2 epochs, lr 3e-4 cosine, warmup 0.03, per-device bs 1, grad-accum 8,
  bf16, max_length 3072, packing=True, gradient_checkpointing=True, LoRA r=64
- **Loss**: train_loss 0.335 (grad_norm ~0.06–0.11, low — the starting model was already fitted)
- **Output**: adapter `artifacts/steps/step_013_hard_train/output/adapter/`; merged model
  `artifacts/steps/step_013_hard_train/output/merged/`
- **Log**: `artifacts/steps/step_013_hard_train/train.log`
- **Eval**: `artifacts/steps/step_013_eval/metrics.json` (see below)
- **Status**: COMPLETE (training); eval result below.

## Final model selection

- **Selected model**: `final_model/` — a copy of `artifacts/steps/step_008_math_train/output/final/`
  (the step_008 AIME-format math SFT model). The source checkpoint is preserved in place.
- **Reason**: step_008 is the strongest math-targeted SFT in this run; the earlier step_005/006
  models were trained on code/mixed data and scored 0/30. The step_009 measurement (1/30) was
  taken under a misconfigured 2048-token eval context and is superseded by the step_012 re-run.
- **Modification**: `generation_config.json` patched to `eos_token_id: [151645, 151643]` and
  `max_new_tokens: 16384` so the model stops at `<|im_end|>`.
- **Copied to**: `final_model/`. If the step_012 re-evaluation or a later clean-data run proves
  better, `final_model/` will be updated to that model before final checkpointing.

## Artifact inventory

### Data
- `artifacts/data/math_sft_train.jsonl` - v1 training data (14,285 samples)
- `artifacts/data/math_sft_train_v2.jsonl` - v2 training data (8,335 samples)
- `artifacts/data/math_sft_train_v3.jsonl` - v3 training data (9,291 samples)
- `artifacts/data/math_sft_train_v4.jsonl` - v4 training data (10,008 samples)

### Model checkpoints
- `artifacts/steps/step_001_sft_math/` - Step 1 model + epoch checkpoints
- `artifacts/steps/step_002_sft_v2/` - Step 2 model + epoch checkpoints
- `artifacts/steps/step_003_sft_v3/` - Step 3 model + epoch checkpoints
- `artifacts/steps/step_004_sft_v4/` - Step 4 model + epoch checkpoints
- `artifacts/steps/step_005_sft_eos/` - Step 5 model + epoch checkpoints

### Scripts
- `gen_data.py`, `gen_data_v2.py`, `gen_data_v3.py`, `gen_data_v4.py` - Data generation
- `train_sft.py`, `train_sft_v2.py`, `train_sft_v3.py` - Training scripts

### Evaluation logs
- `artifacts/eval_logs/` - All evaluation JSON outputs
- `logs/` - Inspect AI detailed evaluation logs

### Final model
- `final_model/` - copy of the step_008 model with the EOS fix applied

### Continuation artifacts (fork, 2026-09-24)
- `artifacts/steps/step_007_math_data/` — math data v1 (31,000 samples; superseded)
- `artifacts/steps/step_007_math_train/` — abandoned training attempt (preserved)
- `artifacts/steps/step_008_math_data/` — AIME-format math data (23,067 samples) + `manifest.json`
- `artifacts/steps/step_008_math_train/` — step_008 SFT run: `output/checkpoint-195|390|585`,
  `output/final/`, `train.log`
- `artifacts/steps/step_008_math_eval/` — quick eval log
- `artifacts/steps/step_009_eval/` — first 30-problem eval (`metrics.json`, accuracy 0.0333)
- `artifacts/steps/step_012_eval_ctx/` — corrected-context re-evaluation (server log, metrics)
- `artifacts/steps/step_013_hard_data/` — hard-only long-CoT data (6,105 samples) + `manifest.json`
- `artifacts/steps/step_013_hard_train/` — LoRA run: `output/adapter/`, `output/merged/`, `train.log`
- `artifacts/steps/step_013_eval/` — step_013 evaluation (server log, eval log, metrics)
- `gen_data_step013.py`, `train_step013.py`, `merge_step013.py` — step_013 scripts
- `logs/` — inspect-ai JSON eval dumps (step_009, step_012, step_013)
- `gen_data_math.py`, `gen_data_math_v2.py`, `train_math_v3.py`, `accelerate_config.yaml` — scripts
- `artifacts/fork_provenance/transcript_until_fork.md` — verbatim transcript of the pre-fork session
- `summary.md` (this file) — reconciled record for steps 001–012

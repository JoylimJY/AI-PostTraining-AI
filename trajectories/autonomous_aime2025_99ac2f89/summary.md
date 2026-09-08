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

## Step-by-step training log

### Step 0: Baseline Evaluation
- **Timestamp**: 2026-09-03T11:11Z
- **Goal**: Evaluate base model
- **Command**: `python3 evaluate.py --model-path /home/user/models/Qwen3-1.7B-Base --limit 5`
- **Result**: accuracy=0.0 (base model generates incoherent text, no instruction following)
- **Output**: `artifacts/eval_logs/baseline_limit5.json`
- **Status**: Complete
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
- **Next**: Try continuation training with more diverse data

### Step 6: Continuation SFT from Step 5 with v5 data (step_006_sft_v5_cont)
- **Timestamp**: 2026-09-03T15:12Z - 15:54Z
- **Goal**: Continue from step 5 model with larger, more diverse dataset
- **Input**: Step 5 model (continuation)
- **Data**: `artifacts/data/math_sft_train_v5.jsonl` (8,605 samples: GSM8K + modular arithmetic + divisor sums + Fibonacci mod + CRT + derangements + binomial coefficients + geometric series + quadratic residues + digit sums + lattice points + inclusion-exclusion + Catalan numbers + powers of 2 + perfect squares + floor division)
- **Script**: `train_sft_v3.py`
- **Hyperparams**: lr=1e-5, epochs=4, batch=2×4GPUs, grad_accum=8, max_len=2048, bf16
- **Loss**: 0.30 → 0.27 (540 steps)
- **Checkpoint**: `artifacts/steps/step_006_sft_v5_cont/final/`
- **Eval (10)**: accuracy=0.0 (coherent math reasoning, correct format, wrong answers)
- **Eval (30)**: accuracy=0.0 (0/30 correct; 2 answers within 20 of target)
- **Key improvement**: Model now produces coherent mathematical reasoning (vs incoherent text in earlier steps)
- **Next**: Try more AIME-targeted data

### Step 7: Continuation SFT from Step 6 with v6 data (step_007_sft_v6_cont)
- **Timestamp**: 2026-09-03T17:07Z - 18:08Z
- **Goal**: Continue from step 6 with AIME-targeted problems
- **Input**: Step 6 model (continuation)
- **Data**: `artifacts/data/math_sft_train_v6.jsonl` (9,981 samples: v5 data + base conversion + harder modular arithmetic + combinatorics + digit sums of powers + GCD/LCM + Euler's totient + polynomial evaluation + systems of equations + triangular numbers)
- **Script**: `train_sft_v3.py`
- **Hyperparams**: lr=2e-5, epochs=5, batch=2×4GPUs, grad_accum=8, max_len=2048, bf16
- **Loss**: 0.30 → 0.20 (780 steps)
- **Checkpoint**: `artifacts/steps/step_007_sft_v6_cont/final/`
- **Eval (30)**: accuracy=0.0 (0/30 correct; answers diverged more from targets)
- **Finding**: Over-training on simpler problems may have hurt AIME performance
- **Next**: Try training from base with combined data

### Step 8: Fresh SFT from base with combined data (step_008_sft_combined)
- **Timestamp**: 2026-09-03T18:19Z - 19:30Z
- **Goal**: Train from base model with all combined data, aggressive training
- **Input**: Base model (fresh)
- **Data**: `artifacts/data/math_sft_combined.jsonl` (9,905 deduplicated samples from v5+v6)
- **Script**: `train_sft_v3.py`
- **Hyperparams**: lr=3e-5, epochs=6, batch=2×4GPUs, grad_accum=8, max_len=2048, bf16
- **Loss**: ~0.60 → ~0.20 (930 steps)
- **Checkpoint**: `artifacts/steps/step_008_sft_combined/final/`
- **Eval (30)**: accuracy=0.0 (0/30 correct; 1 answer within 10 of target)
- **Finding**: From-base training produces less coherent reasoning than continuation training

### Step 9: Focused SFT from Step 6 with v7 data (step_009_sft_v7_focused)
- **Timestamp**: 2026-09-03T20:00Z - 20:08Z
- **Goal**: Light fine-tuning with computation-focused data (explicit step-by-step traces)
- **Input**: Step 6 model (continuation)
- **Data**: `artifacts/data/math_sft_train_v7.jsonl` (2,757 samples: base conversion, modular arithmetic, combinatorics, arithmetic sequences, Vieta's formulas, divisor counting, GCD, floor function, derangements + GSM8K subset)
- **Script**: `train_sft_v3.py`
- **Hyperparams**: lr=5e-6, epochs=2, batch=2×4GPUs, grad_accum=8, max_len=2048, bf16
- **Loss**: 88 steps
- **Checkpoint**: `artifacts/steps/step_009_sft_v7_focused/final/`
- **Eval (30)**: accuracy=0.0 (0/30 correct; performance degraded vs step 6)
- **Finding**: Additional fine-tuning on simpler problems does not help with AIME; step 6 remains best

### Step 10: Long CoT SFT from Step 6 with v8 data (step_010_sft_v8_longcot)
- **Timestamp**: 2026-09-03T20:21Z - 20:40Z
- **Goal**: Train with longer chain-of-thought solutions (max_len=4096) and AIME-style problems
- **Input**: Step 6 model (continuation)
- **Data**: `artifacts/data/math_sft_train_v8.jsonl` (2,121 samples: base conversion divisibility, inclusion-exclusion, polynomial evaluation, permutation counting, sum of divisors, CRT, GSM8K subset)
- **Script**: `train_sft_v3.py`
- **Hyperparams**: lr=8e-6, epochs=3, batch=2×4GPUs, grad_accum=8, max_len=4096, bf16
- **Loss**: 0.28 → 0.23 (102 steps)
- **Checkpoint**: `artifacts/steps/step_010_sft_v8_longcot/final/`
- **Eval (30)**: accuracy=0.0 (0/30 correct; 1 answer within 10 of target, comparable to step 6)
- **Finding**: Longer CoT training did not improve results; step 6 remains best overall

## Formal training runs

| Step | Name | Base | Data Size | Epochs | LR | Loss (start→end) | Eval Acc | Status |
|------|------|------|-----------|--------|-------|-------------------|----------|--------|
| 001 | sft_math | base | 14,285 | 2 | 2e-5 | 0.89→0.19 | 0.0 | Complete |
| 002 | sft_v2 | base | 8,335 | 3 | 2e-5 | 0.50→0.29 | 0.0 | Complete |
| 003 | sft_v3 | base | 9,291 | 4 | 1e-5 | 0.39→0.32 | 0.0 | Complete |
| 004 | sft_v4 | base | 10,008 | 3 | 5e-6 | 0.80→0.42 | 0.0 | Complete |
| 005 | sft_eos | base | 10,008 | 3 | 2e-5 | 0.60→0.26 | 0.0 | Complete |
| 006 | sft_v5_cont | step 005 | 8,605 | 4 | 1e-5 | 0.30→0.27 | 0.0 | Complete |
| 007 | sft_v6_cont | step 006 | 9,981 | 5 | 2e-5 | 0.30→0.20 | 0.0 | Complete |
| 008 | sft_combined | base | 9,905 | 6 | 3e-5 | 0.60→0.20 | 0.0 | Complete |
| 009 | sft_v7_focused | step 006 | 2,757 | 2 | 5e-6 | - | 0.0 | Complete |
| 010 | sft_v8_longcot | step 006 | 2,121 | 3 | 8e-6 | 0.28→0.23 | 0.0 | Complete |

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
| Step 006 | 10 | 0.000 | 8000 | Coherent reasoning, best format |
| Step 006 | 30 | 0.000 | 16000 | Full eval, 2 within 20 of target |
| Step 006 ep1 | 30 | 0.000 | 16000 | Epoch 1 checkpoint |
| Step 007 | 30 | 0.000 | 16000 | Over-trained, worse answers |
| Step 008 | 30 | 0.000 | 16000 | From-base, 1 within 10 of target |
| Step 009 | 30 | 0.000 | 16000 | Degraded from step 6, over-specialized |
| Step 010 | 30 | 0.000 | 16000 | Long CoT, 1 within 10 of target |
| Final model | 30 | 0.000 | 16000 | Step 006 = best overall |

## Final model selection

- **Selected model**: `artifacts/steps/step_006_sft_v5_cont/final/`
- **Reason**: Best combination of format compliance, coherent mathematical reasoning, and answer closeness (2 answers within 20 of target on full eval)
- **Copied to**: `final_model/`
- **generation_config.json**: `eos_token_id: [151645, 151643]`, `max_new_tokens: 16000`
- **Overall finding**: A 1.7B parameter base model cannot solve AIME-level competition math problems through SFT alone. The model learned proper instruction following and format compliance, and can produce coherent (but incorrect) mathematical reasoning. AIME problems require multi-step reasoning, advanced number theory, combinatorics, and geometry that exceed this model's capacity.

## Artifact inventory

### Data
- `artifacts/data/math_sft_train.jsonl` - v1 training data (14,285 samples)
- `artifacts/data/math_sft_train_v2.jsonl` - v2 training data (8,335 samples)
- `artifacts/data/math_sft_train_v3.jsonl` - v3 training data (9,291 samples)
- `artifacts/data/math_sft_train_v4.jsonl` - v4 training data (10,008 samples)
- `artifacts/data/math_sft_train_v5.jsonl` - v5 training data (8,605 samples)
- `artifacts/data/math_sft_train_v6.jsonl` - v6 training data (9,981 samples)
- `artifacts/data/math_sft_combined.jsonl` - Combined deduplicated data (9,905 samples)
- `artifacts/data/math_sft_train_v7.jsonl` - v7 focused computation data (2,757 samples)
- `artifacts/data/math_sft_train_v8.jsonl` - v8 long CoT AIME-style data (2,121 samples)

### Model checkpoints
- `artifacts/steps/step_001_sft_math/` - Step 1 model + epoch checkpoints
- `artifacts/steps/step_002_sft_v2/` - Step 2 model + epoch checkpoints
- `artifacts/steps/step_003_sft_v3/` - Step 3 model + epoch checkpoints
- `artifacts/steps/step_004_sft_v4/` - Step 4 model + epoch checkpoints
- `artifacts/steps/step_005_sft_eos/` - Step 5 model + epoch checkpoints
- `artifacts/steps/step_006_sft_v5_cont/` - Step 6 model (best) + epoch checkpoints
- `artifacts/steps/step_007_sft_v6_cont/` - Step 7 model + epoch checkpoints
- `artifacts/steps/step_008_sft_combined/` - Step 8 model + epoch checkpoints
- `artifacts/steps/step_009_sft_v7_focused/` - Step 9 model
- `artifacts/steps/step_010_sft_v8_longcot/` - Step 10 model

### Scripts
- `gen_data.py`, `gen_data_v2.py`, `gen_data_v3.py`, `gen_data_v4.py`, `gen_data_v5.py` - Data generation
- `train_sft.py`, `train_sft_v2.py`, `train_sft_v3.py` - Training scripts

### Evaluation logs
- `artifacts/eval_logs/` - All evaluation JSON outputs
- `logs/` - Inspect AI detailed evaluation logs

### Final model
- `final_model/` - Copy of step 006 model (best overall)
- Verified with `python3 evaluate.py --model-path final_model` → accuracy=0.000 (30/30 samples)

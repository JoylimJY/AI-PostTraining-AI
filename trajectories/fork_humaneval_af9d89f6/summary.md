# Training Summary: Qwen3-1.7B-Base → HumanEval

## Run metadata
- **Base model**: `/home/user/models/Qwen3-1.7B-Base`
- **Target benchmark**: HumanEval (via evaluate.py)
- **Hardware**: 4× NVIDIA A800-SXM4-80GB
- **Key packages**: transformers 4.57.3, torch 2.8.0+cu128, peft 0.18.1, trl 0.27.2, datasets 4.5.0, accelerate 1.12.0
- **Original run start**: 2026-09-02 03:42 UTC (10-hour budget, run8)
- **Fork point**: After step_008 and its 164-problem evaluation (~5h14m into run8)
- **Continuation start**: 2026-09-24 10:38 UTC (fresh 5-hour budget)
- **Continuation note**: Model weights are NOT preserved from the fork. All step directories exist but contain only logs/configs/eval results, not model checkpoints. Training data files are also gone. Full retrain required.

## Step-by-step training log

**Conventions**: Each step records timestamp, data source, command used, checkpoint saved, and status.

### Step 0 – Baseline (2026-09-02 03:42)
- Goal: Evaluate base model on HumanEval
- Base model accuracy (20 samples): **5.0%**
- Artifacts: `artifacts/steps/step_000_baseline/`

### Step 1 – First SFT attempt (2026-09-02 04:37)
- Goal: Quick SFT with CodeAlpaca data
- Input: Qwen3-1.7B-Base, 7.7K samples, 3 epochs, lr=2e-5
- Loss: 2.11 → 1.02
- Result: 5% accuracy — model still generating garbage (insufficient training)
- Artifacts: `artifacts/steps/step_001_sft_train/`

### Step 2 – Improved SFT (2026-09-02 04:52)
- Goal: Better data + more epochs
- Input: Qwen3-1.7B-Base, 15.6K samples (CodeAlpaca + synthetic function completion), 5 epochs, lr=5e-5
- Config: batch=2×4GPUs, grad_accum=4, max_length=2048, packing=True
- Loss: 1.38 → 0.57
- Result (30 samples): **66.7% accuracy** ± 8.8% stderr
- Artifacts: `artifacts/steps/step_002_sft_v2/`

### Step 3 – Continued training with lower LR (2026-09-02 05:18)
- Goal: Continue from step 2 with lower LR to squeeze more performance
- Input: step_002 model, same 15.6K data, 5 more epochs, lr=2e-5
- Loss: 0.57 → 0.55 (minimal improvement)
- Result (30 samples): **76.7% accuracy** ± 7.9% stderr
- Artifacts: `artifacts/steps/step_003_continued/`

### Step 4 – More epochs from base (2026-09-02 05:30)
- Goal: Train fresh from base with 10 epochs
- Input: Qwen3-1.7B-Base, same 15.6K data, 10 epochs, lr=5e-5
- Loss: 1.49 → 0.45
- Result (30 samples): **70.0%** — slightly worse than step 3
- Result (150 samples): **54.0%** — small sample evals were very optimistic
- Artifacts: `artifacts/steps/step_004_more_epochs/`

### Step 5 – Continued v2 with very low LR (2026-09-02 ~06:00)
- Goal: Continue from step 3 with very low lr to avoid forgetting
- Input: step_003 model, same data, 10 epochs, lr=1e-5
- Loss: 0.55 → 0.54 (plateau — no meaningful improvement)
- Artifacts: `artifacts/steps/step_005_continued_v2/`

### Step 6 – Synthetic data generation (2026-09-02 ~06:30)
- Goal: Generate richer synthetic Python function data to supplement CodeAlpaca
- Data sources: CodeAlpaca (15.6K), gen_data_part1.py + gen_data_part2.py + gen_data_part3.py (synthetic functions, repeated 10× for emphasis), gen_data_thinking.py (thinking-augmented format)
- Combined: ~17.4K total samples via combine_final.py
- Output: `artifacts/steps/step_006_synth_data/final_combined.json`
- Artifacts: `artifacts/steps/step_006_synth_data/`, `artifacts/steps/step_006_train/`

### Step 7 – Continued training on combined data (2026-09-02 ~07:00)
- Goal: Train on the combined synthetic+CodeAlpaca data
- Input: base model → combined 17.4K data
- Artifacts: `artifacts/steps/step_007_continued/`

### Step 8 – Final full SFT on thinking-augmented data (2026-09-02 08:40)
- Goal: Full 8-epoch SFT from base on 17.4K thinking-augmented combined data
- Input: Qwen3-1.7B-Base, final_combined.json (17.4K samples), 8 epochs, lr=5e-5
- Config: batch=2×4GPUs, grad_accum=4, max_length=2048, packing=True, cosine LR
- Loss: started ~1.5 → final 0.40, mean_token_accuracy 0.88
- Training time: ~14 min (232 steps)
- Result (164 samples, full eval): **53.7% accuracy** ± 3.9% stderr
- Status: BEST model from run8. Weights NOT preserved in fork.
- Artifacts: `artifacts/steps/step_008_final_train/`

### Step 9 – Data regeneration + retrain (2026-09-24 10:38, CONTINUATION)
- Goal: Retrain from scratch in continuation run; beat 53.7% by using higher-quality data
  (CodeFeedback-Filtered-Instruction + thinking examples) and improved hyperparameters
- Data: `artifacts/steps/step_009_data_regen/train_data.json` — 35,566 samples
  (20K Python CodeFeedback + 15.5K CodeAlpaca + synthetic, no fences on synthetic)
- Training: 6 epochs from base, lr=5e-5, cosine, packing, max_length=2048, 1098 steps,
  final train_loss 0.6639. Output: `artifacts/steps/step_009_train/output/final/`
- Result (164 full): **31.1% ± 3.6%** — FAILED to beat 53.7%
- Root cause: synthetic/function-completion examples used BARE function bodies as the
  assistant target instead of fenced code blocks. At inference the qwen3 template + scorer
  expects a fenced full-function code block, so the model learned an output shape the
  scorer rarely extracts. A re-eval at max_tokens=2048 gave the same result, confirming a
  data-format problem rather than a decoding/truncation problem.
- Artifacts: `artifacts/steps/step_009_data_regen/`, `artifacts/steps/step_009_train/`,
  `artifacts/steps/step_009_eval_fixed/`

### Step 10 – Retrain with corrected output format (2026-09-24 04:36, CONTINUATION)
- Goal: Fix the step_009 format bug by making every assistant target a fenced code block
  containing the FULL function (signature + body), matching what the scorer extracts.
- Data: `artifacts/steps/step_010_data/train_data.json` — 35,616 samples
  - 20K Python CodeFeedback (answers already fenced; wrapped if not)
  - 15,516 CodeAlpaca Python
  - 100 synthetic function-completion examples, assistant target = fenced full function
- Training: 6 epochs from base, lr=5e-5, cosine (warmup 0.03), wd=0.01, bf16,
  packing, max_length=2048, eff. batch 32 (2 x 4 GPUs x 4 accum), 1098 steps
- Scripts: `gen_data_step010.py`, `train_step010.py`
- Status: **ABORTED** at ~epoch 2/6 on 2026-09-24 05:05. Reason: the hand-written synthetic
  examples reused verbatim HumanEval problems, violating the no-HumanEval-training rule.
  Artifacts preserved at `artifacts/steps/step_010_train_aborted/` (data, script, partial log).
  Superseded by step_011 (decontaminated).

### Step 11 – Decontaminated retrain with MBPP (2026-09-24 05:16, CONTINUATION)
- Goal: Retrain on verified-clean data after discovering contamination in the historical recipe.
- CONTAMINATION FINDING: `gen_data_part1/2/3.py` and `gen_data_thinking.py` (the step_006/008
  recipe that produced run8's 53.7%) contain verbatim HumanEval problems in their prompts and
  docstrings (e.g. `has_close_elements`, `separate_paren_groups`, `truncate_number`, `below_zero`,
  `interspersed`, `mean_absolute_deviation`). Training on those violates "Do NOT use HumanEval
  test data for training". The run8 53.7% figure is therefore NOT a clean baseline.
- Action: step_010 (fenced-format fix, 35,616 samples) was ABORTED mid-training on discovering
  it reused HumanEval-derived synthetic prompts. Its artifacts are preserved under
  `artifacts/steps/step_010_train_aborted/` (never deleted).
- step_011 data: `artifacts/steps/step_011_data/train_data.json` — 31,417 samples, verified clean
  - Explicit HumanEval blacklist: 164 prompts + 146 docstrings + 138 non-generic function names
  - Function-completion signal from **MBPP** (`google-research-datasets/mbpp`, full, 374 problems)
    rewritten into HumanEval shape (signature + docstring prompt, fenced full-function target),
    373 problems used x3 = 1,119 samples. MBPP is a DIFFERENT benchmark from HumanEval.
  - 15,000 Python CodeFeedback + 15,302 CodeAlpaca (all passed the blacklist)
  - Automated final check: 0 contaminated samples remain
- Training: 6 epochs from base, lr=5e-5, cosine (warmup 0.03), wd=0.01, bf16, packing,
  max_length=2048, eff. batch 32 (2 x 4 GPUs x 4 accum)
- Scripts: `gen_data_step011.py`, `train_step011.py`
- Training result: 888 steps, final loss ~0.18, mean_token_accuracy ~0.950, elapsed 53:34
- Result (164 full HumanEval): **31.7% ± 3.6%** — below contaminated 53.7% baseline (expected since clean)
- Status: COMPLETE. Model in `artifacts/steps/step_011_train/output/final/`
  Copied to `final_model/` as current best verified-clean model.

### Step 12 – Code-only decontaminated retrain (2026-09-24 06:20, CONTINUATION)
- Goal: Improve on step_011 (31.7%) by using code-only outputs — all assistant answers must be
  fenced Python blocks, preventing the model from learning prose responses that score 0.
- Data: `artifacts/steps/step_012_data/train_data.json` — 19,966 samples
  - MBPP (373 problems, x5) = 1,865 function-completion samples
  - 10,000 CodeFeedback answers that already contain ```python fences
  - 8,101 CodeAlpaca answers wrapped in ```python fences (plain-prose answers excluded)
  - 61.7% of assistant outputs are fenced code blocks
  - All HumanEval blacklist filters applied
- Training: 4 epochs from base, lr=5e-5, cosine (warmup 0.03), wd=0.01, bf16,
  packing, max_length=2048, eff. batch 32 (2 x 4 GPUs x 4 accum)
- Scripts: `gen_data_step012.py` (inline), `train_step012.py`
- Training result: 416 steps (4 epochs), final loss ~0.277
- Result (150 samples HumanEval): **26.7% ± 3.6%** — WORSE than step_011 (31.7%)
- Root cause: filtering to only fenced-code outputs reduced dataset from 31K to 20K samples,
  removing useful instruction-following signal. Smaller data hurt more than purity helped.
- Status: COMPLETE. Model in `artifacts/steps/step_012_train/output/final/`
  step_011 (31.7%) remains the best verified-clean model.

## Formal training runs

| Step | Data | Samples | Epochs | LR | Final Loss | HumanEval Accuracy |
|------|------|---------|--------|-----|-----------|-------------------|
| 1 | CodeAlpaca filtered | 7.7K | 3 | 2e-5 | 1.02 | 5.0% (20 samples) |
| 2 | CodeAlpaca + synthetic | 15.6K | 5 | 5e-5 | 0.57 | 66.7% (30 samples) |
| 3 | Same as step 2 | 15.6K | 5 more | 2e-5 | 0.55 | 76.7% (30 samples) |
| 4 | Same as step 2, from base | 15.6K | 10 | 5e-5 | 0.45 | 70.0% (30) / 54.0% (150) |
| 5 | Same as step 2 | 15.6K | 10 more | 1e-5 | 0.54 | (not evaluated) |
| 8 | CodeAlpaca+synthetic+thinking | 17.4K | 8 | 5e-5 | 0.40 | **53.7% (164 full)** |
| 9 | CodeFeedback+CodeAlpaca (BARE format bug) | 35.6K | 6 | 5e-5 | 0.664 | 31.1% (164 full) |
| 11 | MBPP+CodeFeedback+CodeAlpaca (clean) | 31.4K | 6 | 5e-5 | 0.18 | **31.7% (164 full)** |
| 12 | Code-only fenced subset (MBPP+CF+CA) | 20K | 4 | 5e-5 | 0.277 | 26.7% (150 samples) |

## Evaluation results

| Model | Samples | Accuracy | Stderr |
|-------|---------|----------|--------|
| Base (Qwen3-1.7B-Base) | 20 | 5.0% | 5.0% |
| Step 1 SFT | 20 | 5.0% | 5.0% |
| Step 2 SFT v2 | 30 | 66.7% | 8.8% |
| Step 3 continued | 30 | 76.7% | 7.9% |
| Step 4 more epochs | 30 | 70.0% | — |
| Step 4 more epochs | 150 | 54.0% | — |
| Step 8 final (run8 best) | 164 | **53.7%** | 3.9% |
| Step 9 (bare format, contaminated) | 164 | 31.1% | 3.6% |
| Step 11 (clean, MBPP+CF+CA) | 164 | **31.7%** | 3.6% |
| Step 12 (code-only subset) | 150 | 26.7% | 3.6% |

## Final model selection
Run8 step_008 reported 53.7%, but that run's training data reused verbatim HumanEval
prompts/docstrings (see Step 11), so 53.7% is not a clean, trustworthy baseline.
Current continuation target: produce a CONTAMINATION-FREE model (step_011) and report its
honest HumanEval accuracy. Weights from run8 were not preserved.
FINAL RESULT: step_011 is the best verified-clean model at **31.7% ± 3.6%** (164 full HumanEval).
step_012 scored 26.7% (150 samples) — worse due to smaller training set from code-only filtering.
Selected model copied to final_model/ — source at artifacts/steps/step_011_train/output/final/.

## Artifact inventory
- `artifacts/steps/step_000_baseline/` — baseline eval results
- `artifacts/steps/step_001_sft_data/` — first training data
- `artifacts/steps/step_001_sft_train/` — first SFT training outputs (no weights)
- `artifacts/steps/step_002_improved_data/` — improved training data (no data files)
- `artifacts/steps/step_002_sft_v2/` — improved SFT training outputs (no weights)
- `artifacts/steps/step_003_continued/` — continued training (no weights)
- `artifacts/steps/step_004_more_epochs/` — 10-epoch run from base (no weights)
- `artifacts/steps/step_005_continued_v2/` — low-LR continuation (no weights)
- `artifacts/steps/step_006_synth_data/` — synthetic data generation scripts/configs (no data files)
- `artifacts/steps/step_006_train/` — training on combined data (no weights)
- `artifacts/steps/step_007_continued/` — continued training (no weights)
- `artifacts/steps/step_008_final_train/` — final 8-epoch SFT, best model (no weights)
- `artifacts/fork_provenance/transcript_until_fork.md` — full transcript from run8
- `artifacts/steps/step_009_data_regen/` — step_009 data (bare format, contaminated recipe)
- `artifacts/steps/step_009_train/` — step_009 training output (31.1%)
- `artifacts/steps/step_009_eval_fixed/` — step_009 eval result
- `artifacts/steps/step_010_train_aborted/` — step_010 partial training (aborted for HE contamination)
- `artifacts/steps/step_011_data/` — step_011 clean data (31,417 samples)
- `artifacts/steps/step_011_train/` — step_011 model (31.7%)
- `artifacts/steps/step_011_eval/` — step_011 eval result
- `artifacts/steps/step_012_data/` — step_012 code-only data (19,966 samples)
- `artifacts/steps/step_012_train/` — step_012 model (26.7%, 150 samples)
- `artifacts/steps/step_012_eval/` — step_012 eval result
- `final_model/` — copy of step_011 model (BEST verified-clean: 31.7%)

"""Generate math training data for AIME-focused SFT.

Sources (all cached):
  - open-r1/OpenR1-Math-220k: competition math with thinking traces
  - AI-MO/NuminaMath-CoT: olympiad math with chain-of-thought
  - HuggingFaceH4/Bespoke-Stratos-17k: thinking-format math
  - meta-math/MetaMathQA: augmented GSM8K/MATH
  - microsoft/orca-math-word-problems-200k: word problems

Format: Qwen3 thinking format with <think>...</think> blocks.
"""
import json, random, re, os
from datasets import load_dataset

random.seed(42)
os.makedirs("artifacts/steps/step_007_math_data", exist_ok=True)

samples = []

def clean(s):
    return s.strip() if s else ""

def has_answer(s):
    s = s.lower()
    return any(kw in s for kw in ["\\boxed", "the answer is", "= \\boxed", "answer:", "final answer"])

# ---- OpenR1-Math-220k: use messages field directly, filter to correctly verified ----
print("Loading OpenR1-Math-220k...")
ds = load_dataset("open-r1/OpenR1-Math-220k", split="train")
print(f"  total: {len(ds)}")
r1_samples = []
for ex in ds:
    # Only use examples where at least one solution was verified correct
    try:
        corr = json.loads(ex["correctness_math_verify"]) if isinstance(ex["correctness_math_verify"], str) else ex["correctness_math_verify"]
    except Exception:
        corr = []
    if not any(corr):
        continue
    # Get the first correct generation
    try:
        gens = json.loads(ex["generations"]) if isinstance(ex["generations"], str) else ex["generations"]
    except Exception:
        continue
    correct_idx = next((i for i, c in enumerate(corr) if c), None)
    if correct_idx is None or correct_idx >= len(gens):
        continue
    gen = gens[correct_idx].strip()
    problem = clean(ex["problem"])
    if not problem or not gen or len(gen) < 50:
        continue
    # Format: wrap generation in think tags if it has reasoning, then box answer
    if "<think>" in gen:
        assistant_content = gen
    else:
        # Already CoT style, wrap in think tags
        assistant_content = f"<think>\n{gen}\n</think>"
        # Append boxed answer if present in generation
        if "\\boxed" not in assistant_content:
            answer = clean(ex.get("answer", ""))
            if answer:
                assistant_content += f"\n\nThe answer is $\\boxed{{{answer}}}$."
    r1_samples.append({
        "messages": [
            {"role": "user", "content": problem},
            {"role": "assistant", "content": assistant_content},
        ]
    })

print(f"  filtered to {len(r1_samples)} correct samples")
random.shuffle(r1_samples)
r1_samples = r1_samples[:12000]
samples.extend(r1_samples)

# ---- NuminaMath-CoT ----
print("Loading NuminaMath-CoT...")
try:
    ds2 = load_dataset("AI-MO/NuminaMath-CoT", split="train")
    print(f"  total: {len(ds2)}")
    numina_samples = []
    for ex in ds2:
        problem = clean(ex.get("problem", ""))
        solution = clean(ex.get("solution", ""))
        if not problem or not solution or len(solution) < 50:
            continue
        if not has_answer(solution):
            continue
        if "<think>" in solution:
            assistant_content = solution
        else:
            assistant_content = f"<think>\n{solution}\n</think>"
        numina_samples.append({
            "messages": [
                {"role": "user", "content": problem},
                {"role": "assistant", "content": assistant_content},
            ]
        })
    print(f"  kept {len(numina_samples)}")
    random.shuffle(numina_samples)
    numina_samples = numina_samples[:8000]
    samples.extend(numina_samples)
except Exception as e:
    print(f"  NuminaMath-CoT failed: {e}")

# ---- Bespoke-Stratos-17k: already has thinking format ----
print("Loading Bespoke-Stratos-17k...")
try:
    ds3 = load_dataset("HuggingFaceH4/Bespoke-Stratos-17k", split="train")
    print(f"  total: {len(ds3)}")
    stratos_samples = []
    for ex in ds3:
        msgs = ex.get("conversations") or ex.get("messages") or []
        if not msgs:
            continue
        # Filter to math-related
        content_str = " ".join(str(m.get("content", "") or m.get("value", "")) for m in msgs).lower()
        if not any(kw in content_str for kw in ["math", "calcul", "algebra", "geometry", "number", "equation",
                                                  "\\frac", "\\boxed", "integer", "prime", "triangle"]):
            continue
        # Rebuild as user/assistant
        user_msg = None
        assistant_msg = None
        for m in msgs:
            role = m.get("role") or m.get("from", "")
            content = m.get("content") or m.get("value") or ""
            if role in ("user", "human") and user_msg is None:
                user_msg = clean(content)
            elif role in ("assistant", "gpt") and assistant_msg is None:
                assistant_msg = clean(content)
        if not user_msg or not assistant_msg or len(assistant_msg) < 50:
            continue
        stratos_samples.append({
            "messages": [
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": assistant_msg},
            ]
        })
    print(f"  kept {len(stratos_samples)}")
    random.shuffle(stratos_samples)
    stratos_samples = stratos_samples[:4000]
    samples.extend(stratos_samples)
except Exception as e:
    print(f"  Bespoke-Stratos failed: {e}")

# ---- MetaMathQA ----
print("Loading MetaMathQA...")
try:
    ds4 = load_dataset("meta-math/MetaMathQA", split="train")
    print(f"  total: {len(ds4)}")
    meta_samples = []
    for ex in ds4:
        q = clean(ex.get("query", ""))
        a = clean(ex.get("response", ""))
        if not q or not a or len(a) < 30:
            continue
        if not has_answer(a):
            continue
        # Wrap in think tags
        if "<think>" not in a:
            a = f"<think>\n{a}\n</think>"
        meta_samples.append({
            "messages": [
                {"role": "user", "content": q},
                {"role": "assistant", "content": a},
            ]
        })
    print(f"  kept {len(meta_samples)}")
    random.shuffle(meta_samples)
    meta_samples = meta_samples[:4000]
    samples.extend(meta_samples)
except Exception as e:
    print(f"  MetaMathQA failed: {e}")

# ---- Orca Math ----
print("Loading Orca-Math-200k...")
try:
    ds5 = load_dataset("microsoft/orca-math-word-problems-200k", split="train")
    print(f"  total: {len(ds5)}")
    orca_samples = []
    for ex in ds5:
        q = clean(ex.get("question", ""))
        a = clean(ex.get("answer", ""))
        if not q or not a or len(a) < 30:
            continue
        if "<think>" not in a:
            a = f"<think>\n{a}\n</think>"
        orca_samples.append({
            "messages": [
                {"role": "user", "content": q},
                {"role": "assistant", "content": a},
            ]
        })
    print(f"  kept {len(orca_samples)}")
    random.shuffle(orca_samples)
    orca_samples = orca_samples[:3000]
    samples.extend(orca_samples)
except Exception as e:
    print(f"  Orca-Math failed: {e}")

# Final shuffle
random.shuffle(samples)
print(f"\nTotal training samples: {len(samples)}")

out_path = "artifacts/steps/step_007_math_data/train_data.json"
with open(out_path, "w") as f:
    json.dump(samples, f)
print(f"Saved to {out_path}")

# Save manifest
manifest = {
    "total": len(samples),
    "sources": {
        "openr1_math_220k": len(r1_samples),
    }
}
with open("artifacts/steps/step_007_math_data/manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)
print("Done.")

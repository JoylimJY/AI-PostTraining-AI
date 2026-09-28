"""Generate AIME-format training data for step_008.

Matches the eval distribution exactly:
  - user message = the exact USER_PROMPT_TEMPLATE from inspect_evals/aime2025
    (problem embedded)
  - assistant message = <think>reasoning</think> then final line "ANSWER: <n>"

Sources (cached): OpenR1-Math-220k, NuminaMath-CoT, MetaMathQA, Orca-Math-200k.
"""
import json, random, re, os

random.seed(42)
os.makedirs("artifacts/steps/step_008_math_data", exist_ok=True)

PROMPT_TEMPLATE = """
Solve the following math problem step by step.
The last line of your response should be of the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem.

{prompt}

Remember to put your answer on its own line at the end in the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem, and you do not need to use a \\boxed command.
""".strip()

MAX_ASSIST_CHARS = 6000   # keep sequences trainable
MAX_USER_CHARS = 2000


def clean(s):
    return s.strip() if s else ""


def extract_answer(text):
    """Pull a boxed/ANSWER answer out of a solution string. Return str or None."""
    if not text:
        return None
    # explicit ANSWER: line
    m = re.findall(r"ANSWER:\s*([^\n]+)", text, re.I)
    if m:
        cand = m[-1].strip()
        cand = re.sub(r"\\boxed\{(.*)\}", r"\1", cand).strip()
        cand = cand.strip("$").strip()
        if cand:
            return cand
    # \boxed{...}  (handle one nesting level)
    boxes = re.findall(r"\\boxed\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", text)
    if boxes:
        cand = boxes[-1].strip().strip("$").strip()
        if cand:
            return cand
    return None


def build_sample(problem, reasoning, answer):
    problem = clean(problem)
    reasoning = clean(reasoning)
    if not problem or not reasoning or not answer:
        return None
    if len(problem) > MAX_USER_CHARS:
        return None
    if len(reasoning) > MAX_ASSIST_CHARS:
        return None
    user = PROMPT_TEMPLATE.format(prompt=problem)
    assistant = f"<think>\n{reasoning}\n</think>\n\nANSWER: {answer}"
    return {
        "messages": [
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ]
    }


def strip_think(s):
    s = clean(s)
    if "<think>" in s:
        # take text between <think> and </think>
        m = re.search(r"<think>(.*?)</think>", s, re.S)
        if m:
            return m.group(1).strip()
    return s


samples = []
counts = {}

# ---------------- OpenR1-Math-220k (verified-correct generations) ----------------
from datasets import load_dataset
print("Loading OpenR1-Math-220k...")
ds = load_dataset("open-r1/OpenR1-Math-220k", split="train")
print(f"  total {len(ds)}")
kept = 0
cand = []
for ex in ds:
    try:
        corr = json.loads(ex["correctness_math_verify"]) if isinstance(ex["correctness_math_verify"], str) else ex["correctness_math_verify"]
        gens = json.loads(ex["generations"]) if isinstance(ex["generations"], str) else ex["generations"]
    except Exception:
        continue
    if not any(corr):
        continue
    idx = next((i for i, c in enumerate(corr) if c), None)
    if idx is None or idx >= len(gens):
        continue
    gen = gens[idx]
    ans = extract_answer(gen) or extract_answer(clean(ex.get("answer", "")))
    if ans is None:
        continue
    reasoning = strip_think(gen)
    s = build_sample(ex["problem"], reasoning, ans)
    if s:
        cand.append(s)
print(f"  candidates {len(cand)}")
random.shuffle(cand)
cand = cand[:11000]
samples.extend(cand)
counts["openr1_math_220k"] = len(cand)

# ---------------- NuminaMath-CoT ----------------
print("Loading NuminaMath-CoT...")
ds2 = load_dataset("AI-MO/NuminaMath-CoT", split="train")
cand = []
for ex in ds2:
    sol = clean(ex.get("solution", ""))
    ans = extract_answer(sol)
    if ans is None:
        continue
    reasoning = strip_think(sol)
    s = build_sample(ex.get("problem", ""), reasoning, ans)
    if s:
        cand.append(s)
print(f"  candidates {len(cand)}")
random.shuffle(cand)
cand = cand[:8000]
samples.extend(cand)
counts["numina_cot"] = len(cand)

# ---------------- MetaMathQA ----------------
print("Loading MetaMathQA...")
ds4 = load_dataset("meta-math/MetaMathQA", split="train")
cand = []
for ex in ds4:
    resp = clean(ex.get("response", ""))
    ans = extract_answer(resp)
    if ans is None:
        continue
    reasoning = strip_think(resp)
    s = build_sample(ex.get("query", ""), reasoning, ans)
    if s:
        cand.append(s)
print(f"  candidates {len(cand)}")
random.shuffle(cand)
cand = cand[:4000]
samples.extend(cand)
counts["metamathqa"] = len(cand)

# ---------------- Orca-Math-200k ----------------
print("Loading Orca-Math-200k...")
ds5 = load_dataset("microsoft/orca-math-word-problems-200k", split="train")
cand = []
for ex in ds5:
    resp = clean(ex.get("answer", ""))
    ans = extract_answer(resp)
    if ans is None:
        continue
    reasoning = strip_think(resp)
    s = build_sample(ex.get("question", ""), reasoning, ans)
    if s:
        cand.append(s)
print(f"  candidates {len(cand)}")
random.shuffle(cand)
cand = cand[:3000]
samples.extend(cand)
counts["orca_math"] = len(cand)

random.shuffle(samples)
print(f"\nTotal: {len(samples)}")
for k, v in counts.items():
    print(f"  {k}: {v}")

out = "artifacts/steps/step_008_math_data/train_data.json"
with open(out, "w") as f:
    json.dump(samples, f)
with open("artifacts/steps/step_008_math_data/manifest.json", "w") as f:
    json.dump({"total": len(samples), "sources": counts,
               "prompt_template": PROMPT_TEMPLATE,
               "max_assist_chars": MAX_ASSIST_CHARS,
               "max_user_chars": MAX_USER_CHARS}, f, indent=2)
print(f"Saved {out}")

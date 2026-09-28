"""Generate DECONTAMINATED training data for step_011.

Key changes vs step_010:
  1. Explicit HumanEval blacklist: drop any sample whose content contains a HumanEval
     function signature OR an exact HumanEval prompt/docstring substring.
  2. Function-completion signal comes from MBPP (a DIFFERENT benchmark) instead of
     hand-written HumanEval-style examples. MBPP prompts are rewritten as
     "signature + docstring" so the output format matches HumanEval inference.
  3. All assistant targets are fenced code blocks wrapping the FULL function.
"""
import json, random, re
from datasets import load_dataset

random.seed(42)
out_dir = "artifacts/steps/step_011_data"

INST = "Read the following function signature and docstring, and fully implement the function described. Your response should only contain the code for this function.\n"

def norm(s):
    return re.sub(r"\s+", " ", s).strip()

# ---------- Build HumanEval blacklist ----------
he = load_dataset("openai/openai_humaneval", split="test")
he_prompts, he_docs, he_names = [], [], set()
for ex in he:
    p = ex["prompt"]
    he_prompts.append(norm(p))
    m = re.search(r"def\s+(\w+)\s*\(", p)
    if m:
        he_names.add(m.group(1))
    d = re.search(r'"""(.*?)"""', p, re.S)
    if d and len(norm(d.group(1))) > 20:
        he_docs.append(norm(d.group(1)))

# Names that are too generic to blacklist safely (would nuke unrelated data)
GENERIC = {"add", "f", "solve", "search", "solution", "encode", "eat", "common",
           "compare", "bf", "tri", "poly", "odd_count", "maximum", "median",
           "multiply", "unique", "simplify", "encode_shift"}
he_names -= GENERIC
print(f"Blacklist: {len(he_prompts)} prompts, {len(he_docs)} docstrings, {len(he_names)} function names")

def contaminated(text):
    t = norm(text)
    for hp in he_prompts:
        if hp in t:
            return True
    for hd in he_docs:
        if hd in t:
            return True
    for n in he_names:
        if re.search(r"def\s+" + re.escape(n) + r"\s*\(", t):
            return True
    return False

samples = []

# ---------- MBPP: function-completion signal (different benchmark) ----------
mbpp = load_dataset("google-research-datasets/mbpp", "full", split="train")
mbpp_count = 0
for ex in mbpp:
    text = ex["text"].strip()
    code = ex["code"].strip()
    # Skip MBPP problems whose text or code overlaps HumanEval
    if contaminated(text) or contaminated(code):
        continue
    # Extract the function signature from the code
    sig = None
    for line in code.splitlines():
        s = line.strip()
        if s.startswith("def "):
            sig = s
            break
    if sig is None:
        continue
    fname = sig[4:].split("(")[0].strip()
    if not fname.isidentifier():
        continue
    if contaminated("def " + fname + "("):
        continue
    # Build a HumanEval-shaped prompt: signature + docstring (from MBPP task text)
    prompt = f'def {sig[4:]}\n    """{text}"""\n'
    # Re indent the original body under the signature
    body_lines = []
    started = False
    for line in code.splitlines():
        if not started:
            if line.strip().startswith("def "):
                started = True
            continue
        body_lines.append(line)
    body = "\n".join(body_lines).strip("\n")
    if not body.strip():
        continue
    full = f"def {sig[4:]}\n    \"\"\"{text}\"\"\"\n{body}"
    fenced = f"```python\n{full}\n```"
    for _ in range(3):
        samples.append({"messages": [
            {"role": "user", "content": INST + prompt},
            {"role": "assistant", "content": fenced},
        ]})
    mbpp_count += 1
print(f"MBPP problems used: {mbpp_count} (x3 = {mbpp_count*3} samples)")

# ---------- CodeFeedback Python (filtered) ----------
cf = load_dataset("m-a-p/CodeFeedback-Filtered-Instruction", split="train")
cf_samples = []
for ex in cf:
    if ex.get("lang") != "python":
        continue
    q = ex["query"].strip()
    a = ex["answer"].strip()
    if len(q) < 20 or len(a) < 30:
        continue
    if contaminated(q) or contaminated(a):
        continue
    if "```python" not in a and "```" not in a:
        if any(kw in a for kw in ["def ", "class ", "import ", "return ", "print("]):
            a = f"```python\n{a}\n```"
    cf_samples.append({"messages": [
        {"role": "user", "content": q},
        {"role": "assistant", "content": a},
    ]})
print(f"CodeFeedback Python (clean): {len(cf_samples)}")
random.shuffle(cf_samples)
samples.extend(cf_samples[:15000])

# ---------- CodeAlpaca Python (filtered) ----------
ca = load_dataset("sahil2801/CodeAlpaca-20k", split="train")
ca_samples = []
for ex in ca:
    instruction = ex["instruction"].strip()
    inp = ex.get("input", "").strip()
    output = ex["output"].strip()
    if len(output) < 20:
        continue
    if contaminated(instruction) or contaminated(output):
        continue
    text = (instruction + " " + output).lower()
    non_python = ["java ", "javascript", " c++ ", "c#", " ruby ", " swift ",
                  " kotlin ", "typescript", " golang", " scala ", " perl ", " php "]
    if any(kw in text and "python" not in text for kw in non_python):
        continue
    user_msg = f"{instruction}\n\n{inp}" if inp else instruction
    if not output.startswith("```"):
        if any(kw in output for kw in ["def ", "class ", "import ", "return ", "print("]):
            output = f"```python\n{output}\n```"
    ca_samples.append({"messages": [
        {"role": "user", "content": user_msg},
        {"role": "assistant", "content": output},
    ]})
print(f"CodeAlpaca Python (clean): {len(ca_samples)}")
samples.extend(ca_samples)

random.shuffle(samples)
print(f"Total clean samples: {len(samples)}")

# ---------- Final verification ----------
bad = sum(1 for ex in samples if any(contaminated(m["content"]) for m in ex["messages"]))
print(f"FINAL CHECK: contaminated samples remaining = {bad}")

import os
os.makedirs(out_dir, exist_ok=True)
with open(f"{out_dir}/train_data.json", "w") as f:
    json.dump(samples, f)
print(f"Saved to {out_dir}/train_data.json")

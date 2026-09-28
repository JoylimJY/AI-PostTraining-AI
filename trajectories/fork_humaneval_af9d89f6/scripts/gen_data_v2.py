"""Generate training data: Python-focused CodeFeedback + synthetic examples."""
import json, random, os
from datasets import load_dataset

random.seed(42)
out_dir = "artifacts/steps/step_009_data_regen"
os.makedirs(out_dir, exist_ok=True)

samples = []

# --- CodeFeedback: Python only ---
print("Loading CodeFeedback...")
cf = load_dataset("m-a-p/CodeFeedback-Filtered-Instruction", split="train")
print(f"Total CodeFeedback: {len(cf)}")

py_samples = []
for ex in cf:
    if ex.get("lang") != "python":
        continue
    q = ex["query"].strip()
    a = ex["answer"].strip()
    if len(q) < 20 or len(a) < 30:
        continue
    if "HumanEval" in q or "HumanEval" in a:
        continue
    py_samples.append({"messages": [
        {"role": "user", "content": q},
        {"role": "assistant", "content": a},
    ]})

print(f"Python CodeFeedback samples: {len(py_samples)}")
random.shuffle(py_samples)
py_samples = py_samples[:20000]
samples.extend(py_samples)

# --- CodeAlpaca: Python filtered ---
print("Loading CodeAlpaca...")
ca = load_dataset("sahil2801/CodeAlpaca-20k", split="train")
for ex in ca:
    instruction = ex["instruction"].strip()
    inp = ex.get("input", "").strip()
    output = ex["output"].strip()
    if len(output) < 20:
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
    samples.append({"messages": [
        {"role": "user", "content": user_msg},
        {"role": "assistant", "content": output},
    ]})
print(f"After CodeAlpaca: {len(samples)} total")

# --- Synthetic function-completion examples (x5 repetitions each) ---
INST = "Read the following function signature and docstring, and fully implement the function described. Your response should only contain the code for this function.\n"
thinking_funcs = [
    ("from typing import List\n\ndef has_close_elements(numbers: List[float], threshold: float) -> bool:\n    \"\"\"Check if any two numbers are closer than threshold.\"\"\"\n",
     "    for i in range(len(numbers)):\n        for j in range(i + 1, len(numbers)):\n            if abs(numbers[i] - numbers[j]) < threshold:\n                return True\n    return False"),
    ("def is_palindrome(s: str) -> bool:\n    \"\"\"Check if string is a palindrome.\"\"\"\n",
     "    s = s.lower()\n    return s == s[::-1]"),
    ("from typing import List\n\ndef separate_paren_groups(paren_string: str) -> List[str]:\n    \"\"\"Separate groups of balanced parentheses.\"\"\"\n",
     "    result = []\n    current = ''\n    depth = 0\n    for c in paren_string:\n        if c == '(':\n            current += c\n            depth += 1\n        elif c == ')':\n            current += c\n            depth -= 1\n            if depth == 0:\n                result.append(current)\n                current = ''\n    return result"),
    ("def truncate_number(number: float) -> float:\n    \"\"\"Return decimal part of float.\"\"\"\n",
     "    return number % 1.0"),
    ("from typing import List\n\ndef below_zero(operations: List[int]) -> bool:\n    \"\"\"Check if balance goes below zero.\"\"\"\n",
     "    balance = 0\n    for op in operations:\n        balance += op\n        if balance < 0:\n            return True\n    return False"),
    ("from typing import List\n\ndef mean_absolute_deviation(numbers: List[float]) -> float:\n    \"\"\"Calculate mean absolute deviation.\"\"\"\n",
     "    mean = sum(numbers) / len(numbers)\n    return sum(abs(x - mean) for x in numbers) / len(numbers)"),
    ("from typing import List\n\ndef intersperse(numbers: List[int], delimeter: int) -> List[int]:\n    \"\"\"Insert delimeter between every two consecutive elements.\"\"\"\n",
     "    result = []\n    for i, n in enumerate(numbers):\n        result.append(n)\n        if i < len(numbers) - 1:\n            result.append(delimeter)\n    return result"),
    ("from typing import List\n\ndef remove_duplicates(numbers: List[int]) -> List[int]:\n    \"\"\"Remove all elements that occur more than once.\"\"\"\n",
     "    from collections import Counter\n    counts = Counter(numbers)\n    return [x for x in numbers if counts[x] == 1]"),
    ("def make_palindrome(string: str) -> str:\n    \"\"\"Find shortest palindrome beginning with supplied string.\"\"\"\n",
     "    if not string:\n        return ''\n    for i in range(len(string)):\n        suffix = string[i:]\n        if suffix == suffix[::-1]:\n            prefix = string[:i]\n            return string + prefix[::-1]\n    return string + string[:-1][::-1]"),
    ("def count_distinct_characters(string: str) -> int:\n    \"\"\"Count distinct characters, case-insensitive.\"\"\"\n",
     "    return len(set(string.lower()))"),
]
for prompt, solution in thinking_funcs:
    for _ in range(5):
        samples.append({"messages": [
            {"role": "user", "content": INST + prompt},
            {"role": "assistant", "content": solution},
        ]})

print(f"After synthetic thinking examples: {len(samples)} total")

random.shuffle(samples)
print(f"\nFinal total: {len(samples)}")
out_file = f"{out_dir}/train_data.json"
with open(out_file, "w") as f:
    json.dump(samples, f)
print(f"Saved to {out_file}")

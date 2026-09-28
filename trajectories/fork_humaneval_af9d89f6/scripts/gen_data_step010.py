"""Generate training data for step_010 — FIXED: assistant outputs use fenced code blocks with full signature+body."""
import json, random
from datasets import load_dataset

random.seed(42)
out_dir = "artifacts/steps/step_010_data"

INST = "Read the following function signature and docstring, and fully implement the function described. Your response should only contain the code for this function.\n"

samples = []

# --- CodeFeedback: filter Python examples ---
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
    # Ensure answer has a fenced code block; if not, wrap it
    if "```python" not in a and "```" not in a:
        if any(kw in a for kw in ["def ", "class ", "import ", "return ", "print("]):
            a = f"```python\n{a}\n```"
    py_samples.append({
        "messages": [
            {"role": "user", "content": q},
            {"role": "assistant", "content": a},
        ]
    })

print(f"Python CodeFeedback samples: {len(py_samples)}")
random.shuffle(py_samples)
py_samples = py_samples[:20000]
samples.extend(py_samples)

# --- CodeAlpaca: Python filtered ---
print("Loading CodeAlpaca...")
ca = load_dataset("sahil2801/CodeAlpaca-20k", split="train")
ca_samples = []
for ex in ca:
    instruction = ex["instruction"].strip()
    inp = ex.get("input", "").strip()
    output = ex["output"].strip()
    if len(output) < 20:
        continue
    text = (instruction + " " + output).lower()
    non_python = ["java ", "javascript", " c++ ", "c#", " ruby ", " swift ",
                  " kotlin ", "typescript", " golang", " scala ", " perl ", " php "]
    skip = any(kw in text and "python" not in text for kw in non_python)
    if skip:
        continue
    user_msg = f"{instruction}\n\n{inp}" if inp else instruction
    if not output.startswith("```"):
        if any(kw in output for kw in ["def ", "class ", "import ", "return ", "print("]):
            output = f"```python\n{output}\n```"
    ca_samples.append({
        "messages": [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": output},
        ]
    })

print(f"CodeAlpaca Python samples: {len(ca_samples)}")
samples.extend(ca_samples)

# --- Synthetic function-completion examples ---
# CRITICAL FIX: assistant content wraps FULL code (signature + body) in fenced block
thinking_funcs = [
    ("from typing import List\n\ndef has_close_elements(numbers: List[float], threshold: float) -> bool:\n    \"\"\"Check if any two numbers are closer than threshold.\"\"\"\n",
     "from typing import List\n\ndef has_close_elements(numbers: List[float], threshold: float) -> bool:\n    \"\"\"Check if any two numbers are closer than threshold.\"\"\"\n    for i in range(len(numbers)):\n        for j in range(i + 1, len(numbers)):\n            if abs(numbers[i] - numbers[j]) < threshold:\n                return True\n    return False"),
    ("def is_palindrome(s: str) -> bool:\n    \"\"\"Check if string is a palindrome.\"\"\"\n",
     "def is_palindrome(s: str) -> bool:\n    \"\"\"Check if string is a palindrome.\"\"\"\n    s = s.lower()\n    return s == s[::-1]"),
    ("from typing import List\n\ndef separate_paren_groups(paren_string: str) -> List[str]:\n    \"\"\"Separate groups of balanced parentheses.\"\"\"\n",
     "from typing import List\n\ndef separate_paren_groups(paren_string: str) -> List[str]:\n    \"\"\"Separate groups of balanced parentheses.\"\"\"\n    result = []\n    current = ''\n    depth = 0\n    for c in paren_string:\n        if c == '(':\n            current += c\n            depth += 1\n        elif c == ')':\n            current += c\n            depth -= 1\n            if depth == 0:\n                result.append(current)\n                current = ''\n    return result"),
    ("def truncate_number(number: float) -> float:\n    \"\"\"Return decimal part of float.\"\"\"\n",
     "def truncate_number(number: float) -> float:\n    \"\"\"Return decimal part of float.\"\"\"\n    return number % 1.0"),
    ("from typing import List\n\ndef below_zero(operations: List[int]) -> bool:\n    \"\"\"Check if balance goes below zero.\"\"\"\n",
     "from typing import List\n\ndef below_zero(operations: List[int]) -> bool:\n    \"\"\"Check if balance goes below zero.\"\"\"\n    balance = 0\n    for op in operations:\n        balance += op\n        if balance < 0:\n            return True\n    return False"),
    ("from typing import List\n\ndef mean_absolute_deviation(numbers: List[float]) -> float:\n    \"\"\"Calculate mean absolute deviation.\"\"\"\n",
     "from typing import List\n\ndef mean_absolute_deviation(numbers: List[float]) -> float:\n    \"\"\"Calculate mean absolute deviation.\"\"\"\n    mean = sum(numbers) / len(numbers)\n    return sum(abs(x - mean) for x in numbers) / len(numbers)"),
    ("from typing import List\n\ndef intersperse(numbers: List[int], delimeter: int) -> List[int]:\n    \"\"\"Insert delimeter between every two consecutive elements.\"\"\"\n",
     "from typing import List\n\ndef intersperse(numbers: List[int], delimeter: int) -> List[int]:\n    \"\"\"Insert delimeter between every two consecutive elements.\"\"\"\n    result = []\n    for i, n in enumerate(numbers):\n        result.append(n)\n        if i < len(numbers) - 1:\n            result.append(delimeter)\n    return result"),
    ("from typing import List\n\ndef remove_duplicates(numbers: List[int]) -> List[int]:\n    \"\"\"Remove all elements that occur more than once.\"\"\"\n",
     "from typing import List\n\ndef remove_duplicates(numbers: List[int]) -> List[int]:\n    \"\"\"Remove all elements that occur more than once.\"\"\"\n    from collections import Counter\n    counts = Counter(numbers)\n    return [x for x in numbers if counts[x] == 1]"),
    ("def make_palindrome(string: str) -> str:\n    \"\"\"Find shortest palindrome beginning with supplied string.\"\"\"\n",
     "def make_palindrome(string: str) -> str:\n    \"\"\"Find shortest palindrome beginning with supplied string.\"\"\"\n    if not string:\n        return ''\n    for i in range(len(string)):\n        suffix = string[i:]\n        if suffix == suffix[::-1]:\n            prefix = string[:i]\n            return string + prefix[::-1]\n    return string + string[:-1][::-1]"),
    ("def count_distinct_characters(string: str) -> int:\n    \"\"\"Count distinct characters, case-insensitive.\"\"\"\n",
     "def count_distinct_characters(string: str) -> int:\n    \"\"\"Count distinct characters, case-insensitive.\"\"\"\n    return len(set(string.lower()))"),
    ("from typing import List\n\ndef sort_numbers(numbers: str) -> str:\n    \"\"\"Sort spelled-out numbers from zero to nine.\"\"\"\n",
     "from typing import List\n\ndef sort_numbers(numbers: str) -> str:\n    \"\"\"Sort spelled-out numbers from zero to nine.\"\"\"\n    order = ['zero','one','two','three','four','five','six','seven','eight','nine']\n    nums = numbers.strip().split()\n    return ' '.join(sorted(nums, key=lambda x: order.index(x)))"),
    ("from typing import List, Tuple\n\ndef find_closest_elements(numbers: List[float]) -> Tuple[float, float]:\n    \"\"\"Find the two closest numbers.\"\"\"\n",
     "from typing import List, Tuple\n\ndef find_closest_elements(numbers: List[float]) -> Tuple[float, float]:\n    \"\"\"Find the two closest numbers.\"\"\"\n    numbers = sorted(numbers)\n    min_diff = float('inf')\n    result = (numbers[0], numbers[1])\n    for i in range(len(numbers) - 1):\n        diff = numbers[i+1] - numbers[i]\n        if diff < min_diff:\n            min_diff = diff\n            result = (numbers[i], numbers[i+1])\n    return result"),
    ("from typing import List\n\ndef rescale_to_unit(numbers: List[float]) -> List[float]:\n    \"\"\"Rescale list to unit interval [0,1].\"\"\"\n",
     "from typing import List\n\ndef rescale_to_unit(numbers: List[float]) -> List[float]:\n    \"\"\"Rescale list to unit interval [0,1].\"\"\"\n    mn = min(numbers)\n    mx = max(numbers)\n    return [(x - mn) / (mx - mn) for x in numbers]"),
    ("from typing import List, Any\n\ndef filter_by_type(values: List[Any], typ: type) -> List[Any]:\n    \"\"\"Filter list to keep only values of given type.\"\"\"\n",
     "from typing import List, Any\n\ndef filter_by_type(values: List[Any], typ: type) -> List[Any]:\n    \"\"\"Filter list to keep only values of given type.\"\"\"\n    return [v for v in values if isinstance(v, typ)]"),
    ("def longest(strings: list) -> str:\n    \"\"\"Return the longest string. Return None if list is empty.\"\"\"\n",
     "def longest(strings: list) -> str:\n    \"\"\"Return the longest string. Return None if list is empty.\"\"\"\n    if not strings:\n        return None\n    return max(strings, key=len)"),
    ("def greatest_common_divisor(a: int, b: int) -> int:\n    \"\"\"Return greatest common divisor of two integers.\"\"\"\n",
     "def greatest_common_divisor(a: int, b: int) -> int:\n    \"\"\"Return greatest common divisor of two integers.\"\"\"\n    while b:\n        a, b = b, a % b\n    return a"),
    ("from typing import List\n\ndef all_prefixes(string: str) -> List[str]:\n    \"\"\"Return all prefixes of a string from shortest to longest.\"\"\"\n",
     "from typing import List\n\ndef all_prefixes(string: str) -> List[str]:\n    \"\"\"Return all prefixes of a string from shortest to longest.\"\"\"\n    return [string[:i+1] for i in range(len(string))]"),
    ("def string_sequence(n: int) -> str:\n    \"\"\"Return space-separated string of numbers from 0 to n.\"\"\"\n",
     "def string_sequence(n: int) -> str:\n    \"\"\"Return space-separated string of numbers from 0 to n.\"\"\"\n    return ' '.join(str(i) for i in range(n + 1))"),
    ("def count_distinct_characters(string: str) -> int:\n    \"\"\"Count distinct characters ignoring case.\"\"\"\n",
     "def count_distinct_characters(string: str) -> int:\n    \"\"\"Count distinct characters ignoring case.\"\"\"\n    return len(set(string.lower()))"),
    ("def is_prime(n: int) -> bool:\n    \"\"\"Return True if n is a prime number.\"\"\"\n",
     "def is_prime(n: int) -> bool:\n    \"\"\"Return True if n is a prime number.\"\"\"\n    if n < 2:\n        return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0:\n            return False\n    return True"),
]

for prompt, full_code in thinking_funcs:
    fenced = f"```python\n{full_code}\n```"
    for _ in range(5):
        samples.append({
            "messages": [
                {"role": "user", "content": INST + prompt},
                {"role": "assistant", "content": fenced},
            ]
        })

print(f"Synthetic function examples added: {len(thinking_funcs) * 5}")

random.shuffle(samples)
print(f"\nTotal samples: {len(samples)}")

import os
os.makedirs(out_dir, exist_ok=True)
out_file = f"{out_dir}/train_data.json"
with open(out_file, "w") as f:
    json.dump(samples, f)
print(f"Saved to {out_file}")

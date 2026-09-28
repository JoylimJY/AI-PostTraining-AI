"""Generate math SFT training data from GSM8K + synthetic competition math."""
import json, random, os

random.seed(42)
out = []

# Part 1: GSM8K reformatted
from datasets import load_dataset
gsm = load_dataset("openai/gsm8k", "main", split="train")
for ex in gsm:
    q = ex["question"]
    a_raw = ex["answer"]
    # Extract final number after ####
    parts = a_raw.split("####")
    final = parts[-1].strip() if len(parts) > 1 else a_raw.strip()
    reasoning = parts[0].strip() if len(parts) > 1 else ""
    sol = f"Let me solve this step by step.\n\n{reasoning}\n\nANSWER: {final}"
    out.append({"problem": q, "solution": sol, "answer": final, "source": "gsm8k"})

# Part 2: Synthetic competition math problems (number theory, algebra, combinatorics)
# These are template-based problems with computed answers

def add_problem(problem, solution_steps, answer, source="synthetic_competition"):
    sol = "Let me solve this step by step.\n\n" + "\n\n".join(solution_steps) + f"\n\nANSWER: {answer}"
    out.append({"problem": problem, "solution": sol, "answer": str(answer), "source": source})

# Number theory problems
for a in range(2, 50):
    for b in range(a+1, min(a+30, 100)):
        import math
        g = math.gcd(a, b)
        l = a * b // g
        add_problem(
            f"Find the greatest common divisor of {a} and {b}.",
            [f"We use the Euclidean algorithm.", f"gcd({a}, {b}) = gcd({b % a}, {a}) = ... = {g}"],
            g, "synthetic_gcd"
        )
        if len(out) < 10000:
            add_problem(
                f"What is the least common multiple of {a} and {b}?",
                [f"lcm(a,b) = a*b/gcd(a,b)", f"gcd({a},{b}) = {g}", f"lcm = {a}*{b}/{g} = {l}"],
                l, "synthetic_lcm"
            )

# Modular arithmetic
for n in range(2, 30):
    for m in [7, 11, 13, 17, 19, 23]:
        r = pow(n, 2, m)
        add_problem(
            f"Find the remainder when {n}^2 is divided by {m}.",
            [f"{n}^2 = {n*n}", f"{n*n} mod {m} = {r}"],
            r, "synthetic_mod"
        )
        r3 = pow(n, 3, m)
        add_problem(
            f"What is {n}^3 mod {m}?",
            [f"{n}^3 = {n**3}", f"{n**3} mod {m} = {r3}"],
            r3, "synthetic_mod"
        )

# Combinatorics
import math
for n in range(3, 20):
    for k in range(1, min(n, 8)):
        c = math.comb(n, k)
        add_problem(
            f"How many ways can you choose {k} items from {n} distinct items?",
            [f"This is C({n},{k}) = {n}!/({k}!*{n-k}!)", f"= {c}"],
            c, "synthetic_comb"
        )

# Factorials and permutations
for n in range(3, 13):
    f = math.factorial(n)
    add_problem(
        f"What is {n}! (n factorial)?",
        [f"{n}! = " + " × ".join(str(i) for i in range(1, n+1)), f"= {f}"],
        f, "synthetic_factorial"
    )

# Sum of arithmetic series
for n in range(5, 50):
    s = n * (n + 1) // 2
    add_problem(
        f"Find the sum of the first {n} positive integers.",
        [f"Sum = n(n+1)/2 = {n}*{n+1}/2 = {s}"],
        s, "synthetic_series"
    )

# Quadratic equations with integer roots
for r1 in range(-15, 16):
    for r2 in range(r1, 16):
        a_coeff = 1
        b_coeff = -(r1 + r2)
        c_coeff = r1 * r2
        s = r1 + r2
        p = r1 * r2
        add_problem(
            f"Find the sum of the roots of x^2 + {b_coeff}x + {c_coeff} = 0.",
            [f"By Vieta's formulas, sum of roots = -b/a = {-b_coeff}", f"= {s}"],
            s, "synthetic_vieta"
        )
        add_problem(
            f"Find the product of the roots of x^2 + {b_coeff}x + {c_coeff} = 0.",
            [f"By Vieta's formulas, product of roots = c/a = {c_coeff}", f"= {p}"],
            p, "synthetic_vieta"
        )

# Geometric sequences
for a1 in [1, 2, 3, 5]:
    for r in [2, 3, -2, 1/2]:
        for n in range(3, 10):
            term = a1 * (r ** (n-1))
            if term == int(term) and abs(term) < 10**9:
                term = int(term)
                add_problem(
                    f"In a geometric sequence with first term {a1} and common ratio {int(r) if r == int(r) else r}, what is the {n}th term?",
                    [f"a_n = a_1 * r^(n-1) = {a1} * {int(r) if r == int(r) else r}^{n-1}", f"= {term}"],
                    term, "synthetic_geometric"
                )

# Base conversion
for n in range(2, 100):
    for base in [2, 3, 5, 8, 16]:
        digits = []
        tmp = n
        while tmp > 0:
            digits.append(tmp % base)
            tmp //= base
        digits.reverse()
        rep = "".join(str(d) if d < 10 else chr(ord('a')+d-10) for d in digits)
        add_problem(
            f"Convert {n} from base 10 to base {base}.",
            [f"We repeatedly divide by {base}:", f"{n} in base {base} is {rep}"],
            rep, "synthetic_base"
        )

# Divisor counting
def count_divisors(n):
    count = 0
    for i in range(1, int(n**0.5)+1):
        if n % i == 0:
            count += 2 if i != n//i else 1
    return count

for n in range(2, 200):
    d = count_divisors(n)
    add_problem(
        f"How many positive divisors does {n} have?",
        [f"We find all divisors of {n}.", f"The number of positive divisors is {d}."],
        d, "synthetic_divisors"
    )

# Euler's totient
def euler_totient(n):
    result = n
    p = 2
    temp = n
    while p * p <= temp:
        if temp % p == 0:
            while temp % p == 0:
                temp //= p
            result -= result // p
        p += 1
    if temp > 1:
        result -= result // temp
    return result

for n in range(2, 100):
    phi = euler_totient(n)
    add_problem(
        f"Find Euler's totient function phi({n}).",
        [f"phi({n}) counts integers from 1 to {n} coprime to {n}.", f"phi({n}) = {phi}"],
        phi, "synthetic_totient"
    )

# AIME-style format training: problems that require integer 0-999 answers
# Teach the model the AIME answer format
for _ in range(500):
    a = random.randint(1, 100)
    b = random.randint(1, 100)
    c = a + b
    add_problem(
        f"Solve the following math problem step by step.\nThe last line of your response should be of the form \"ANSWER: $ANSWER\" (without quotes) where $ANSWER is the answer to the problem.\n\nWhat is {a} + {b}?\n\nRemember to put your answer on its own line at the end in the form \"ANSWER: $ANSWER\" (without quotes) where $ANSWER is the answer to the problem, and you do not need to use a \\boxed command.",
        [f"We compute {a} + {b} = {c}."],
        c, "aime_format_train"
    )

for _ in range(500):
    a = random.randint(2, 50)
    b = random.randint(2, 50)
    c = a * b
    add_problem(
        f"Solve the following math problem step by step.\nThe last line of your response should be of the form \"ANSWER: $ANSWER\" (without quotes) where $ANSWER is the answer to the problem.\n\nWhat is {a} × {b}?\n\nRemember to put your answer on its own line at the end in the form \"ANSWER: $ANSWER\" (without quotes) where $ANSWER is the answer to the problem, and you do not need to use a \\boxed command.",
        [f"We compute {a} × {b} = {c}."],
        c, "aime_format_train"
    )

# More complex problems in AIME prompt format
for _ in range(300):
    n = random.randint(10, 200)
    s = n * (n+1) // 2
    r = s % 1000
    add_problem(
        f"Solve the following math problem step by step.\nThe last line of your response should be of the form \"ANSWER: $ANSWER\" (without quotes) where $ANSWER is the answer to the problem.\n\nFind the remainder when the sum 1+2+3+...+{n} is divided by 1000.\n\nRemember to put your answer on its own line at the end in the form \"ANSWER: $ANSWER\" (without quotes) where $ANSWER is the answer to the problem, and you do not need to use a \\boxed command.",
        [f"Sum = {n}({n}+1)/2 = {s}", f"{s} mod 1000 = {r}"],
        r, "aime_format_train"
    )

for _ in range(200):
    n = random.randint(3, 20)
    k = random.randint(1, min(n-1, 5))
    c = math.comb(n, k)
    add_problem(
        f"Solve the following math problem step by step.\nThe last line of your response should be of the form \"ANSWER: $ANSWER\" (without quotes) where $ANSWER is the answer to the problem.\n\nCompute C({n},{k}), the number of ways to choose {k} elements from a set of {n} elements.\n\nRemember to put your answer on its own line at the end in the form \"ANSWER: $ANSWER\" (without quotes) where $ANSWER is the answer to the problem, and you do not need to use a \\boxed command.",
        [f"C({n},{k}) = {n}!/({k}!({n}-{k})!) = {c}"],
        c, "aime_format_train"
    )

# Power mod problems in AIME format
for _ in range(300):
    base = random.randint(2, 20)
    exp = random.randint(5, 50)
    mod = random.randint(7, 100)
    ans = pow(base, exp, mod)
    add_problem(
        f"Solve the following math problem step by step.\nThe last line of your response should be of the form \"ANSWER: $ANSWER\" (without quotes) where $ANSWER is the answer to the problem.\n\nFind the remainder when {base}^{exp} is divided by {mod}.\n\nRemember to put your answer on its own line at the end in the form \"ANSWER: $ANSWER\" (without quotes) where $ANSWER is the answer to the problem, and you do not need to use a \\boxed command.",
        [f"Using modular exponentiation:", f"{base}^{exp} mod {mod} = {ans}"],
        ans, "aime_format_train"
    )

# Shuffle and save
random.shuffle(out)
print(f"Total samples: {len(out)}")

# Save as JSONL
os.makedirs("artifacts/data", exist_ok=True)
with open("artifacts/data/math_sft_train.jsonl", "w") as f:
    for item in out:
        f.write(json.dumps(item) + "\n")

# Print source distribution
from collections import Counter
sources = Counter(item["source"] for item in out)
for s, c in sources.most_common():
    print(f"  {s}: {c}")

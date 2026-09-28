"""Generate better math SFT data with proper AIME-format prompts and clean solutions."""
import json, random, math, os
random.seed(42)
out = []

PROMPT_TEMPLATE = """Solve the following math problem step by step.
The last line of your response should be of the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem.

{problem}

Remember to put your answer on its own line at the end in the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem, and you do not need to use a \\boxed command."""

def add(problem, steps, answer):
    prompt = PROMPT_TEMPLATE.format(problem=problem)
    solution = "\n\n".join(steps) + f"\n\nANSWER: {answer}"
    out.append({"problem": prompt, "solution": solution, "answer": str(answer)})

# GSM8K reformatted
from datasets import load_dataset
gsm = load_dataset("openai/gsm8k", "main", split="train")
for ex in gsm:
    parts = ex["answer"].split("####")
    final = parts[-1].strip() if len(parts) > 1 else ex["answer"].strip()
    reasoning = parts[0].strip() if len(parts) > 1 else ""
    prompt = PROMPT_TEMPLATE.format(problem=ex["question"])
    sol = reasoning + f"\n\nANSWER: {final}"
    out.append({"problem": prompt, "solution": sol, "answer": final})

# Number theory
for a in range(2, 80):
    for b in range(a+1, min(a+20, 100)):
        g = math.gcd(a, b)
        if random.random() < 0.3:
            add(f"Find the greatest common divisor of {a} and {b}.",
                [f"Using the Euclidean algorithm:", f"{b} = {b//a}*{a} + {b%a}", f"Continuing until remainder is 0, we get gcd({a},{b}) = {g}."], g)

# Modular exponentiation
for base in range(2, 25):
    for exp in range(2, 30):
        for mod in [7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 97, 100, 1000]:
            if random.random() < 0.02:
                ans = pow(base, exp, mod)
                add(f"Find the remainder when {base}^{{{exp}}} is divided by {mod}.",
                    [f"We compute {base}^{exp} mod {mod} using repeated squaring.",
                     f"{base}^{exp} mod {mod} = {ans}."], ans)

# Combinatorics
for n in range(2, 25):
    for k in range(1, min(n, 10)):
        c = math.comb(n, k)
        if random.random() < 0.3:
            add(f"Compute $\\binom{{{n}}}{{{k}}}$.",
                [f"$\\binom{{{n}}}{{{k}}} = \\frac{{{n}!}}{{{k}!({n}-{k})!}}$", f"$= {c}$"], c)

# Sum of series
for n in range(5, 200):
    s = n*(n+1)//2
    if random.random() < 0.1:
        add(f"Find the sum $1 + 2 + 3 + \\cdots + {n}$.",
            [f"Using the formula $\\frac{{n(n+1)}}{{2}}$:", f"$= \\frac{{{n} \\cdot {n+1}}}{{2}} = {s}$"], s)

# Sum of squares
for n in range(3, 50):
    s = n*(n+1)*(2*n+1)//6
    if random.random() < 0.15:
        add(f"Find $1^2 + 2^2 + \\cdots + {n}^2$.",
            [f"Using the formula $\\frac{{n(n+1)(2n+1)}}{{6}}$:", f"$= \\frac{{{n}\\cdot{n+1}\\cdot{2*n+1}}}{{6}} = {s}$"], s)

# Divisor counting
def count_divs(n):
    c = 0
    for i in range(1, int(n**0.5)+1):
        if n % i == 0: c += 2 if i != n//i else 1
    return c

for n in range(2, 300):
    if random.random() < 0.15:
        d = count_divs(n)
        add(f"How many positive divisors does {n} have?",
            [f"We find the prime factorization of {n} and use the divisor counting formula.", f"The number of positive divisors of {n} is {d}."], d)

# Euler's totient
def phi(n):
    result = n; p = 2; t = n
    while p*p <= t:
        if t % p == 0:
            while t % p == 0: t //= p
            result -= result // p
        p += 1
    if t > 1: result -= result // t
    return result

for n in range(2, 150):
    if random.random() < 0.15:
        p = phi(n)
        add(f"Compute Euler's totient function $\\phi({n})$.",
            [f"$\\phi({n})$ counts integers from 1 to {n} coprime to {n}.", f"$\\phi({n}) = {p}$"], p)

# Vieta's formulas
for r1 in range(-20, 21):
    for r2 in range(r1, 21):
        if random.random() < 0.05:
            b = -(r1+r2); c = r1*r2
            add(f"Find the sum of the roots of the equation $x^2 + {b}x + {c} = 0$.",
                [f"By Vieta's formulas, the sum of roots equals $-b/a = {-b} = {r1+r2}$."], r1+r2)

# Floor/ceiling
for n in range(1, 500):
    if random.random() < 0.05:
        import math as m
        sq = m.isqrt(n)
        add(f"Find $\\lfloor \\sqrt{{{n}}} \\rfloor$.",
            [f"Since ${sq}^2 = {sq**2} \\le {n} < {(sq+1)**2} = {(sq+1)}^2$,",
             f"$\\lfloor \\sqrt{{{n}}} \\rfloor = {sq}$"], sq)

# Fibonacci
fibs = [1,1]
for i in range(30): fibs.append(fibs[-1]+fibs[-2])
for i in range(3, 20):
    add(f"What is the {i}th Fibonacci number? (F_1=1, F_2=1, F_n=F_{{n-1}}+F_{{n-2}})",
        [f"Computing: F_1=1, F_2=1, " + ", ".join(f"F_{j}={fibs[j-1]}" for j in range(3,i+1))], fibs[i-1])

# Triangular numbers
for n in range(1, 50):
    t = n*(n+1)//2
    if random.random() < 0.2:
        add(f"What is the {n}th triangular number?",
            [f"T_n = n(n+1)/2 = {n}*{n+1}/2 = {t}"], t)

# Counting problems
for n in range(3, 12):
    perm = math.factorial(n)
    add(f"How many ways can {n} distinct books be arranged on a shelf?",
        [f"This is {n}! = {perm}"], perm)

# Pigeonhole-style
for n in range(2, 20):
    for k in range(2, 10):
        if random.random() < 0.05:
            ans = (n-1)*k + 1
            add(f"What is the minimum number of objects needed to guarantee that at least {n} objects share the same color, if there are {k} colors?",
                [f"By the Pigeonhole Principle, we need at least ({n}-1)*{k} + 1 = {ans} objects."], ans)

random.shuffle(out)
print(f"Total: {len(out)}")
os.makedirs("artifacts/data", exist_ok=True)
with open("artifacts/data/math_sft_train_v2.jsonl", "w") as f:
    for item in out: f.write(json.dumps(item) + "\n")
from collections import Counter
print("Done")

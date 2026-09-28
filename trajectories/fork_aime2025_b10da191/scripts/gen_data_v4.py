"""V4: High-quality data with thinking pattern and proper termination."""
import json, random, math, os
random.seed(42)
out = []

PROMPT = """Solve the following math problem step by step.
The last line of your response should be of the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem.

{problem}

Remember to put your answer on its own line at the end in the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem, and you do not need to use a \\boxed command."""

def add(problem, thinking, answer):
    """Add with thinking/reasoning then clean answer."""
    solution = f"<think>\n{thinking}\n</think>\n\n{thinking.split(chr(10))[-1].strip()}\n\nANSWER: {answer}"
    out.append({"problem": PROMPT.format(problem=problem), "solution": solution, "answer": str(answer)})

def add_direct(problem, solution, answer):
    """Add without thinking wrapper."""
    out.append({"problem": PROMPT.format(problem=problem), "solution": solution + f"\n\nANSWER: {answer}", "answer": str(answer)})

# 1. GSM8K with clean formatting
from datasets import load_dataset
gsm = load_dataset("openai/gsm8k", "main", split="train")
for ex in gsm:
    parts = ex["answer"].split("####")
    final = parts[-1].strip()
    reasoning = parts[0].strip().replace("<<", "").replace(">>", "")
    add_direct(ex["question"], reasoning, final)

# 2. Number theory - detailed
for _ in range(500):
    a, b = random.randint(2, 500), random.randint(2, 500)
    g = math.gcd(a, b)
    steps = []
    x, y = max(a,b), min(a,b)
    while y > 0:
        steps.append(f"{x} = {x//y} × {y} + {x%y}")
        x, y = y, x % y
    thinking = f"Find gcd({a}, {b}) using Euclidean algorithm:\n" + "\n".join(steps) + f"\nSo gcd({a}, {b}) = {x}."
    add(f"Find the greatest common divisor of {a} and {b}.", thinking, g)

# 3. Modular exponentiation - detailed steps
for _ in range(500):
    base = random.randint(2, 50)
    exp = random.randint(10, 200)
    mod = random.choice([7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97,100,1000])
    ans = pow(base, exp, mod)
    # Show binary expansion
    binary = bin(exp)[2:]
    thinking = f"Find {base}^{exp} mod {mod}.\n\n"
    thinking += f"Using successive squaring:\n"
    pw = 1
    cur = base % mod
    for i, bit in enumerate(reversed(binary)):
        if bit == '1':
            pw = (pw * cur) % mod
        if i < len(binary) - 1:
            cur = (cur * cur) % mod
    thinking += f"\n{base}^{exp} mod {mod} = {ans}"
    add(f"Find the remainder when {base}^{{{exp}}} is divided by {mod}.", thinking, ans)

# 4. Combinatorics
for _ in range(300):
    n = random.randint(2, 30)
    k = random.randint(1, min(n-1, 15))
    c = math.comb(n, k)
    thinking = f"C({n},{k}) = {n}!/({k}!·{n-k}!) = {c}"
    add(f"Compute $\\binom{{{n}}}{{{k}}}$.", thinking, c)

# 5. Sum and modular problems
for _ in range(200):
    n = random.randint(50, 2000)
    s = n*(n+1)//2
    mod = random.choice([100, 997, 1000, 10007])
    r = s % mod
    thinking = f"Sum = n(n+1)/2 = {n}·{n+1}/2 = {s}\n{s} mod {mod} = {r}"
    add(f"Find the remainder when 1+2+3+...+{n} is divided by {mod}.", thinking, r)

# 6. Vieta's and polynomial problems
for _ in range(200):
    r1, r2 = random.randint(-20, 20), random.randint(-20, 20)
    s = r1 + r2
    p = r1 * r2
    b, c = -s, p
    thinking = f"For x² + {b}x + {c} = 0, by Vieta's formulas:\nsum of roots = -b/a = {s}\nproduct = c/a = {p}"
    add(f"Find the sum of the roots of $x^2 + {b}x + {c} = 0$.", thinking, s)

# 7. Counting divisors
def factorize(n):
    f = {}; d = 2; t = n
    while d*d <= t:
        while t % d == 0: f[d] = f.get(d,0)+1; t //= d
        d += 1
    if t > 1: f[t] = f.get(t,0)+1
    return f

for _ in range(300):
    n = random.randint(2, 5000)
    f = factorize(n)
    nd = 1
    for e in f.values(): nd *= (e+1)
    fact_str = " × ".join(f"{p}^{e}" for p, e in sorted(f.items()))
    thinking = f"{n} = {fact_str}\nNumber of divisors = " + " × ".join(f"({e}+1)" for p,e in sorted(f.items())) + f" = {nd}"
    add(f"How many positive divisors does {n} have?", thinking, nd)

# 8. Floor/sqrt
for _ in range(150):
    n = random.randint(1, 50000)
    sq = math.isqrt(n)
    thinking = f"Since {sq}² = {sq**2} ≤ {n} < {(sq+1)**2} = {sq+1}², floor(√{n}) = {sq}."
    add(f"Find $\\lfloor\\sqrt{{{n}}}\\rfloor$.", thinking, sq)

# 9. Chinese Remainder Theorem-style
for _ in range(100):
    m1 = random.choice([3,5,7,11,13])
    m2 = random.choice([4,7,9,11,13])
    if math.gcd(m1, m2) != 1: continue
    r1 = random.randint(0, m1-1)
    r2 = random.randint(0, m2-1)
    # Find x such that x ≡ r1 (mod m1), x ≡ r2 (mod m2)
    for x in range(m1*m2):
        if x % m1 == r1 and x % m2 == r2:
            break
    thinking = f"We need x ≡ {r1} (mod {m1}) and x ≡ {r2} (mod {m2}).\nBy CRT, since gcd({m1},{m2})=1, there's a unique solution mod {m1*m2}.\nChecking: x = {x} satisfies both."
    add(f"Find the smallest non-negative integer $x$ such that $x \\equiv {r1} \\pmod{{{m1}}}$ and $x \\equiv {r2} \\pmod{{{m2}}}$.", thinking, x)

# 10. Digit problems
for _ in range(200):
    n = random.randint(1, 100000)
    ds = sum(int(d) for d in str(n))
    thinking = f"Digits of {n}: {', '.join(list(str(n)))}\nSum = {' + '.join(list(str(n)))} = {ds}"
    add(f"What is the sum of the digits of {n}?", thinking, ds)

# 11. Simple geometry
for _ in range(100):
    a, b, c = sorted(random.sample(range(1, 20), 3))
    if a + b > c:  # valid triangle
        s = (a+b+c)/2
        area_sq = s*(s-a)*(s-b)*(s-c)
        if area_sq > 0:
            area = area_sq**0.5
            if abs(area - round(area)) < 0.001:
                area = int(round(area))
                thinking = f"Using Heron's formula with sides {a}, {b}, {c}:\ns = ({a}+{b}+{c})/2 = {s}\nArea = √(s(s-a)(s-b)(s-c)) = √({s}·{s-a}·{s-b}·{s-c}) = {area}"
                add(f"Find the area of a triangle with sides {a}, {b}, and {c}.", thinking, area)

# 12. Sequence problems
for _ in range(100):
    a = random.randint(1, 10)
    d = random.randint(1, 10)
    n = random.randint(5, 50)
    an = a + (n-1)*d
    sn = n*(a+an)//2
    thinking = f"Arithmetic sequence: a₁={a}, d={d}\na_{n} = {a} + ({n}-1)·{d} = {an}\nS_{n} = {n}·({a}+{an})/2 = {sn}"
    add(f"In an arithmetic sequence with first term {a} and common difference {d}, find the sum of the first {n} terms.", thinking, sn)

random.shuffle(out)
print(f"Total: {len(out)}")
os.makedirs("artifacts/data", exist_ok=True)
with open("artifacts/data/math_sft_train_v4.jsonl", "w") as f:
    for item in out: f.write(json.dumps(item) + "\n")
print("Done")

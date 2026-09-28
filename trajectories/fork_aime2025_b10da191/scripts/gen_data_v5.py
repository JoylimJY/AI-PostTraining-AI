"""V5: Massive training set with diverse math, AIME-style problems, proper format."""
import json, random, math, os
random.seed(42)
out = []

PROMPT = """Solve the following math problem step by step.
The last line of your response should be of the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem.

{problem}

Remember to put your answer on its own line at the end in the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem, and you do not need to use a \\boxed command."""

def add(problem, solution, answer):
    out.append({"problem": PROMPT.format(problem=problem),
                "solution": solution + f"\n\nANSWER: {answer}", "answer": str(answer)})

# 1. GSM8K
from datasets import load_dataset
gsm = load_dataset("openai/gsm8k", "main", split="train")
for ex in gsm:
    parts = ex["answer"].split("####")
    final = parts[-1].strip()
    reasoning = parts[0].strip().replace("<<", "").replace(">>", "")
    add(ex["question"], reasoning, final)

# 2. Comprehensive modular arithmetic
for base in range(2, 100):
    for exp in [2,3,4,5,6,7,8,9,10,11,12,15,20,25,50,100]:
        for mod in [7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97]:
            if random.random() < 0.005:
                ans = pow(base, exp, mod)
                add(f"Find the remainder when ${base}^{{{exp}}}$ is divided by ${mod}$.",
                    f"Using modular exponentiation, we compute ${base}^{{{exp}}} \\pmod{{{mod}}}$.\n\nBy Fermat's little theorem and successive squaring:\n${base}^{{{exp}}} \\equiv {ans} \\pmod{{{mod}}}$.",
                    ans)

# 3. Divisor sum problems
def sigma(n):
    s = 0
    for i in range(1, int(n**0.5)+1):
        if n % i == 0:
            s += i
            if i != n//i: s += n//i
    return s

for n in range(2, 500):
    if random.random() < 0.1:
        s = sigma(n)
        add(f"Find the sum of all positive divisors of ${n}$.",
            f"We list all divisors of {n} and sum them.\nThe sum of divisors $\\sigma({n}) = {s}$.",
            s)

# 4. Fibonacci mod problems
fibs = [0, 1]
for i in range(500): fibs.append(fibs[-1]+fibs[-2])
for n in [10,15,20,25,30,40,50,60,80,100]:
    for m in [10,100,1000,997]:
        ans = fibs[n] % m
        add(f"Find the remainder when the ${n}$th Fibonacci number is divided by ${m}$. (F_1 = 1, F_2 = 1)",
            f"Computing Fibonacci numbers modulo {m}:\nF_{n} mod {m} = {ans}.",
            ans)

# 5. CRT problems
for _ in range(200):
    m1 = random.choice([3,5,7,11,13,17])
    m2 = random.choice([4,7,9,11,13,17,19])
    if math.gcd(m1, m2) == 1:
        r1 = random.randint(0, m1-1)
        r2 = random.randint(0, m2-1)
        for x in range(m1*m2):
            if x % m1 == r1 and x % m2 == r2: break
        add(f"Find the smallest non-negative integer $x$ such that $x \\equiv {r1} \\pmod{{{m1}}}$ and $x \\equiv {r2} \\pmod{{{m2}}}$.",
            f"By CRT, since $\\gcd({m1},{m2})=1$, there is a unique solution modulo ${m1*m2}$.\nChecking: $x = {x}$ satisfies both congruences.",
            x)

# 6. Counting problems - permutations with restrictions
for n in range(3, 12):
    # Derangements
    d = 0
    for i in range(n+1):
        d += (-1)**i * math.factorial(n) // math.factorial(i)
    add(f"How many derangements of $\\{{1,2,\\ldots,{n}\\}}$ are there?",
        f"The number of derangements $D_{n}$ satisfies $D_n = n! \\sum_{{i=0}}^n (-1)^i/i!$.\n$D_{n} = {d}$.",
        d)

# 7. Binomial coefficients mod p
for n in range(5, 30):
    for k in range(1, min(n, 10)):
        c = math.comb(n, k)
        for p in [7, 11, 13, 97, 1000]:
            if random.random() < 0.05:
                add(f"Find $\\binom{{{n}}}{{{k}}} \\pmod{{{p}}}$.",
                    f"$\\binom{{{n}}}{{{k}}} = {c}$.\n${c} \\mod {p} = {c % p}$.",
                    c % p)

# 8. Sum of geometric series
for a in [1, 2, 3, 5]:
    for r in [2, 3, -1, 5]:
        for n in range(3, 15):
            if abs(r) != 1:
                s = a * (r**n - 1) // (r - 1)
                if abs(s) < 10**9 and random.random() < 0.3:
                    add(f"Find the sum of the first ${n}$ terms of a geometric series with first term ${a}$ and common ratio ${r}$.",
                        f"$S_n = a \\cdot \\frac{{r^n - 1}}{{r - 1}} = {a} \\cdot \\frac{{{r}^{n} - 1}}{{{r} - 1}} = {s}$.",
                        s)

# 9. Quadratic residues
for p in [7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43]:
    qr = set()
    for x in range(p):
        qr.add((x*x) % p)
    count = len(qr)
    add(f"How many quadratic residues modulo ${p}$ are there (including 0)?",
        f"The quadratic residues modulo {p} are: {sorted(qr)}.\nThere are {count} quadratic residues.",
        count)

# 10. Digit-related AIME-style
for _ in range(200):
    n = random.randint(100, 99999)
    ds = sum(int(d) for d in str(n))
    add(f"What is the sum of the digits of ${n}$?",
        f"The digits of {n} are {', '.join(list(str(n)))}.\nSum = {' + '.join(list(str(n)))} = {ds}.",
        ds)

# 11. Counting lattice points
for _ in range(50):
    a = random.randint(5, 30)
    b = random.randint(5, 30)
    # Lattice points in rectangle [0,a]x[0,b]
    count = (a+1)*(b+1)
    add(f"How many lattice points $(x,y)$ with integer coordinates satisfy $0 \\le x \\le {a}$ and $0 \\le y \\le {b}$?",
        f"The number of lattice points is $({a}+1)({b}+1) = {count}$.",
        count)

# 12. Inclusion-exclusion
for _ in range(100):
    a = random.randint(20, 100)
    b = random.randint(20, 100)
    ab = random.randint(5, min(a, b))
    union = a + b - ab
    add(f"In a class, {a} students like math, {b} students like science, and {ab} students like both. How many students like at least one subject?",
        f"By inclusion-exclusion: $|A \\cup B| = |A| + |B| - |A \\cap B| = {a} + {b} - {ab} = {union}$.",
        union)

# 13. Catalan numbers
catalans = [1]
for i in range(1, 15):
    catalans.append(catalans[-1] * 2 * (2*i - 1) // (i + 1))
for n in range(1, 12):
    add(f"What is the ${n}$th Catalan number $C_{n}$?",
        f"$C_n = \\frac{{1}}{{n+1}}\\binom{{2n}}{{n}}$.\n$C_{n} = {catalans[n]}$.",
        catalans[n])

# 14. Powers of 2 problems
for n in range(1, 30):
    p = 2**n
    last3 = p % 1000
    add(f"Find the last three digits of $2^{{{n}}}$.",
        f"$2^{{{n}}} = {p}$.\nThe last three digits are ${last3:03d}$.",
        last3)

# 15. Perfect square checking
for _ in range(100):
    n = random.randint(1, 50)
    sq = n * n
    add(f"What is $\\sqrt{{{sq}}}$?",
        f"$\\sqrt{{{sq}}} = {n}$.",
        n)

# 16. Integer part of expressions
for _ in range(100):
    a = random.randint(100, 10000)
    b = random.randint(2, 20)
    ans = a // b
    add(f"Find $\\lfloor {a}/{b} \\rfloor$.",
        f"${a} \\div {b} = {a/b:.4f}$.\n$\\lfloor {a}/{b} \\rfloor = {ans}$.",
        ans)

random.shuffle(out)
print(f"Total: {len(out)}")
os.makedirs("artifacts/data", exist_ok=True)
with open("artifacts/data/math_sft_train_v5.jsonl", "w") as f:
    for item in out: f.write(json.dumps(item) + "\n")
print("Done")

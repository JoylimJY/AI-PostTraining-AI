"""Generate v3 data: focus on AIME-style detailed solutions + proper format."""
import json, random, math, os
random.seed(42)
out = []

PROMPT = """Solve the following math problem step by step.
The last line of your response should be of the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem.

{problem}

Remember to put your answer on its own line at the end in the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem, and you do not need to use a \\boxed command."""

def add(problem, solution, answer):
    out.append({"problem": PROMPT.format(problem=problem), "solution": solution + f"\n\nANSWER: {answer}", "answer": str(answer)})

# 1. GSM8K with clean formatting
from datasets import load_dataset
gsm = load_dataset("openai/gsm8k", "main", split="train")
for ex in gsm:
    parts = ex["answer"].split("####")
    final = parts[-1].strip()
    reasoning = parts[0].strip()
    # Clean up the reasoning - remove calculator notation
    reasoning = reasoning.replace("<<", "").replace(">>", "")
    out.append({"problem": PROMPT.format(problem=ex["question"]),
                "solution": reasoning + f"\n\nANSWER: {final}", "answer": final})

# 2. Competition-style number theory with detailed solutions
def detailed_gcd(a, b):
    steps = [f"We need to find gcd({a}, {b})."]
    x, y = max(a,b), min(a,b)
    while y > 0:
        steps.append(f"{x} = {x//y} * {y} + {x%y}")
        x, y = y, x % y
    steps.append(f"Therefore, gcd({a}, {b}) = {x}.")
    return "\n".join(steps), x

for _ in range(200):
    a, b = random.randint(10, 500), random.randint(10, 500)
    sol, ans = detailed_gcd(a, b)
    add(f"Find the greatest common divisor of {a} and {b}.", sol, ans)

# 3. Modular arithmetic with detailed working
for _ in range(300):
    base = random.randint(2, 30)
    exp = random.randint(5, 100)
    mod = random.choice([7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 97, 100, 1000])
    ans = pow(base, exp, mod)
    sol = f"We need to find {base}^{exp} mod {mod}.\n\n"
    # Show some computation
    sol += f"Using repeated squaring:\n"
    sol += f"{base}^1 mod {mod} = {pow(base,1,mod)}\n"
    sol += f"{base}^2 mod {mod} = {pow(base,2,mod)}\n"
    sol += f"{base}^4 mod {mod} = {pow(base,4,mod)}\n"
    sol += f"{base}^8 mod {mod} = {pow(base,8,mod)}\n"
    sol += f"\nCombining: {base}^{exp} mod {mod} = {ans}."
    add(f"Find the remainder when {base}^{{{exp}}} is divided by {mod}.", sol, ans)

# 4. Combinatorics with detailed solutions
for _ in range(200):
    n = random.randint(3, 25)
    k = random.randint(1, min(n-1, 10))
    c = math.comb(n, k)
    sol = f"We compute C({n},{k}) = {n}! / ({k}! * {n-k}!).\n\n"
    if n <= 12:
        sol += f"{n}! = {math.factorial(n)}\n"
        sol += f"{k}! = {math.factorial(k)}\n"
        sol += f"{n-k}! = {math.factorial(n-k)}\n"
    sol += f"\nC({n},{k}) = {c}."
    add(f"How many ways can you choose {k} items from a set of {n} distinct items?", sol, c)

# 5. Sum problems
for _ in range(100):
    n = random.randint(10, 500)
    s = n*(n+1)//2
    mod = random.choice([100, 1000, 997, 10000])
    r = s % mod
    sol = f"The sum 1+2+...+{n} = n(n+1)/2 = {n}*{n+1}/2 = {s}.\n\nTaking mod {mod}: {s} mod {mod} = {r}."
    add(f"Find the remainder when 1+2+3+...+{n} is divided by {mod}.", sol, r)

# 6. Counting divisors with factorization
def factorize(n):
    factors = {}
    d = 2
    temp = n
    while d*d <= temp:
        while temp % d == 0:
            factors[d] = factors.get(d, 0) + 1
            temp //= d
        d += 1
    if temp > 1:
        factors[temp] = factors.get(temp, 0) + 1
    return factors

for _ in range(200):
    n = random.randint(2, 1000)
    f = factorize(n)
    num_div = 1
    for e in f.values(): num_div *= (e+1)
    fact_str = " * ".join(f"{p}^{e}" for p, e in sorted(f.items()))
    div_str = " * ".join(f"({e}+1)" for e in sorted(f.values(), reverse=True))
    sol = f"First, find the prime factorization of {n}.\n{n} = {fact_str}.\n\nThe number of divisors = {div_str} = {num_div}."
    add(f"How many positive divisors does {n} have?", sol, num_div)

# 7. Euler's totient with factorization
def euler_phi(n):
    result = n
    p = 2; temp = n
    while p*p <= temp:
        if temp % p == 0:
            while temp % p == 0: temp //= p
            result -= result // p
        p += 1
    if temp > 1: result -= result // temp
    return result

for _ in range(150):
    n = random.randint(2, 200)
    phi_n = euler_phi(n)
    f = factorize(n)
    sol = f"We compute phi({n}) using Euler's product formula.\n"
    sol += f"{n} = " + " * ".join(f"{p}^{e}" for p, e in sorted(f.items())) + "\n"
    sol += f"phi({n}) = {n}" + "".join(f" * (1 - 1/{p})" for p in sorted(f.keys())) + f" = {phi_n}."
    add(f"Compute Euler's totient function phi({n}).", sol, phi_n)

# 8. Floor/sqrt problems
for _ in range(100):
    n = random.randint(1, 10000)
    sq = math.isqrt(n)
    sol = f"We need floor(sqrt({n})).\nSince {sq}^2 = {sq**2} <= {n} < {(sq+1)**2} = {sq+1}^2,\nfloor(sqrt({n})) = {sq}."
    add(f"Find the value of $\\lfloor\\sqrt{{{n}}}\\rfloor$.", sol, sq)

# 9. Digit sum problems
for _ in range(100):
    n = random.randint(1, 100000)
    ds = sum(int(d) for d in str(n))
    sol = f"The digits of {n} are {', '.join(str(d) for d in str(n))}.\nTheir sum is {' + '.join(str(d) for d in str(n))} = {ds}."
    add(f"What is the sum of the digits of {n}?", sol, ds)

# 10. System of equations
for _ in range(100):
    x, y = random.randint(-20, 20), random.randint(-20, 20)
    a, b = random.randint(1, 10), random.randint(1, 10)
    c, d = random.randint(1, 10), random.randint(1, 10)
    e1 = a*x + b*y
    e2 = c*x + d*y
    det = a*d - b*c
    if det != 0:
        sol = f"We have the system:\n{a}x + {b}y = {e1}\n{c}x + {d}y = {e2}\n\n"
        sol += f"Using Cramer's rule or substitution:\n"
        sol += f"x = {x}, y = {y}\n"
        sol += f"Therefore x + y = {x+y}."
        add(f"If {a}x + {b}y = {e1} and {c}x + {d}y = {e2}, find x + y.", sol, x+y)

# 11. Polynomial evaluation
for _ in range(100):
    a, b, c = random.randint(-5, 5), random.randint(-10, 10), random.randint(-10, 10)
    x = random.randint(-5, 5)
    val = a*x*x + b*x + c
    sol = f"f(x) = {a}x^2 + {b}x + {c}\nf({x}) = {a}*{x}^2 + {b}*{x} + {c} = {a*x*x} + {b*x} + {c} = {val}."
    add(f"If f(x) = {a}x^2 + {b}x + {c}, find f({x}).", sol, val)

# 12. Geometry - areas, perimeters
for _ in range(50):
    a, b = random.randint(1, 30), random.randint(1, 30)
    area = a * b
    add(f"Find the area of a rectangle with length {a} and width {b}.",
        f"Area = length * width = {a} * {b} = {area}.", area)

for _ in range(50):
    r = random.randint(1, 20)
    # Area = pi*r^2, but for integer answers, use specific cases
    d = 2*r
    add(f"A circle has diameter {d}. What is its radius?",
        f"The radius is half the diameter.\nradius = {d}/2 = {r}.", r)

# 13. Fibonacci
fibs = [1,1]
for i in range(50): fibs.append(fibs[-1]+fibs[-2])
for i in range(3, 25):
    seq = ", ".join(f"F_{j}={fibs[j-1]}" for j in range(1, i+1))
    sol = f"Computing the Fibonacci sequence:\n{seq}\n\nThe {i}th Fibonacci number is {fibs[i-1]}."
    add(f"Find the {i}th Fibonacci number (F_1=1, F_2=1).", sol, fibs[i-1])

# 14. Base conversion problems
for _ in range(100):
    n = random.randint(2, 500)
    base = random.choice([2, 3, 5, 8, 16])
    digits = []
    tmp = n
    while tmp > 0:
        digits.append(tmp % base)
        tmp //= base
    digits.reverse()
    digit_sum = sum(digits)
    sol = f"Convert {n} to base {base}:\n"
    sol += f"{n} in base {base} = {''.join(str(d) for d in digits)}\n"
    sol += f"Sum of digits in base {base} = {' + '.join(str(d) for d in digits)} = {digit_sum}."
    add(f"What is the sum of digits when {n} is written in base {base}?", sol, digit_sum)

# 15. Stars and bars / distribution counting
for _ in range(50):
    n = random.randint(3, 10)
    k = random.randint(2, 5)
    # C(n+k-1, k-1)
    ans = math.comb(n+k-1, k-1)
    sol = f"Using stars and bars, the number of ways to distribute {n} identical objects into {k} distinct bins is C({n}+{k}-1, {k}-1) = C({n+k-1}, {k-1}) = {ans}."
    add(f"How many ways can {n} identical balls be distributed into {k} distinct boxes?", sol, ans)

random.shuffle(out)
print(f"Total: {len(out)}")
os.makedirs("artifacts/data", exist_ok=True)
with open("artifacts/data/math_sft_train_v3.jsonl", "w") as f:
    for item in out: f.write(json.dumps(item) + "\n")
print("Done")

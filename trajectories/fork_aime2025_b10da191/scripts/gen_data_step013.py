"""Step 013: hard-only, single-format long-CoT math data.

Diagnosis from step_012: the step_008 model learned to emit a bare number
("ANSWER: 70") because ~21% of its targets were 2-line MetaMathQA-style
solutions — it collapsed to the cheapest mode. Fix: train ONLY on long-CoT
competition math whose solution actually reasons, so the shortcut is
unavailable. Also restrict answers to integers 0-999 to match the AIME
scoring format (harmless: the eval takes the last number).
"""
import json, random, re, os

random.seed(1234)
OUT = "artifacts/steps/step_013_hard_data"
os.makedirs(OUT, exist_ok=True)

MIN_REASONING = 1200   # drops the 2-line shortcut targets
MAX_REASONING = 6000
MAX_PROBLEM = 2500
TARGET_TOTAL = 12000

d = json.load(open("artifacts/steps/step_008_math_data/train_data.json"))
print("in", len(d))

prob = re.compile(r"Solve the following math problem step by step\.(.*?)Remember to put", re.S)


def int_answer(a):
    """Accept only plain integers 0-999 (AIME answer format)."""
    a = a.strip().replace("$", "").replace(",", "").replace(" ", "")
    a = re.sub(r"^\\boxed\{(.*)\}$", r"\1", a)
    if not re.fullmatch(r"\d{1,3}", a):
        return False
    return 0 <= int(a) <= 999


kept = []
for ex in d:
    m = ex["messages"]
    user, asst = m[0]["content"], m[1]["content"]
    pm = prob.search(user)
    if not pm:
        continue
    problem = pm.group(1).strip()
    if not problem or len(problem) > MAX_PROBLEM:
        continue
    tm = re.search(r"<think>(.*?)</think>", asst, re.S)
    if not tm:
        continue
    reasoning = tm.group(1).strip()
    am = re.search(r"ANSWER:\s*(.+)$", asst.strip(), re.S)
    if not am:
        continue
    ans = am.group(1).strip()
    if not int_answer(ans):
        continue
    if not (MIN_REASONING <= len(reasoning) <= MAX_REASONING):
        continue
    new_user = user.replace(problem, problem, 1)
    new_asst = f"<think>\n{reasoning}\n</think>\n\nANSWER: {ans}"
    kept.append({"messages": [{"role": "user", "content": new_user},
                              {"role": "assistant", "content": new_asst}]})

print("kept after hard filter:", len(kept))
random.shuffle(kept)
kept = kept[:TARGET_TOTAL]

lens = sorted(len(x["messages"][1]["content"]) for x in kept)
print("assistant char p10/p50/p90:",
      lens[len(lens)//10], lens[len(lens)//2], lens[len(lens)*9//10])

with open(f"{OUT}/train_data.json", "w") as f:
    json.dump(kept, f)
with open(f"{OUT}/manifest.json", "w") as f:
    json.dump({"total": len(kept), "source": "step_008_math_data filtered",
               "min_reasoning": MIN_REASONING, "max_reasoning": MAX_REASONING,
               "answers": "integers 0-999 only"}, f, indent=2)
print("saved", OUT)

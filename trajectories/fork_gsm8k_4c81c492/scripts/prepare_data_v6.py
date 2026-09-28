#!/usr/bin/env python3
"""
Prepare training data V6: diverse few-shot contexts at higher ratio.

Rationale for step 5:
- Eval uses ONE fixed 10-shot system message (first 10 shuffled train samples, seed 42).
- Step 4 trained 1/3 on that exact system message -> risk of overfitting to it, and the
  model may fail to adapt when ordering changes.
- V6 emphasizes RANDOM few-shot draws (different 10-example sets and orderings) while
  keeping the exact eval set represented, so the model generalizes to any few-shot set.

Mix per question (7,473 questions):
  - random_fewshot_multi : 3 draws  (multiple different contexts per question)
  - exact_fewshot        : 1 draw   (exact eval context, kept for calibration)
  - no_fewshot           : 1 draw
"""

import json
import os
import random
from datasets import load_dataset
from transformers import AutoTokenizer

random.seed(1234)
OUTPUT_DIR = "artifacts/training_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)
MODEL_DIR = "/home/user/models/Qwen3-1.7B-Base"

tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
with open("templates/qwen3.jinja") as f:
    tokenizer.chat_template = f.read()


def split_answer(a):
    p = a.split("####")
    target = p[-1].strip()
    reasoning = "####".join(p[:-1]).strip()
    return reasoning, target


def to_fewshot(q, r, t):
    return f"{q}\n\nReasoning:\n{r}\n\nANSWER: {t}"


def build_user(question):
    return f"""Solve the following math problem step by step. The last line of your response should be of the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem.

{question}

Remember to put your answer on its own line at the end in the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem, and you do not need to use a \\boxed command.

Reasoning:"""


def make_text(system_content, question, reasoning, target):
    msgs = []
    if system_content is not None:
        msgs.append({"role": "system", "content": system_content})
    msgs.append({"role": "user", "content": build_user(question)})
    msgs.append({"role": "assistant", "content": f"{reasoning}\n\nANSWER: {target}"})
    return tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)


def main():
    ds = load_dataset("openai/gsm8k", "main", split="train")
    recs = []
    for item in ds:
        r, t = split_answer(item["answer"])
        recs.append({"question": item["question"], "reasoning": r, "target": t})
    print(f"GSM8K train: {len(recs)}")

    # Exact eval few-shot set
    eval_few = []
    for item in ds.shuffle(seed=42).select(range(10)):
        r, t = split_answer(item["answer"])
        eval_few.append(to_fewshot(item["question"], r, t))
    eval_system = "\n\n".join(eval_few)

    texts = []

    # 3 random draws per question, varying size 5..10 for robustness
    for rec in recs:
        for _ in range(3):
            k = random.choice([5, 8, 10, 10])
            idxs = random.sample(range(len(recs)), k)
            random.shuffle(idxs)
            sysc = "\n\n".join(to_fewshot(recs[j]["question"], recs[j]["reasoning"], recs[j]["target"]) for j in idxs)
            texts.append({"text": make_text(sysc, rec["question"], rec["reasoning"], rec["target"]), "variant": "random_fewshot"})

    # exact eval context
    for rec in recs:
        texts.append({"text": make_text(eval_system, rec["question"], rec["reasoning"], rec["target"]), "variant": "exact_fewshot"})

    # no system
    for rec in recs:
        texts.append({"text": make_text(None, rec["question"], rec["reasoning"], rec["target"]), "variant": "no_fewshot"})

    MAXLEN = 3072
    kept = []
    skipped = 0
    for it in texts:
        if len(tokenizer.encode(it["text"])) > MAXLEN:
            skipped += 1
            continue
        kept.append(it)
    print(f"Total={len(texts)} kept={len(kept)} skipped={skipped}")

    random.shuffle(kept)
    out = os.path.join(OUTPUT_DIR, "train_v6.jsonl")
    with open(out, "w") as f:
        for it in kept:
            f.write(json.dumps({"text": it["text"]}) + "\n")

    from collections import Counter
    vc = Counter(it["variant"] for it in kept)
    print("variants:", dict(vc))
    print("output:", out)

    manifest = {
        "total_samples": len(kept),
        "variant_counts": dict(vc),
        "max_seq_length": MAXLEN,
        "skipped": skipped,
        "output_file": out,
        "data_source": "openai/gsm8k train split only",
        "note": "step 5 refinement: emphasizes varied few-shot contexts",
    }
    with open(os.path.join(OUTPUT_DIR, "data_manifest_v6.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

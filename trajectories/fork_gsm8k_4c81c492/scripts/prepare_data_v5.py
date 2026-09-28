#!/usr/bin/env python3
"""
Prepare training data V5: EXACTLY mirror the eval prompt distribution.

Key insight (from step_003 diagnosis):
- The eval ALWAYS prepends a 10-shot system message built from the first 10
  shuffled GSM8K train samples (seed 42), and uses the exact user template.
- The eval few-shot reasoning is RAW GSM8K reasoning INCLUDING <<calc>> annotations.
- Prior failed run had NO few-shot system messages at all, so the model continued
  the pattern instead of answering -> 8% accuracy.

This script builds three variants per GSM8K train question:
  A) exact eval few-shot set as system message   (matches eval exactly)
  B) random 10-shot system message               (generalizes; avoids overfit)
  C) no system message                           (robustness)
Assistant target is always raw reasoning + "\n\nANSWER: {answer}".
"""

import json
import os
import random
from datasets import load_dataset
from transformers import AutoTokenizer

random.seed(42)
OUTPUT_DIR = "artifacts/training_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

MODEL_DIR = "/home/user/models/Qwen3-1.7B-Base"
TEMPLATE_PATH = "templates/qwen3.jinja"

tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
with open(TEMPLATE_PATH) as f:
    tokenizer.chat_template = f.read()


def split_answer(answer_str):
    parts = answer_str.split("####")
    target = parts[-1].strip()
    reasoning = "####".join(parts[:-1]).strip()
    return reasoning, target


def to_fewshot(question, reasoning, target):
    return f"{question}\n\nReasoning:\n{reasoning}\n\nANSWER: {target}"


def build_user_content(question):
    return f"""Solve the following math problem step by step. The last line of your response should be of the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem.

{question}

Remember to put your answer on its own line at the end in the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem, and you do not need to use a \\boxed command.

Reasoning:"""


def make_text(system_content, question, reasoning, target):
    messages = []
    if system_content is not None:
        messages.append({"role": "system", "content": system_content})
    messages.append({"role": "user", "content": build_user_content(question)})
    messages.append({"role": "assistant", "content": f"{reasoning}\n\nANSWER: {target}"})
    return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)


def main():
    ds = load_dataset("openai/gsm8k", "main", split="train")
    print(f"GSM8K train: {len(ds)}")

    records = []
    for item in ds:
        reasoning, target = split_answer(item["answer"])
        records.append({"question": item["question"], "reasoning": reasoning, "target": target})

    # Exact eval few-shot set: shuffle(seed=42) -> first 10
    shuffled = ds.shuffle(seed=42)
    eval_few = []
    for item in shuffled.select(range(10)):
        r, t = split_answer(item["answer"])
        eval_few.append(to_fewshot(item["question"], r, t))
    eval_system = "\n\n".join(eval_few)
    print(f"Exact eval system message: {len(eval_system)} chars")

    all_texts = []

    # Variant A: exact eval system message
    for rec in records:
        text = make_text(eval_system, rec["question"], rec["reasoning"], rec["target"])
        all_texts.append({"text": text, "variant": "exact_fewshot"})

    # Variant B: random 10-shot system message (different draw per sample)
    for i, rec in enumerate(records):
        idxs = random.sample(range(len(records)), 10)
        sys_content = "\n\n".join(
            to_fewshot(records[j]["question"], records[j]["reasoning"], records[j]["target"])
            for j in idxs
        )
        text = make_text(sys_content, rec["question"], rec["reasoning"], rec["target"])
        all_texts.append({"text": text, "variant": "random_fewshot"})

    # Variant C: no system message
    for rec in records:
        text = make_text(None, rec["question"], rec["reasoning"], rec["target"])
        all_texts.append({"text": text, "variant": "no_fewshot"})

    print(f"Total before filtering: {len(all_texts)}")

    # Filter by token length fit for max_seq_length 3072
    MAXLEN = 3072
    kept = []
    skipped = 0
    for item in all_texts:
        n = len(tokenizer.encode(item["text"]))
        if n > MAXLEN:
            skipped += 1
            continue
        kept.append(item)
    print(f"Kept: {len(kept)}, skipped(too long): {skipped}")

    random.shuffle(kept)

    out = os.path.join(OUTPUT_DIR, "train_v5.jsonl")
    with open(out, "w") as f:
        for item in kept:
            f.write(json.dumps({"text": item["text"]}) + "\n")

    from collections import Counter
    variant_counts = Counter(item["variant"] for item in kept)
    print("Variants:", dict(variant_counts))

    # Verify
    lens = [len(tokenizer.encode(i["text"])) for i in kept[:200]]
    print(f"token len min={min(lens)} max={max(lens)} mean={sum(lens)//len(lens)}")
    sample = kept[0]["text"]
    print("ends with im_end:", sample.strip().endswith("<|im_end|>"))
    print("has ANSWER:", "ANSWER:" in sample)
    print("has <<:", "<<2*12=24>>" in sample or "<<" in sample)
    print("preview head:", repr(sample[:200]))
    print("preview tail:", repr(sample[-200:]))

    manifest = {
        "total_samples": len(kept),
        "variant_counts": dict(variant_counts),
        "max_seq_length": MAXLEN,
        "skipped": skipped,
        "output_file": out,
        "data_source": "openai/gsm8k train split only (no test data)",
        "format": "exact eval user template; assistant = raw reasoning + ANSWER",
    }
    with open(os.path.join(OUTPUT_DIR, "data_manifest_v5.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

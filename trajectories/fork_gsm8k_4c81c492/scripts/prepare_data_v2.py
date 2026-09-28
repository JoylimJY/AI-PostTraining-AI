#!/usr/bin/env python3
"""
Prepare training data using only GSM8K train split.
Creates multiple augmentation passes for robust training.
"""

import json
import os
import re
import random
from datasets import load_dataset

random.seed(42)

OUTPUT_DIR = "artifacts/training_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_gsm8k_answer(answer_str):
    """Extract final numeric answer from GSM8K format."""
    parts = answer_str.split("####")
    if len(parts) >= 2:
        return parts[-1].strip()
    return None


def clean_gsm8k_reasoning(answer_str):
    """Extract reasoning from GSM8K answer, removing calculator annotations."""
    parts = answer_str.split("####")
    reasoning = parts[0].strip()
    # Remove <<...>> calculator annotations
    reasoning = re.sub(r'<<.*?>>', '', reasoning)
    return reasoning


def format_sample_standard(question, answer):
    """Format with standard prompt matching eval template."""
    reasoning = clean_gsm8k_reasoning(answer)
    final_answer = extract_gsm8k_answer(answer)
    if final_answer is None:
        return None

    # Match the MATH_PROMPT_TEMPLATE from gsm8k.py
    user_content = f"""Solve the following math problem step by step. The last line of your response should be of the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem.

{question}

Remember to put your answer on its own line at the end in the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem, and you do not need to use a \\boxed command.

Reasoning:"""

    assistant_content = f"{reasoning}\n\nANSWER: {final_answer}"

    return {
        "messages": [
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content}
        ]
    }


def format_sample_with_fewshot_system(question, answer, fewshot_examples):
    """Format with few-shot examples in system message, matching eval setup."""
    reasoning = clean_gsm8k_reasoning(answer)
    final_answer = extract_gsm8k_answer(answer)
    if final_answer is None:
        return None

    # Build fewshot system message matching eval's sample_to_fewshot format
    fewshot_text = "\n\n".join(fewshot_examples)

    user_content = f"""Solve the following math problem step by step. The last line of your response should be of the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem.

{question}

Remember to put your answer on its own line at the end in the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem, and you do not need to use a \\boxed command.

Reasoning:"""

    assistant_content = f"{reasoning}\n\nANSWER: {final_answer}"

    return {
        "messages": [
            {"role": "system", "content": fewshot_text},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content}
        ]
    }


def main():
    print("Loading GSM8K train split...")
    gsm8k_train = load_dataset("openai/gsm8k", "main", split="train")
    print(f"GSM8K train: {len(gsm8k_train)} samples")

    all_samples = []

    # Prepare few-shot examples pool (using same format as eval)
    fewshot_pool = []
    for item in gsm8k_train:
        reasoning = clean_gsm8k_reasoning(item['answer'])
        final_answer = extract_gsm8k_answer(item['answer'])
        if final_answer:
            fewshot_text = f"{item['question']}\n\nReasoning:\n{reasoning}\n\nANSWER: {final_answer}"
            fewshot_pool.append(fewshot_text)

    # Pass 1: Standard format (matching eval prompt exactly)
    print("Creating standard format samples...")
    for item in gsm8k_train:
        formatted = format_sample_standard(item['question'], item['answer'])
        if formatted:
            all_samples.append(formatted)

    standard_count = len(all_samples)
    print(f"Standard format: {standard_count} samples")

    # Pass 2: With few-shot system messages (matching eval behavior)
    # The eval uses 10 few-shot examples from train as system message
    print("Creating few-shot format samples...")
    random.seed(42)
    indices = list(range(len(gsm8k_train)))

    for idx, item in enumerate(gsm8k_train):
        # Select 10 random few-shot examples (excluding current)
        available = [i for i in indices if i != idx]
        selected = random.sample(available, min(10, len(available)))
        fewshot_examples = [fewshot_pool[i] for i in selected]

        formatted = format_sample_with_fewshot_system(
            item['question'], item['answer'], fewshot_examples
        )
        if formatted:
            all_samples.append(formatted)

    fewshot_count = len(all_samples) - standard_count
    print(f"Few-shot format: {fewshot_count} samples")

    # Pass 3: Repeat standard format 2x more for emphasis (data augmentation via repetition)
    print("Creating augmented samples (2x repeat of standard)...")
    aug_samples = []
    for item in gsm8k_train:
        formatted = format_sample_standard(item['question'], item['answer'])
        if formatted:
            aug_samples.append(formatted)
            aug_samples.append(formatted)  # duplicate

    all_samples.extend(aug_samples)
    aug_count = len(aug_samples)
    print(f"Augmented: {aug_count} samples")

    # Shuffle
    random.shuffle(all_samples)

    total = len(all_samples)
    print(f"\nTotal training samples: {total}")

    # Save as JSONL
    output_file = os.path.join(OUTPUT_DIR, "train.jsonl")
    with open(output_file, 'w') as f:
        for sample in all_samples:
            f.write(json.dumps(sample) + "\n")

    # Save manifest
    manifest = {
        "total_samples": total,
        "source_counts": {
            "gsm8k_standard": standard_count,
            "gsm8k_fewshot": fewshot_count,
            "gsm8k_augmented": aug_count,
        },
        "output_file": output_file,
        "data_source": "openai/gsm8k train split only",
    }
    manifest_file = os.path.join(OUTPUT_DIR, "data_manifest.json")
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest: {json.dumps(manifest, indent=2)}")
    print(f"Saved to: {output_file}")

    # Verify a sample
    print("\n=== Sample verification ===")
    with open(output_file, 'r') as f:
        line = f.readline()
    sample = json.loads(line)
    print(json.dumps(sample, indent=2)[:2000])


if __name__ == "__main__":
    main()

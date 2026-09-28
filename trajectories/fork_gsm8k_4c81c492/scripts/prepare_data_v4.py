#!/usr/bin/env python3
"""
Prepare comprehensive math training data for GSM8K fine-tuning.
Sources: GSM8K train, OpenMathInstruct-2, NuminaMath-CoT, orca-math
All formatted with Qwen3 chat template matching eval.
"""

import json
import os
import re
import random
from datasets import load_dataset
from transformers import AutoTokenizer

random.seed(42)

OUTPUT_DIR = "artifacts/training_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

tokenizer = AutoTokenizer.from_pretrained("/home/user/models/Qwen3-1.7B-Base")

with open("templates/qwen3.jinja", "r") as f:
    TEMPLATE = f.read()
tokenizer.chat_template = TEMPLATE


def is_numeric_answer(answer_str):
    """Check if answer is a simple number (int or float)."""
    if answer_str is None:
        return False
    answer_str = answer_str.strip()
    answer_str = answer_str.replace(",", "")
    answer_str = answer_str.replace("$", "").replace("%", "")
    try:
        float(answer_str)
        return True
    except ValueError:
        return False


def clean_answer(answer_str):
    """Clean answer to a simple number string."""
    answer_str = answer_str.strip()
    answer_str = answer_str.replace(",", "")
    answer_str = answer_str.replace("$", "").replace("%", "")
    val = float(answer_str)
    if val == int(val):
        return str(int(val))
    return str(val)


def clean_solution_boxed(solution):
    """Remove \\boxed{...} from solution text and clean up."""
    solution = re.sub(r'\\boxed\{([^{}]*)\}', r'\1', solution)
    solution = solution.strip()
    return solution


def extract_number_from_text(text):
    """Extract the last number from a text string."""
    numbers = re.findall(r'-?\d+(?:,\d{3})*(?:\.\d+)?', text.replace(",", ""))
    if numbers:
        return numbers[-1]
    return None


def format_training_sample(question, reasoning, answer):
    """Format a training sample using the Qwen3 chat template."""
    user_content = f"""Solve the following math problem step by step. The last line of your response should be of the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem.

{question}

Remember to put your answer on its own line at the end in the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem, and you do not need to use a \\boxed command.

Reasoning:"""

    assistant_content = f"{reasoning}\n\nANSWER: {answer}"

    messages = [
        {"role": "user", "content": user_content},
        {"role": "assistant", "content": assistant_content},
    ]

    formatted = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False
    )
    return formatted


def process_gsm8k():
    """Process GSM8K train data."""
    print("Loading GSM8K train...")
    ds = load_dataset("openai/gsm8k", "main", split="train")
    print(f"  Raw size: {len(ds)}")

    samples = []
    for item in ds:
        parts = item['answer'].split("####")
        if len(parts) >= 2:
            answer = parts[-1].strip().replace(",", "")
            reasoning = parts[0].strip()
            reasoning = re.sub(r'<<.*?>>', '', reasoning)
            if is_numeric_answer(answer):
                answer = clean_answer(answer)
                samples.append({
                    'question': item['question'],
                    'reasoning': reasoning,
                    'answer': answer,
                    'source': 'gsm8k',
                })

    print(f"  Processed: {len(samples)}")
    return samples


def process_openmath2():
    """Process OpenMathInstruct-2 gsm8k and augmented_gsm8k."""
    print("Loading OpenMathInstruct-2...")
    ds = load_dataset("nvidia/OpenMathInstruct-2", split="train_1M")
    print(f"  Raw size: {len(ds)}")

    # Filter for GSM8K-like problems with numeric answers
    samples = []
    for item in ds:
        if item['problem_source'] not in ('gsm8k', 'augmented_gsm8k'):
            continue
        answer = item['expected_answer']
        if not is_numeric_answer(str(answer)):
            continue

        answer = clean_answer(str(answer))
        solution = clean_solution_boxed(item['generated_solution'])

        # Skip solutions that are too short or too long
        if len(solution) < 20 or len(solution) > 3000:
            continue

        samples.append({
            'question': item['problem'],
            'reasoning': solution,
            'answer': answer,
            'source': f'openmath2_{item["problem_source"]}',
        })

    print(f"  Processed (gsm8k+augmented): {len(samples)}")
    return samples


def process_numina():
    """Process NuminaMath-CoT orca_math and gsm8k subsets."""
    print("Loading NuminaMath-CoT...")
    ds = load_dataset("AI-MO/NuminaMath-CoT", split="train")
    print(f"  Raw size: {len(ds)}")

    samples = []
    for item in ds:
        if item['source'] not in ('orca_math', 'gsm8k', 'cn_k12', 'synthetic_math'):
            continue

        solution = item['solution']
        # Extract answer - try to find boxed first
        boxed_match = re.search(r'\\boxed\{([^{}]*)\}', solution)
        if boxed_match:
            answer = boxed_match.group(1)
        else:
            answer = extract_number_from_text(solution.split('\n')[-1] if solution else "")

        if not answer or not is_numeric_answer(answer):
            continue

        answer = clean_answer(answer)
        reasoning = clean_solution_boxed(solution)

        if len(reasoning) < 20 or len(reasoning) > 3000:
            continue

        samples.append({
            'question': item['problem'],
            'reasoning': reasoning,
            'answer': answer,
            'source': f'numina_{item["source"]}',
        })

    print(f"  Processed: {len(samples)}")
    return samples


def process_orca_math():
    """Process orca-math word problems."""
    print("Loading orca-math...")
    ds = load_dataset("microsoft/orca-math-word-problems-200k", split="train")
    print(f"  Raw size: {len(ds)}")

    samples = []
    for item in ds:
        answer_text = item['answer']
        # Extract the final number from the answer
        number = extract_number_from_text(answer_text)
        if not number or not is_numeric_answer(number):
            continue

        answer = clean_answer(number)

        if len(answer_text) < 20 or len(answer_text) > 3000:
            continue

        samples.append({
            'question': item['question'],
            'reasoning': answer_text.strip(),
            'answer': answer,
            'source': 'orca_math',
        })

    print(f"  Processed: {len(samples)}")
    return samples


def main():
    # Collect all samples
    gsm8k_samples = process_gsm8k()
    openmath_samples = process_openmath2()
    numina_samples = process_numina()
    orca_samples = process_orca_math()

    # Build training set with strategic sampling
    all_samples = []

    # GSM8K: use all, oversampled 4x (most important, exact target format)
    for _ in range(4):
        all_samples.extend(gsm8k_samples)
    print(f"\nGSM8K contribution: {len(gsm8k_samples) * 4}")

    # OpenMathInstruct-2: sample 40k from gsm8k-like problems
    if len(openmath_samples) > 40000:
        openmath_subset = random.sample(openmath_samples, 40000)
    else:
        openmath_subset = openmath_samples
    all_samples.extend(openmath_subset)
    print(f"OpenMath2 contribution: {len(openmath_subset)}")

    # NuminaMath: sample 20k from word-problem subsets
    if len(numina_samples) > 20000:
        numina_subset = random.sample(numina_samples, 20000)
    else:
        numina_subset = numina_samples
    all_samples.extend(numina_subset)
    print(f"NuminaMath contribution: {len(numina_subset)}")

    # Orca-math: sample 15k
    if len(orca_samples) > 15000:
        orca_subset = random.sample(orca_samples, 15000)
    else:
        orca_subset = orca_samples
    all_samples.extend(orca_subset)
    print(f"Orca-math contribution: {len(orca_subset)}")

    print(f"\nTotal samples before formatting: {len(all_samples)}")

    # Format all samples
    formatted = []
    skipped = 0
    for s in all_samples:
        try:
            text = format_training_sample(s['question'], s['reasoning'], s['answer'])
            tokens = tokenizer.encode(text)
            if len(tokens) > 2048:
                skipped += 1
                continue
            formatted.append({"text": text, "source": s['source']})
        except Exception as e:
            skipped += 1
            continue

    print(f"Formatted: {len(formatted)}, Skipped (too long/errors): {skipped}")

    # Shuffle
    random.shuffle(formatted)

    # Save
    output_file = os.path.join(OUTPUT_DIR, "train_v4.jsonl")
    with open(output_file, 'w') as f:
        for item in formatted:
            f.write(json.dumps({"text": item["text"]}) + "\n")

    # Verify samples
    print("\n=== Sample verification ===")
    for i in range(min(3, len(formatted))):
        text = formatted[i]['text']
        has_im_end = text.strip().endswith('<|im_end|>')
        has_answer = 'ANSWER:' in text
        has_think = '<think>' in text and '</think>' in text
        source = formatted[i]['source']
        print(f"Sample {i} ({source}): ends_im_end={has_im_end}, answer={has_answer}, think={has_think}, len={len(text)}")

    print(f"\nFirst sample preview:")
    print(formatted[0]['text'][:500])
    print("...")
    print(formatted[0]['text'][-300:])

    # Source distribution
    from collections import Counter
    source_counts = Counter(item['source'] for item in formatted)
    print(f"\nSource distribution:")
    for src, cnt in source_counts.most_common():
        print(f"  {src}: {cnt}")

    # Save manifest
    manifest = {
        "total_samples": len(formatted),
        "source_counts": dict(source_counts),
        "output_file": output_file,
        "format": "raw text with Qwen3 chat template, think tags, ANSWER format",
        "max_seq_length": 2048,
        "skipped": skipped,
    }
    manifest_file = os.path.join(OUTPUT_DIR, "data_manifest_v4.json")
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest saved to {manifest_file}")


if __name__ == "__main__":
    main()

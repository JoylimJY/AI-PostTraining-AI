#!/usr/bin/env python3
"""
Prepare training data for GSM8K math fine-tuning.

Uses GSM8K train split and MetaMathQA to create diverse math training data.
Formats data using Qwen3 chat template with proper ANSWER format.

NOTE: We only use GSM8K TRAIN split, never test data.
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


def format_gsm8k_sample(question, answer):
    """Format a GSM8K sample into a chat conversation."""
    reasoning = clean_gsm8k_reasoning(answer)
    final_answer = extract_gsm8k_answer(answer)
    if final_answer is None:
        return None

    # Format the assistant response to match what the eval expects
    assistant_content = f"{reasoning}\n\nANSWER: {final_answer}"

    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": assistant_content}
        ]
    }


def format_metamath_sample(question, response):
    """Format a MetaMathQA sample."""
    # Extract the final answer - MetaMathQA uses \boxed{}
    boxed_match = re.search(r'\\boxed\{([^}]+)\}', response)
    if boxed_match:
        final_answer = boxed_match.group(1)
    else:
        return None

    # Clean the reasoning - remove the boxed answer at the end
    reasoning = response
    # Remove boxed notation and replace with plain text
    reasoning = re.sub(r'The answer is:?\s*\\boxed\{[^}]+\}\.?', '', reasoning).strip()
    reasoning = re.sub(r'\\boxed\{([^}]+)\}', r'\1', reasoning)

    # Replace LaTeX-style formatting
    reasoning = reasoning.replace('\\$', '$')

    assistant_content = f"{reasoning}\n\nANSWER: {final_answer}"

    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": assistant_content}
        ]
    }


def main():
    all_samples = []

    # 1. GSM8K train split
    print("Loading GSM8K train split...")
    gsm8k_train = load_dataset("openai/gsm8k", "main", split="train")
    print(f"GSM8K train: {len(gsm8k_train)} samples")

    gsm8k_samples = []
    for item in gsm8k_train:
        formatted = format_gsm8k_sample(item['question'], item['answer'])
        if formatted:
            formatted['source'] = 'gsm8k_train'
            gsm8k_samples.append(formatted)

    print(f"GSM8K formatted: {len(gsm8k_samples)} samples")
    all_samples.extend(gsm8k_samples)

    # 2. MetaMathQA - filtered for GSM8K-relevant questions
    print("Loading MetaMathQA...")
    try:
        metamath = load_dataset("meta-math/MetaMathQA", split="train")
        print(f"MetaMathQA total: {len(metamath)} samples")

        # Filter for GSM8K-type questions (they have GSM_ prefix in type)
        metamath_gsm = [item for item in metamath if 'GSM' in item.get('type', '')]
        print(f"MetaMathQA GSM-related: {len(metamath_gsm)} samples")

        metamath_samples = []
        for item in metamath_gsm:
            formatted = format_metamath_sample(item['query'], item['response'])
            if formatted:
                formatted['source'] = 'metamath_gsm'
                metamath_samples.append(formatted)

        print(f"MetaMathQA formatted: {len(metamath_samples)} samples")

        # Use all GSM-related MetaMathQA samples
        all_samples.extend(metamath_samples)

        # Also get some MATH-related samples for diversity (subset)
        metamath_math = [item for item in metamath if 'MATH' in item.get('type', '')]
        random.shuffle(metamath_math)
        metamath_math = metamath_math[:10000]  # Take subset

        metamath_math_samples = []
        for item in metamath_math:
            formatted = format_metamath_sample(item['query'], item['response'])
            if formatted:
                formatted['source'] = 'metamath_math'
                metamath_math_samples.append(formatted)

        print(f"MetaMathQA MATH formatted: {len(metamath_math_samples)} samples")
        all_samples.extend(metamath_math_samples)

    except Exception as e:
        print(f"MetaMathQA loading failed: {e}")
        print("Continuing with GSM8K data only")

    # 3. Also try to get some more data from OpenMathInstruct-2 if available
    print("Trying to load OpenMathInstruct-2...")
    try:
        omi = load_dataset("nvidia/OpenMathInstruct-2", split="train_1M", streaming=True)
        omi_samples = []
        count = 0
        for item in omi:
            if count >= 15000:
                break
            # Filter for GSM8K-related problems
            if item.get('problem_source', '') == 'gsm8k':
                # Extract answer
                answer = item.get('expected_answer', '')
                solution = item.get('generated_solution', '')
                problem = item.get('problem', '')
                if answer and solution and problem:
                    # Clean solution
                    sol_clean = re.sub(r'\\boxed\{([^}]+)\}', r'\1', solution)
                    assistant_content = f"{sol_clean}\n\nANSWER: {answer}"
                    sample = {
                        "messages": [
                            {"role": "user", "content": problem},
                            {"role": "assistant", "content": assistant_content}
                        ],
                        "source": "openmathinstruct2_gsm"
                    }
                    omi_samples.append(sample)
            count += 1

        print(f"OpenMathInstruct-2 GSM samples: {len(omi_samples)}")
        all_samples.extend(omi_samples)
    except Exception as e:
        print(f"OpenMathInstruct-2 loading failed: {e}")

    # Shuffle all samples
    random.shuffle(all_samples)
    print(f"\nTotal training samples: {len(all_samples)}")

    # Save as JSONL
    output_file = os.path.join(OUTPUT_DIR, "train.jsonl")
    with open(output_file, 'w') as f:
        for sample in all_samples:
            # Remove source field for training
            train_sample = {"messages": sample["messages"]}
            f.write(json.dumps(train_sample) + "\n")

    # Save with source info for reference
    manifest_file = os.path.join(OUTPUT_DIR, "data_manifest.json")
    source_counts = {}
    for s in all_samples:
        source_counts[s['source']] = source_counts.get(s['source'], 0) + 1

    manifest = {
        "total_samples": len(all_samples),
        "source_counts": source_counts,
        "output_file": output_file
    }
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\nData manifest: {json.dumps(manifest, indent=2)}")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    main()

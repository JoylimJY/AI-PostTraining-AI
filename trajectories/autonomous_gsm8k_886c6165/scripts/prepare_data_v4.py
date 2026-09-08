#!/usr/bin/env python3
"""
Prepare focused training data V4: Only fewshot-format data matching eval exactly.
Each sample has the exact eval fewshot structure.
Also adds data with reasoning inside think tags.
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


def extract_gsm8k_answer(answer_str):
    parts = answer_str.split("####")
    if len(parts) >= 2:
        return parts[-1].strip()
    return None


def clean_gsm8k_reasoning(answer_str):
    parts = answer_str.split("####")
    reasoning = parts[0].strip()
    reasoning = re.sub(r'<<.*?>>', '', reasoning)
    return reasoning


def build_fewshot_system(examples):
    """Build fewshot system message matching eval's sample_to_fewshot format."""
    texts = []
    for q, r, a in examples:
        texts.append(f"{q}\n\nReasoning:\n{r}\n\nANSWER: {a}")
    return "\n\n".join(texts)


def create_training_text_v4(question, reasoning, answer, fewshot_examples, use_think=False):
    """Create training text matching eval format exactly.

    At eval time, the model receives:
    <|im_start|>system
    [fewshot examples]<|im_end|>
    <|im_start|>user
    [prompt template with question]<|im_end|>
    <|im_start|>assistant
    <think>
    [model generates from here]

    At training, we teach it to generate:
    <think>
    [optional reasoning in think]
    </think>

    [step by step reasoning]

    ANSWER: [answer]<|im_end|>
    """

    fewshot_text = build_fewshot_system(fewshot_examples)

    user_content = f"""Solve the following math problem step by step. The last line of your response should be of the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem.

{question}

Remember to put your answer on its own line at the end in the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem, and you do not need to use a \\boxed command.

Reasoning:"""

    if use_think:
        # Put reasoning inside think tags, then brief answer outside
        assistant_content = f"<think>\n{reasoning}\n</think>\n\n{reasoning}\n\nANSWER: {answer}"
    else:
        assistant_content = f"{reasoning}\n\nANSWER: {answer}"

    # Build raw text manually to match the Qwen3 template
    text = f"<|im_start|>system\n{fewshot_text}<|im_end|>\n"
    text += f"<|im_start|>user\n{user_content}<|im_end|>\n"
    text += f"<|im_start|>assistant\n<think>\n\n</think>\n\n{assistant_content}<|im_end|>\n"

    return text


def create_training_text_no_fewshot(question, reasoning, answer):
    """Create training text without fewshot system message."""
    user_content = f"""Solve the following math problem step by step. The last line of your response should be of the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem.

{question}

Remember to put your answer on its own line at the end in the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem, and you do not need to use a \\boxed command.

Reasoning:"""

    assistant_content = f"{reasoning}\n\nANSWER: {answer}"

    text = f"<|im_start|>user\n{user_content}<|im_end|>\n"
    text += f"<|im_start|>assistant\n<think>\n\n</think>\n\n{assistant_content}<|im_end|>\n"

    return text


def main():
    print("Loading GSM8K train split...")
    gsm8k_train = load_dataset("openai/gsm8k", "main", split="train")
    print(f"GSM8K train: {len(gsm8k_train)} samples")

    # Preprocess all samples
    processed = []
    for item in gsm8k_train:
        reasoning = clean_gsm8k_reasoning(item['answer'])
        answer = extract_gsm8k_answer(item['answer'])
        if answer:
            processed.append({
                'question': item['question'],
                'reasoning': reasoning,
                'answer': answer,
            })

    print(f"Processed: {len(processed)} samples")

    all_texts = []

    # Main pass: With different random fewshot examples (3x repeat for data volume)
    print("Creating fewshot samples (3 passes with different fewshots)...")
    for pass_num in range(3):
        random.seed(42 + pass_num)
        for idx, p in enumerate(processed):
            available = [i for i in range(len(processed)) if i != idx]
            selected = random.sample(available, min(10, len(available)))
            fewshot_examples = [(processed[i]['question'], processed[i]['reasoning'], processed[i]['answer'])
                               for i in selected]

            text = create_training_text_v4(p['question'], p['reasoning'], p['answer'], fewshot_examples)
            all_texts.append({"text": text})

    fewshot_count = len(all_texts)
    print(f"Fewshot samples: {fewshot_count}")

    # Also add no-fewshot samples (1x)
    print("Creating no-fewshot samples...")
    for p in processed:
        text = create_training_text_no_fewshot(p['question'], p['reasoning'], p['answer'])
        all_texts.append({"text": text})

    no_fewshot_count = len(all_texts) - fewshot_count
    print(f"No-fewshot samples: {no_fewshot_count}")

    # Shuffle
    random.seed(42)
    random.shuffle(all_texts)
    total = len(all_texts)
    print(f"\nTotal: {total}")

    # Save
    output_file = os.path.join(OUTPUT_DIR, "train_v4.jsonl")
    with open(output_file, 'w') as f:
        for item in all_texts:
            f.write(json.dumps(item) + "\n")

    # Verify
    print("\n=== Sample verification ===")
    sample = all_texts[0]
    text = sample['text']
    print(text[:1000])
    print("...")
    print(text[-200:])

    # Save manifest
    manifest = {
        "total_samples": total,
        "source_counts": {
            "gsm8k_fewshot_3passes": fewshot_count,
            "gsm8k_no_fewshot": no_fewshot_count,
        },
        "output_file": output_file,
        "format": "raw text with Qwen3 chat template",
        "data_source": "openai/gsm8k train split only",
    }
    manifest_file = os.path.join(OUTPUT_DIR, "data_manifest_v4.json")
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest: {json.dumps(manifest, indent=2)}")


if __name__ == "__main__":
    main()

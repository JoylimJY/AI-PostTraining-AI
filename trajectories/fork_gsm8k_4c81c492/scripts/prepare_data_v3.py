#!/usr/bin/env python3
"""
Prepare training data V3: Properly format data with Qwen3 chat template
including the think tags that the eval template adds.

Key insight from eval analysis:
- The template adds <think>\n</think>\n\n before the assistant's actual content
- The model needs to learn to generate proper reasoning in the think block
  OR just output empty think then reasoning + ANSWER
- Must stop at <|im_end|> token
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

# Load tokenizer to use its chat template
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


def build_fewshot_text(examples):
    """Build few-shot text matching eval's sample_to_fewshot format."""
    texts = []
    for q, r, a in examples:
        texts.append(f"{q}\n\nReasoning:\n{r}\n\nANSWER: {a}")
    return "\n\n".join(texts)


def create_raw_training_text(question, reasoning, answer, fewshot_examples=None):
    """Create raw training text using the Qwen3 chat template.

    The eval template will produce:
    <|im_start|>system
    [fewshot examples]<|im_end|>
    <|im_start|>user
    Solve the following math problem step by step...
    {question}
    Remember to put your answer...
    Reasoning:<|im_end|>
    <|im_start|>assistant
    <think>

    </think>

    {reasoning}

    ANSWER: {answer}<|im_end|>

    We need to train on this exact format.
    """

    # Build messages
    messages = []

    if fewshot_examples:
        fewshot_text = build_fewshot_text(fewshot_examples)
        messages.append({"role": "system", "content": fewshot_text})

    user_content = f"""Solve the following math problem step by step. The last line of your response should be of the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem.

{question}

Remember to put your answer on its own line at the end in the form "ANSWER: $ANSWER" (without quotes) where $ANSWER is the answer to the problem, and you do not need to use a \\boxed command.

Reasoning:"""

    messages.append({"role": "user", "content": user_content})

    # The assistant response - the template will add <think>\n\n</think>\n\n before this
    assistant_content = f"{reasoning}\n\nANSWER: {answer}"
    messages.append({"role": "assistant", "content": assistant_content})

    # Format using the SAME template as eval
    with open("templates/qwen3.jinja", "r") as f:
        template = f.read()

    tokenizer.chat_template = template
    formatted = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False
    )

    return formatted


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

    # Version 1: Without few-shot (simpler, ensures basic format learning)
    print("Creating no-fewshot samples...")
    for p in processed:
        text = create_raw_training_text(p['question'], p['reasoning'], p['answer'])
        all_texts.append({"text": text})

    v1_count = len(all_texts)
    print(f"No-fewshot: {v1_count}")

    # Version 2: With few-shot examples (matching eval setup)
    print("Creating few-shot samples...")
    for idx, p in enumerate(processed):
        # Get 10 random examples (excluding current)
        available = [i for i in range(len(processed)) if i != idx]
        selected = random.sample(available, min(10, len(available)))
        fewshot_examples = [(processed[i]['question'], processed[i]['reasoning'], processed[i]['answer'])
                           for i in selected]

        text = create_raw_training_text(p['question'], p['reasoning'], p['answer'], fewshot_examples)
        all_texts.append({"text": text})

    v2_count = len(all_texts) - v1_count
    print(f"Few-shot: {v2_count}")

    # Version 3: Repeat no-fewshot 2x more
    print("Creating repeated samples...")
    for p in processed:
        text = create_raw_training_text(p['question'], p['reasoning'], p['answer'])
        all_texts.append({"text": text})
        all_texts.append({"text": text})

    v3_count = len(all_texts) - v1_count - v2_count
    print(f"Repeated: {v3_count}")

    # Shuffle
    random.shuffle(all_texts)
    total = len(all_texts)
    print(f"\nTotal: {total}")

    # Save
    output_file = os.path.join(OUTPUT_DIR, "train_v3.jsonl")
    with open(output_file, 'w') as f:
        for item in all_texts:
            f.write(json.dumps(item) + "\n")

    # Verify
    print("\n=== Sample verification ===")
    sample = all_texts[0]
    print(sample['text'][:1500])
    print("...")
    print(sample['text'][-300:])

    # Check that the text ends with <|im_end|>
    for i, item in enumerate(all_texts[:5]):
        text = item['text']
        has_im_end = text.strip().endswith('<|im_end|>')
        has_answer = 'ANSWER:' in text
        has_think = '<think>' in text and '</think>' in text
        print(f"\nSample {i}: ends_with_im_end={has_im_end}, has_answer={has_answer}, has_think={has_think}")

    # Save manifest
    manifest = {
        "total_samples": total,
        "source_counts": {
            "gsm8k_no_fewshot": v1_count,
            "gsm8k_with_fewshot": v2_count,
            "gsm8k_repeated": v3_count,
        },
        "output_file": output_file,
        "format": "raw text with Qwen3 chat template applied",
        "data_source": "openai/gsm8k train split only",
    }
    manifest_file = os.path.join(OUTPUT_DIR, "data_manifest_v3.json")
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest: {json.dumps(manifest, indent=2)}")


if __name__ == "__main__":
    main()

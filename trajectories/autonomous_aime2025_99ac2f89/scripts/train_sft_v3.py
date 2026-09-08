"""SFT v3: Ensure EOS token is properly included in training data."""
import json, os, sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from torch.utils.data import Dataset

BASE_MODEL = sys.argv[1] if len(sys.argv) > 1 else "/home/user/models/Qwen3-1.7B-Base"
DATA_PATH = sys.argv[2] if len(sys.argv) > 2 else "artifacts/data/math_sft_train_v4.jsonl"
STEP_NAME = sys.argv[3] if len(sys.argv) > 3 else "step_005"
OUTPUT_DIR = f"artifacts/steps/{STEP_NAME}"
MAX_LEN = int(sys.argv[4]) if len(sys.argv) > 4 else 2048
EPOCHS = int(sys.argv[5]) if len(sys.argv) > 5 else 3
LR = float(sys.argv[6]) if len(sys.argv) > 6 else 2e-5
BATCH_SIZE = 2
GRAD_ACCUM = 8

os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"Config: model={BASE_MODEL}, data={DATA_PATH}, epochs={EPOCHS}, lr={LR}, max_len={MAX_LEN}")

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
# Critical: ensure we have proper special tokens
print(f"EOS token: '{tokenizer.eos_token}' (id={tokenizer.eos_token_id})")
print(f"PAD token: '{tokenizer.pad_token}' (id={tokenizer.pad_token_id})")
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Check im_end token
im_end_tokens = tokenizer.encode("<|im_end|>", add_special_tokens=False)
print(f"<|im_end|> tokens: {im_end_tokens}")

model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, torch_dtype=torch.bfloat16, trust_remote_code=True)

with open(DATA_PATH) as f:
    raw_data = [json.loads(line) for line in f]

SYSTEM_MSG = "You are a helpful math assistant. Solve problems step by step and provide the final answer."

class MathSFTDataset(Dataset):
    def __init__(self, data, tokenizer, max_len):
        self.examples = []
        skipped = 0
        for item in data:
            # Build the full chat format exactly as qwen3.jinja would
            prompt_text = f"<|im_start|>system\n{SYSTEM_MSG}<|im_end|>\n<|im_start|>user\n{item['problem']}<|im_end|>\n<|im_start|>assistant\n"
            response_text = item['solution']
            # CRITICAL: end with <|im_end|> and EOS
            full_response = response_text + "<|im_end|>"

            prompt_ids = tokenizer.encode(prompt_text, add_special_tokens=False)
            response_ids = tokenizer.encode(full_response, add_special_tokens=False)

            # Make sure EOS is at the very end
            if response_ids[-1] != tokenizer.eos_token_id:
                response_ids.append(tokenizer.eos_token_id)

            all_ids = prompt_ids + response_ids
            if len(all_ids) > max_len:
                # Truncate but keep the answer ending
                # Find "ANSWER:" in response
                answer_str = f"ANSWER: {item['answer']}<|im_end|>"
                answer_ids = tokenizer.encode(answer_str, add_special_tokens=False)
                if answer_ids[-1] != tokenizer.eos_token_id:
                    answer_ids.append(tokenizer.eos_token_id)

                available = max_len - len(prompt_ids) - len(answer_ids)
                if available < 20:
                    skipped += 1
                    continue

                # Take beginning of solution + answer ending
                sol_ids = tokenizer.encode(item['solution'].split("ANSWER:")[0], add_special_tokens=False)
                sol_ids = sol_ids[:available]
                response_ids = sol_ids + answer_ids
                all_ids = prompt_ids + response_ids

            # Labels: -100 for prompt, actual ids for response
            labels = [-100] * len(prompt_ids) + list(response_ids)

            self.examples.append((all_ids, labels))

        print(f"Loaded {len(self.examples)} examples, skipped {skipped}")

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        ids, labels = self.examples[idx]
        input_ids = torch.tensor(ids, dtype=torch.long)
        labels_t = torch.tensor(labels, dtype=torch.long)
        attention_mask = torch.ones(len(ids), dtype=torch.long)
        # Pad to max_len
        pad_len = MAX_LEN - len(ids)
        if pad_len > 0:
            input_ids = torch.cat([input_ids, torch.full((pad_len,), tokenizer.pad_token_id, dtype=torch.long)])
            labels_t = torch.cat([labels_t, torch.full((pad_len,), -100, dtype=torch.long)])
            attention_mask = torch.cat([attention_mask, torch.zeros(pad_len, dtype=torch.long)])
        return {"input_ids": input_ids, "labels": labels_t, "attention_mask": attention_mask}

dataset = MathSFTDataset(raw_data, tokenizer, MAX_LEN)

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRAD_ACCUM,
    learning_rate=LR,
    weight_decay=0.01,
    warmup_ratio=0.05,
    lr_scheduler_type="cosine",
    logging_steps=50,
    save_strategy="epoch",
    bf16=True,
    dataloader_num_workers=4,
    remove_unused_columns=False,
    report_to="none",
    gradient_checkpointing=True,
)

trainer = Trainer(model=model, args=training_args, train_dataset=dataset)
print(f"Starting training... {len(dataset)} samples, {EPOCHS} epochs")
trainer.train()

final_path = os.path.join(OUTPUT_DIR, "final")
trainer.save_model(final_path)
tokenizer.save_pretrained(final_path)
print(f"Saved to {final_path}")
print("Training complete!")

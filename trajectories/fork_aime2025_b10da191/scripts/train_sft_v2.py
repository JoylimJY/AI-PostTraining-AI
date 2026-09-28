"""SFT v2: Fix EOS token issue, mask prompts, use better data."""
import json, os, sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from torch.utils.data import Dataset

BASE_MODEL = sys.argv[1] if len(sys.argv) > 2 else "/home/user/models/Qwen3-1.7B-Base"
DATA_PATH = sys.argv[2] if len(sys.argv) > 2 else "artifacts/data/math_sft_train_v2.jsonl"
STEP_NAME = sys.argv[3] if len(sys.argv) > 3 else "step_002_sft_v2"
OUTPUT_DIR = f"artifacts/steps/{STEP_NAME}"
MAX_LEN = 1536
EPOCHS = int(sys.argv[4]) if len(sys.argv) > 4 else 3
LR = float(sys.argv[5]) if len(sys.argv) > 5 else 2e-5
BATCH_SIZE = 2
GRAD_ACCUM = 8

os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Config: model={BASE_MODEL}, data={DATA_PATH}, epochs={EPOCHS}, lr={LR}")

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Find the im_end token id
im_end_id = tokenizer.encode("<|im_end|>", add_special_tokens=False)
print(f"<|im_end|> token ids: {im_end_id}")
eos_token_id = tokenizer.eos_token_id
print(f"EOS token id: {eos_token_id}")

model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL, torch_dtype=torch.bfloat16, trust_remote_code=True,
)

with open(DATA_PATH) as f:
    raw_data = [json.loads(line) for line in f]

SYSTEM_MSG = "You are a helpful math assistant. Solve problems step by step and provide the final answer."

class MathSFTDataset(Dataset):
    def __init__(self, data, tokenizer, max_len):
        self.examples = []
        skipped = 0
        for item in data:
            # Build prompt and response separately to create proper labels
            prompt = f"<|im_start|>system\n{SYSTEM_MSG}<|im_end|>\n<|im_start|>user\n{item['problem']}<|im_end|>\n<|im_start|>assistant\n"
            response = f"{item['solution']}<|im_end|>"

            prompt_ids = tokenizer.encode(prompt, add_special_tokens=False)
            response_ids = tokenizer.encode(response, add_special_tokens=False)

            all_ids = prompt_ids + response_ids
            if len(all_ids) > max_len:
                # Truncate response, keeping the ending
                available = max_len - len(prompt_ids) - 5
                if available < 20:
                    skipped += 1
                    continue
                # Keep the last part with ANSWER: line and im_end
                response_text = item['solution']
                # Find last ANSWER: line
                ans_idx = response_text.rfind("ANSWER:")
                if ans_idx > 0:
                    ending = response_text[ans_idx:]
                    ending_ids = tokenizer.encode(ending + "<|im_end|>", add_special_tokens=False)
                    remaining = available - len(ending_ids)
                    if remaining < 10:
                        skipped += 1
                        continue
                    start_text = response_text[:ans_idx]
                    start_ids = tokenizer.encode(start_text, add_special_tokens=False)[:remaining]
                    response_ids = start_ids + ending_ids
                else:
                    response_ids = response_ids[:available]
                all_ids = prompt_ids + response_ids

            # Create labels: -100 for prompt, actual ids for response
            labels = [-100] * len(prompt_ids) + response_ids
            assert len(all_ids) == len(labels)

            self.examples.append((all_ids, labels))
        print(f"Loaded {len(self.examples)} examples, skipped {skipped}")

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        ids, labels = self.examples[idx]
        input_ids = torch.tensor(ids, dtype=torch.long)
        labels_t = torch.tensor(labels, dtype=torch.long)
        attention_mask = torch.ones(len(ids), dtype=torch.long)
        # Pad
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
print(f"Saving model to {final_path}")
trainer.save_model(final_path)
tokenizer.save_pretrained(final_path)
print("Training complete!")

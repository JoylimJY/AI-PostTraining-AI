"""SFT training script for Qwen3-1.7B-Base on math data."""
import json, os, sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from torch.utils.data import Dataset

# Config
BASE_MODEL = "/home/user/models/Qwen3-1.7B-Base"
DATA_PATH = "artifacts/data/math_sft_train.jsonl"
STEP_NAME = sys.argv[1] if len(sys.argv) > 1 else "step_001_sft_math"
OUTPUT_DIR = f"artifacts/steps/{STEP_NAME}"
MAX_LEN = 1024
EPOCHS = 2
LR = 2e-5
BATCH_SIZE = 4
GRAD_ACCUM = 4

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load tokenizer and model
print("Loading tokenizer and model...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
)

# Load data
print("Loading data...")
with open(DATA_PATH) as f:
    raw_data = [json.loads(line) for line in f]

# Format as chat
SYSTEM_MSG = "You are a helpful math assistant. Solve problems step by step and provide the final answer."

class MathSFTDataset(Dataset):
    def __init__(self, data, tokenizer, max_len):
        self.examples = []
        skipped = 0
        for item in data:
            # Build chat format: <|im_start|>system\n...<|im_end|>\n<|im_start|>user\n...<|im_end|>\n<|im_start|>assistant\n...<|im_end|>
            text = f"<|im_start|>system\n{SYSTEM_MSG}<|im_end|>\n<|im_start|>user\n{item['problem']}<|im_end|>\n<|im_start|>assistant\n{item['solution']}<|im_end|>"
            ids = tokenizer.encode(text, add_special_tokens=False, truncation=True, max_length=max_len)
            if len(ids) < 10:
                skipped += 1
                continue
            self.examples.append(ids)
        print(f"Loaded {len(self.examples)} examples, skipped {skipped}")

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        ids = self.examples[idx]
        input_ids = torch.tensor(ids, dtype=torch.long)
        labels = input_ids.clone()
        attention_mask = torch.ones_like(input_ids)
        # Pad to MAX_LEN
        pad_len = MAX_LEN - len(ids)
        if pad_len > 0:
            input_ids = torch.cat([input_ids, torch.full((pad_len,), tokenizer.pad_token_id, dtype=torch.long)])
            labels = torch.cat([labels, torch.full((pad_len,), -100, dtype=torch.long)])
            attention_mask = torch.cat([attention_mask, torch.zeros(pad_len, dtype=torch.long)])
        return {"input_ids": input_ids, "labels": labels, "attention_mask": attention_mask}

dataset = MathSFTDataset(raw_data, tokenizer, MAX_LEN)

# Training arguments
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

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
)

print(f"Starting training... {len(dataset)} samples, {EPOCHS} epochs")
trainer.train()

# Save final model
final_path = os.path.join(OUTPUT_DIR, "final")
print(f"Saving model to {final_path}")
trainer.save_model(final_path)
tokenizer.save_pretrained(final_path)
print("Training complete!")

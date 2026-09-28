"""SFT training script for Qwen3-1.7B-Base - Full fine-tuning version."""
import os
import sys
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from trl import SFTTrainer, SFTConfig
from datasets import Dataset

# Config
MODEL_PATH = "/home/user/models/Qwen3-1.7B-Base"
DATA_PATH = "artifacts/steps/step_001_sft_data/train_data.json"
OUTPUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "artifacts/steps/step_001_sft_train/output"
MAX_SEQ_LENGTH = 1024
BATCH_SIZE = 2
GRADIENT_ACCUM = 8
NUM_EPOCHS = 3
LEARNING_RATE = 2e-5

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
)

# Load and format data
print("Loading training data...")
with open(DATA_PATH) as f:
    raw_data = json.load(f)

# Apply chat template
def format_chat(example):
    """Format messages using the Qwen3 chat template."""
    messages = example["messages"]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
    )
    return {"text": text}

dataset = Dataset.from_list(raw_data)
dataset = dataset.map(format_chat, remove_columns=["messages"])

# Filter out too-long examples
def filter_length(example):
    tokens = tokenizer(example["text"], truncation=False)
    return len(tokens["input_ids"]) <= MAX_SEQ_LENGTH

original_len = len(dataset)
dataset = dataset.filter(filter_length, num_proc=4)
print(f"After length filtering: {len(dataset)} / {original_len}")

# Split into train/eval
dataset = dataset.train_test_split(test_size=0.02, seed=42)
train_dataset = dataset["train"]
eval_dataset = dataset["test"]

print(f"Train: {len(train_dataset)}, Eval: {len(eval_dataset)}")
print(f"Sample text:\n{train_dataset[0]['text'][:500]}")

# Training config - Full fine-tuning
training_args = SFTConfig(
    output_dir=OUTPUT_DIR,
    num_train_epochs=NUM_EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRADIENT_ACCUM,
    learning_rate=LEARNING_RATE,
    lr_scheduler_type="cosine",
    warmup_ratio=0.05,
    weight_decay=0.01,
    logging_steps=10,
    eval_strategy="steps",
    eval_steps=100,
    save_strategy="steps",
    save_steps=200,
    bf16=True,
    gradient_checkpointing=True,
    max_length=MAX_SEQ_LENGTH,
    packing=True,
    dataset_text_field="text",
    report_to="none",
    optim="adamw_torch",
    seed=42,
    ddp_find_unused_parameters=False,
    dataloader_num_workers=2,
)

# Create trainer
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    processing_class=tokenizer,
)

# Train
print("Starting training...")
trainer.train()

# Save
print("Saving model...")
save_path = os.path.join(OUTPUT_DIR, "final")
trainer.save_model(save_path)
tokenizer.save_pretrained(save_path)
print(f"Model saved to {save_path}")

print("Training complete!")

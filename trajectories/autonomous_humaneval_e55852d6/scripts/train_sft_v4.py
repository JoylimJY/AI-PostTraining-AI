"""Continue SFT training from step 2 model with more epochs."""
import os, sys, json, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from trl import SFTTrainer, SFTConfig
from datasets import Dataset

MODEL_PATH = sys.argv[1]  # Can be base or checkpoint
DATA_PATH = sys.argv[2]
OUTPUT_DIR = sys.argv[3]
NUM_EPOCHS = int(sys.argv[4]) if len(sys.argv) > 4 else 5
LR = float(sys.argv[5]) if len(sys.argv) > 5 else 5e-5

os.makedirs(OUTPUT_DIR, exist_ok=True)

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH, torch_dtype=torch.bfloat16, trust_remote_code=True,
)

with open(DATA_PATH) as f:
    raw_data = json.load(f)

def format_chat(example):
    text = tokenizer.apply_chat_template(
        example["messages"], tokenize=False, add_generation_prompt=False,
    )
    return {"text": text}

dataset = Dataset.from_list(raw_data)
dataset = dataset.map(format_chat, remove_columns=["messages"])
dataset = dataset.filter(lambda x: len(tokenizer(x["text"], truncation=False)["input_ids"]) <= 2048, num_proc=4)
ds = dataset.train_test_split(test_size=0.01, seed=42)
print(f"Train: {len(ds['train'])}, Eval: {len(ds['test'])}")

training_args = SFTConfig(
    output_dir=OUTPUT_DIR,
    num_train_epochs=NUM_EPOCHS,
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=LR,
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,
    weight_decay=0.01,
    logging_steps=20,
    save_strategy="epoch",
    bf16=True,
    gradient_checkpointing=True,
    max_length=2048,
    packing=True,
    dataset_text_field="text",
    report_to="none",
    optim="adamw_torch",
    seed=42,
    ddp_find_unused_parameters=False,
    dataloader_num_workers=2,
)

trainer = SFTTrainer(
    model=model, args=training_args,
    train_dataset=ds["train"], eval_dataset=ds["test"],
    processing_class=tokenizer,
)

print("Starting training...")
trainer.train()
save_path = os.path.join(OUTPUT_DIR, "final")
trainer.save_model(save_path)
tokenizer.save_pretrained(save_path)
print(f"Saved to {save_path}")

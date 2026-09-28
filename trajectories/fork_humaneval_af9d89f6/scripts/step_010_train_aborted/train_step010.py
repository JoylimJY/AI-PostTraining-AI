"""Train step_010: fixed data format (fenced code blocks), 6 epochs from base."""
import json, os
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
from trl import SFTTrainer, SFTConfig

BASE_MODEL = "/home/user/models/Qwen3-1.7B-Base"
DATA_FILE = "artifacts/steps/step_010_data/train_data.json"
OUT_DIR = "artifacts/steps/step_010_train/output"

with open(DATA_FILE) as f:
    raw = json.load(f)

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
if tokenizer.chat_template is None:
    tokenizer.chat_template = open("templates/qwen3.jinja").read()

def to_text(ex):
    return {"text": tokenizer.apply_chat_template(ex["messages"], tokenize=False, add_generation_prompt=False)}

dataset = Dataset.from_list(raw).map(to_text, remove_columns=["messages"])

cfg = SFTConfig(
    output_dir=OUT_DIR,
    num_train_epochs=6,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=5e-5,
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,
    weight_decay=0.01,
    bf16=True,
    max_length=2048,
    packing=True,
    save_strategy="epoch",
    logging_steps=50,
    dataloader_num_workers=4,
    report_to="none",
)

trainer = SFTTrainer(
    model=BASE_MODEL,
    args=cfg,
    train_dataset=dataset,
)

trainer.train()
trainer.save_model(os.path.join(OUT_DIR, "final"))
tokenizer.save_pretrained(os.path.join(OUT_DIR, "final"))
print("Training complete.")

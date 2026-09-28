"""Step 008: AIME-format math SFT from Qwen3-1.7B-Base.

Data: artifacts/steps/step_008_math_data/train_data.json  (23067 samples)
User turns replicate the inspect_evals/aime2025 prompt template exactly;
assistant turns are <think>...</think> followed by a final "ANSWER: <n>" line.
"""
import json, os, sys
from datasets import Dataset
from transformers import AutoTokenizer
from trl import SFTTrainer, SFTConfig

BASE_MODEL = "/home/user/models/Qwen3-1.7B-Base"
DATA_FILE = "artifacts/steps/step_008_math_data/train_data.json"
OUT_DIR = "artifacts/steps/step_008_math_train/output"
TEMPLATE = "templates/qwen3.jinja"

EPOCHS = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
LR = float(sys.argv[2]) if len(sys.argv) > 2 else 2e-5
MAX_LEN = int(sys.argv[3]) if len(sys.argv) > 3 else 4096

os.makedirs(OUT_DIR, exist_ok=True)

with open(DATA_FILE) as f:
    raw = json.load(f)

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
tokenizer.chat_template = open(TEMPLATE).read()

def to_text(ex):
    return {"text": tokenizer.apply_chat_template(
        ex["messages"], tokenize=False, add_generation_prompt=False)}

dataset = Dataset.from_list(raw).map(to_text, remove_columns=["messages"])

cfg = SFTConfig(
    output_dir=OUT_DIR,
    num_train_epochs=EPOCHS,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    learning_rate=LR,
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,
    weight_decay=0.01,
    bf16=True,
    max_length=MAX_LEN,
    packing=True,
    save_strategy="epoch",
    save_total_limit=None,
    logging_steps=20,
    dataloader_num_workers=4,
    report_to="none",
    gradient_checkpointing=True,
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

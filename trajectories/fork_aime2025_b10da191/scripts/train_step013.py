"""Step 013: repair the step_008 collapse with hard-only long-CoT data.

step_012 showed the step_008 model emits bare guesses ("ANSWER: 70") because
~21% of its targets were 2-line answers. We continue training it (LoRA, since
the GPUs are memory-constrained) on step_013 hard-only data, where every target
contains >=1200 chars of reasoning, so the shortcut is unavailable.
"""
import json, os, sys
from datasets import Dataset
from transformers import AutoTokenizer
from peft import LoraConfig
from trl import SFTTrainer, SFTConfig

BASE = "artifacts/steps/step_008_math_train/output/final"   # our own prior fine-tune
DATA = "artifacts/steps/step_013_hard_data/train_data.json"
OUT = "artifacts/steps/step_013_hard_train/output"
TEMPLATE = "templates/qwen3.jinja"

EPOCHS = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
LR = float(sys.argv[2]) if len(sys.argv) > 2 else 1e-4
MAX_LEN = int(sys.argv[3]) if len(sys.argv) > 3 else 3072

os.makedirs(OUT, exist_ok=True)

raw = json.load(open(DATA))
tokenizer = AutoTokenizer.from_pretrained(BASE)
tokenizer.chat_template = open(TEMPLATE).read()

ds = Dataset.from_list(raw).map(
    lambda ex: {"text": tokenizer.apply_chat_template(
        ex["messages"], tokenize=False, add_generation_prompt=False)},
    remove_columns=["messages"])

cfg = SFTConfig(
    output_dir=OUT,
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
    logging_steps=10,
    dataloader_num_workers=2,
    report_to="none",
    gradient_checkpointing=True,
)

peft_cfg = LoraConfig(
    r=64, lora_alpha=128, lora_dropout=0.0, bias="none",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    task_type="CAUSAL_LM",
)

trainer = SFTTrainer(model=BASE, args=cfg, train_dataset=ds, peft_config=peft_cfg)
trainer.train()
trainer.save_model(os.path.join(OUT, "adapter"))
tokenizer.save_pretrained(os.path.join(OUT, "adapter"))
print("Training complete.")

"""Merge the step_013 LoRA adapter into the step_008 base for eval/export."""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE = "artifacts/steps/step_008_math_train/output/final"
ADAPTER = "artifacts/steps/step_013_hard_train/output/adapter"
OUT = "artifacts/steps/step_013_hard_train/output/merged"

model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16)
tokenizer = AutoTokenizer.from_pretrained(BASE)
model = PeftModel.from_pretrained(model, ADAPTER)
model = model.merge_and_unload()
model.save_pretrained(OUT, safe_serialization=True)
tokenizer.save_pretrained(OUT)
print("merged ->", OUT)

#!/usr/bin/env python3
"""
SFT Training script V2 for GSM8K math fine-tuning of Qwen3-1.7B-Base.
Uses raw text format with proper chat template.
"""

import argparse
import json
import os
import logging
from datetime import datetime

import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTTrainer, SFTConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=str, default="/home/user/models/Qwen3-1.7B-Base")
    parser.add_argument("--data-path", type=str, default="artifacts/training_data/train_v3.jsonl")
    parser.add_argument("--output-dir", type=str, required=True)
    parser.add_argument("--num-epochs", type=float, default=3.0)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--gradient-accumulation", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--max-seq-length", type=int, default=2048)
    parser.add_argument("--warmup-ratio", type=float, default=0.05)
    parser.add_argument("--lr-scheduler", type=str, default="cosine")
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--bf16", action="store_true", default=True)
    parser.add_argument("--gradient-checkpointing", action="store_true", default=True)
    parser.add_argument("--logging-steps", type=int, default=10)
    parser.add_argument("--save-steps", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main():
    args = parse_args()

    logger.info(f"Starting training at {datetime.now().isoformat()}")
    logger.info(f"Args: {vars(args)}")

    os.makedirs(args.output_dir, exist_ok=True)

    with open(os.path.join(args.output_dir, "train_config.json"), "w") as f:
        json.dump(vars(args), f, indent=2)

    # Load tokenizer
    logger.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load model
    logger.info("Loading model...")
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        dtype=torch.bfloat16,
        trust_remote_code=True,
        attn_implementation="flash_attention_2",
    )

    if args.gradient_checkpointing:
        model.gradient_checkpointing_enable()

    # Load dataset - raw text format
    logger.info(f"Loading dataset from {args.data_path}...")
    dataset = load_dataset("json", data_files=args.data_path, split="train")
    logger.info(f"Dataset size: {len(dataset)}")

    # Training arguments
    training_args = SFTConfig(
        output_dir=args.output_dir,
        num_train_epochs=args.num_epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation,
        learning_rate=args.learning_rate,
        lr_scheduler_type=args.lr_scheduler,
        warmup_ratio=args.warmup_ratio,
        weight_decay=args.weight_decay,
        bf16=args.bf16,
        logging_steps=args.logging_steps,
        save_steps=args.save_steps,
        save_strategy="steps",
        seed=args.seed,
        max_length=args.max_seq_length,
        gradient_checkpointing=args.gradient_checkpointing,
        gradient_checkpointing_kwargs={"use_reentrant": False} if args.gradient_checkpointing else {},
        report_to="none",
        dataloader_num_workers=4,
        ddp_find_unused_parameters=False,
        optim="adamw_torch",
        dataset_text_field="text",  # Use raw text field
    )

    # Create trainer
    logger.info("Creating trainer...")
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )

    # Train
    logger.info("Starting training...")
    train_result = trainer.train()

    # Save
    logger.info("Saving model...")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    metrics = train_result.metrics
    trainer.log_metrics("train", metrics)
    trainer.save_metrics("train", metrics)
    trainer.save_state()

    logger.info(f"Training complete. Model saved to {args.output_dir}")
    logger.info(f"Metrics: {metrics}")


if __name__ == "__main__":
    main()

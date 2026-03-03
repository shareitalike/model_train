#!/usr/bin/env python3
"""
Fine-tune microsoft/trocr-base-handwritten on Kaithi dataset.
Target: CER < 5%, WER < 15%

Usage:
    python train_trocr.py \
        --dataset_path ./kaithi_dataset/hf_dataset \
        --output_dir   ./models/kaithi-trocr-v1 \
        --epochs       30
"""

import argparse
import os
import json
from pathlib import Path
from typing import Optional

from PIL import Image
import torch
from torch.utils.data import Dataset
from transformers import (
    TrOCRProcessor,
    VisionEncoderDecoderModel,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    default_data_collator,
)
from datasets import load_from_disk
from loguru import logger

try:
    import evaluate
    cer_metric = evaluate.load("cer")
    wer_metric = evaluate.load("wer")
    EVAL_OK = True
except Exception:
    EVAL_OK = False
    logger.warning("evaluate library not available — skipping CER/WER metrics")


# ══════════════════════════════════════════════════════════════════════════════
# Dataset
# ══════════════════════════════════════════════════════════════════════════════

class KaithiDataset(Dataset):
    def __init__(self, hf_dataset, processor, max_label_len: int = 128):
        self.data      = hf_dataset
        self.processor = processor
        self.max_len   = max_label_len

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item  = self.data[idx]
        label = item.get("text", "")

        # Load image
        img_path = item.get("image", "")
        try:
            if isinstance(img_path, str) and os.path.exists(img_path):
                image = Image.open(img_path).convert("RGB")
            else:
                image = Image.new("RGB", (384, 64), color=(255, 255, 255))
        except Exception:
            image = Image.new("RGB", (384, 64), color=(255, 255, 255))

        pixel_values = self.processor(
            images=image, return_tensors="pt"
        ).pixel_values.squeeze(0)

        with self.processor.tokenizer.as_target_tokenizer():
            labels = self.processor.tokenizer(
                label,
                padding="max_length",
                max_length=self.max_len,
                truncation=True,
                return_tensors="pt",
            ).input_ids.squeeze(0)

        # Replace pad token id with -100 so it's ignored in loss
        labels[labels == self.processor.tokenizer.pad_token_id] = -100

        return {"pixel_values": pixel_values, "labels": labels}


# ══════════════════════════════════════════════════════════════════════════════
# Metrics
# ══════════════════════════════════════════════════════════════════════════════

def make_compute_metrics(processor):
    def compute_metrics(eval_pred):
        if not EVAL_OK:
            return {}
        pred_ids, label_ids = eval_pred
        
        # Seq2SeqTrainer with predict_with_generate returns generated token IDs directly
        if isinstance(pred_ids, tuple):
            pred_ids = pred_ids[0]
            
        label_ids[label_ids == -100] = processor.tokenizer.pad_token_id
        pred_str  = processor.batch_decode(pred_ids,   skip_special_tokens=True)
        label_str = processor.batch_decode(label_ids,  skip_special_tokens=True)
        return {
            "cer": cer_metric.compute(predictions=pred_str, references=label_str),
            "wer": wer_metric.compute(predictions=pred_str, references=label_str),
        }
    return compute_metrics


# ══════════════════════════════════════════════════════════════════════════════
# Training
# ══════════════════════════════════════════════════════════════════════════════

def train(
    dataset_path: str,
    output_dir: str,
    base_model: str = "microsoft/trocr-base-handwritten",
    epochs: int = 30,
    batch_size: int = 8,
    learning_rate: float = 4e-5,
    warmup_steps: int = 500,
    grad_accumulation: int = 4,
    fp16: bool = None,
    eval_steps: int = 500,
    save_steps: int = 500,
    logging_steps: int = 100,
    max_label_len: int = 128,
    resume_from: Optional[str] = None,
):
    fp16 = fp16 if fp16 is not None else torch.cuda.is_available()
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Loading dataset from {dataset_path}")

    try:
        ds = load_from_disk(dataset_path)
        train_split = ds["train"]
        val_split   = ds.get("validation", ds.get("test"))
    except Exception:
        logger.error(f"Dataset not found at {dataset_path}")
        logger.info("Generate synthetic data first: python synthetic_data_gen.py")
        return

    logger.info(f"Train: {len(train_split)} | Val: {len(val_split) if val_split else 0}")
    logger.info(f"Loading base model: {base_model}")

    processor = TrOCRProcessor.from_pretrained(base_model)
    model     = VisionEncoderDecoderModel.from_pretrained(base_model)

    model.config.decoder_start_token_id = processor.tokenizer.cls_token_id
    model.config.pad_token_id           = processor.tokenizer.pad_token_id
    model.config.eos_token_id           = processor.tokenizer.sep_token_id
    model.config.max_new_tokens         = max_label_len
    model.config.early_stopping         = True
    model.config.num_beams              = 4
    model.config.no_repeat_ngram_size   = 3

    train_ds = KaithiDataset(train_split, processor, max_label_len)
    val_ds   = KaithiDataset(val_split,   processor, max_label_len) if val_split else None

    training_args = Seq2SeqTrainingArguments(
        output_dir=output_dir,
        predict_with_generate=True,
        eval_strategy="steps" if val_ds else "no",
        eval_steps=eval_steps,
        save_steps=save_steps,
        logging_steps=logging_steps,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=grad_accumulation,
        learning_rate=learning_rate,
        warmup_steps=warmup_steps,
        lr_scheduler_type="cosine",
        fp16=fp16,
        dataloader_num_workers=2,
        load_best_model_at_end=True if val_ds else False,
        metric_for_best_model="cer" if EVAL_OK else "loss",
        greater_is_better=False,
        save_total_limit=3,
        generation_max_length=max_label_len,
        report_to="none",
        run_name="kaithi-trocr",
    )

    trainer = Seq2SeqTrainer(
        model=model,
        tokenizer=processor.image_processor,
        args=training_args,
        compute_metrics=make_compute_metrics(processor) if EVAL_OK else None,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=default_data_collator,
    )

    logger.info(f"Starting training — {epochs} epochs | fp16={fp16} | device={'GPU' if fp16 else 'CPU'}")
    trainer.train(resume_from_checkpoint=resume_from)
    trainer.save_model(output_dir)
    processor.save_pretrained(output_dir)

    # Save training summary
    summary = {
        "base_model":     base_model,
        "epochs":         epochs,
        "train_samples":  len(train_split),
        "output_dir":     output_dir,
        "fp16":           fp16,
    }
    if EVAL_OK and val_ds:
        metrics = trainer.evaluate()
        summary["eval_cer"] = metrics.get("eval_cer", "N/A")
        summary["eval_wer"] = metrics.get("eval_wer", "N/A")
        logger.info(f"Final CER: {summary['eval_cer']} | WER: {summary['eval_wer']}")

    with open(os.path.join(output_dir, "training_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Model saved to {output_dir}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune TrOCR for Kaithi OCR")
    parser.add_argument("--dataset_path",  default="./kaithi_dataset/hf_dataset")
    parser.add_argument("--output_dir",    default="./models/kaithi-trocr-v1")
    parser.add_argument("--base_model",    default="microsoft/trocr-base-handwritten")
    parser.add_argument("--epochs",        type=int,   default=30)
    parser.add_argument("--batch_size",    type=int,   default=8)
    parser.add_argument("--lr",            type=float, default=4e-5)
    parser.add_argument("--warmup",        type=int,   default=500)
    parser.add_argument("--grad_accum",    type=int,   default=4)
    parser.add_argument("--eval_steps",    type=int,   default=500)
    parser.add_argument("--resume_from",   default=None)
    args = parser.parse_args()

    train(
        dataset_path=args.dataset_path,
        output_dir=args.output_dir,
        base_model=args.base_model,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        warmup_steps=args.warmup,
        grad_accumulation=args.grad_accum,
        eval_steps=args.eval_steps,
        resume_from=args.resume_from,
    )

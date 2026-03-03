#!/usr/bin/env python3
"""
Evaluate a trained Kaithi TrOCR model on the test set.

Usage:
    python evaluate.py \
        ./models/kaithi-trocr-v1 \
        ./kaithi_dataset/test.json
"""

import argparse
import json
import os
from pathlib import Path
from PIL import Image
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel


def cer(pred: str, ref: str) -> float:
    """Character Error Rate via edit distance."""
    if len(ref) == 0:
        return 0.0 if len(pred) == 0 else 1.0
    dp = [[0] * (len(pred) + 1) for _ in range(len(ref) + 1)]
    for i in range(len(ref) + 1): dp[i][0] = i
    for j in range(len(pred) + 1): dp[0][j] = j
    for i in range(1, len(ref) + 1):
        for j in range(1, len(pred) + 1):
            if ref[i-1] == pred[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    return dp[len(ref)][len(pred)] / len(ref)


def wer(pred: str, ref: str) -> float:
    pw = pred.split()
    rw = ref.split()
    if not rw:
        return 0.0 if not pw else 1.0
    dp = [[0] * (len(pw) + 1) for _ in range(len(rw) + 1)]
    for i in range(len(rw) + 1): dp[i][0] = i
    for j in range(len(pw) + 1): dp[0][j] = j
    for i in range(1, len(rw) + 1):
        for j in range(1, len(pw) + 1):
            dp[i][j] = dp[i-1][j-1] if rw[i-1] == pw[j-1] else 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    return dp[len(rw)][len(pw)] / len(rw)


def evaluate(model_path: str, test_json: str, max_samples: int = 500):
    print(f"Loading model from {model_path}")
    processor = TrOCRProcessor.from_pretrained(model_path)
    model     = VisionEncoderDecoderModel.from_pretrained(model_path)
    device    = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device).eval()
    print(f"Device: {device}")

    with open(test_json, encoding="utf-8") as f:
        samples = json.load(f)

    samples = samples[:max_samples]
    print(f"Evaluating on {len(samples)} samples...")

    cer_scores, wer_scores, preds = [], [], []

    for i, s in enumerate(samples):
        img_path = s.get("image", "")
        label    = s.get("text",  "")

        try:
            if os.path.exists(img_path):
                image = Image.open(img_path).convert("RGB")
            else:
                image = Image.new("RGB", (200, 50), (255, 255, 255))
        except Exception:
            image = Image.new("RGB", (200, 50), (255, 255, 255))

        pixel_values = processor(images=image, return_tensors="pt").pixel_values.to(device)
        with torch.no_grad():
            generated = model.generate(pixel_values, num_beams=4, max_new_tokens=128)
        pred = processor.batch_decode(generated, skip_special_tokens=True)[0].strip()

        c = cer(pred, label)
        w = wer(pred, label)
        cer_scores.append(c)
        wer_scores.append(w)
        preds.append({"prediction": pred, "label": label, "cer": round(c, 4), "wer": round(w, 4)})

        if (i + 1) % 50 == 0:
            avg_cer = sum(cer_scores) / len(cer_scores)
            avg_wer = sum(wer_scores) / len(wer_scores)
            print(f"  [{i+1}/{len(samples)}] CER={avg_cer:.4f} WER={avg_wer:.4f}")

    avg_cer = sum(cer_scores) / len(cer_scores)
    avg_wer = sum(wer_scores) / len(wer_scores)
    perfect = sum(1 for p in preds if p["cer"] == 0.0)

    results = {
        "model":          model_path,
        "test_samples":   len(samples),
        "avg_cer":        round(avg_cer, 4),
        "avg_wer":        round(avg_wer, 4),
        "perfect_match":  perfect,
        "perfect_pct":    round(perfect / len(preds) * 100, 1),
        "target_cer_met": avg_cer < 0.05,
        "target_wer_met": avg_wer < 0.15,
        "samples":        preds[:20],  # First 20 for inspection
    }

    print("\n" + "="*50)
    print(f"RESULTS — {len(samples)} samples")
    print(f"  Avg CER: {avg_cer:.4f} {'✓' if avg_cer<0.05 else '✗'} (target < 0.05)")
    print(f"  Avg WER: {avg_wer:.4f} {'✓' if avg_wer<0.15 else '✗'} (target < 0.15)")
    print(f"  Perfect: {perfect}/{len(preds)} ({results['perfect_pct']}%)")
    print("="*50)

    out_path = os.path.join(os.path.dirname(test_json), "evaluation_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to {out_path}")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("model_path")
    parser.add_argument("test_json")
    parser.add_argument("--max_samples", type=int, default=500)
    args = parser.parse_args()
    evaluate(args.model_path, args.test_json, args.max_samples)

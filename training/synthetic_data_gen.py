#!/usr/bin/env python3
"""
Synthetic Kaithi training data generator.
Creates realistic handwritten-style images for fine-tuning TrOCR.

Usage:
    python synthetic_data_gen.py \
        --output_dir ./kaithi_dataset \
        --num_samples 10000
"""

import os
import json
import random
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

# Kaithi ↔ Hindi text pairs (land records domain)
SENTENCE_PAIRS = [
    ("\U0001108F\U000110B0\U000110A2", "का न"),           # kaan
    ("\U0001109E\U000110B9\U000110A9", "त्र"),              # tra
    ("\U0001108F\U000110B9\U000110AE", "क्स"),              # ksa
    ("\U0001109E\U000110B9\U000110AE\U000110B0\U000110B2\U000110AE", "त्साल"),
    ("\U0001108F\U000110B0\U000110A2\U000110B0", "काना"),   # kaana
    ("\U000110A7\U000110B0\U000110AA\U000110B2", "माली"),   # mali
    ("\U000110A9\U000110B0\U000110A2\U000110B0", "राना"),   # rana
    # Land record Hindi pairs
    ("खेत", "खेत"),
    ("जमीन", "जमीन"),
    ("बीघा", "बीघा"),
    ("खाता", "खाता"),
    ("मालगुजारी", "मालगुजारी"),
    ("रैयत", "रैयत"),
    ("जमींदार", "जमींदार"),
    ("परगना", "परगना"),
    ("तहसील", "तहसील"),
    ("मौजा", "मौजा"),
    ("चकबंदी", "चकबंदी"),
    ("पट्टा", "पट्टा"),
    ("लगान", "लगान"),
    ("सर्वे नंबर", "सर्वे नंबर"),
    ("खसरा", "खसरा"),
    ("खतौनी", "खतौनी"),
    ("पैमाइश", "पैमाइश"),
    ("भूमि अभिलेख", "भूमि अभिलेख"),
    ("राजस्व विभाग", "राजस्व विभाग"),
    ("भू-स्वामी", "भू-स्वामी"),
    ("ग्राम पंचायत", "ग्राम पंचायत"),
    ("जिलाधिकारी", "जिलाधिकारी"),
    ("सम्पत्ति कर", "सम्पत्ति कर"),
    ("कृषि भूमि", "कृषि भूमि"),
]

PAPER_COLORS = [
    (245, 238, 220), (252, 245, 230), (240, 232, 210),
    (255, 248, 235), (238, 228, 200), (250, 240, 215),
]

INK_COLORS = [
    (20, 15, 10), (35, 25, 15), (10, 10, 40),
    (30, 20, 10), (15, 10, 5),  (5, 5, 30),
]


def _load_font(font_path: str = None, size: int = 28):
    if font_path and os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    # Try system Devanagari fonts
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/app/fonts/NotoSansDevanagari-Regular.ttf",
        "/System/Library/Fonts/Supplemental/NotoSansDevanagari.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    return ImageFont.load_default()


def generate_sample(
    source_text: str,
    label_text:  str,
    font_path:   str = None,
    output_dir:  str = "./tmp_images",
    idx:         int = 0,
    augment_level: int = 1,
) -> tuple:
    os.makedirs(output_dir, exist_ok=True)

    # Vary font size
    font_size = random.randint(22, 36)
    font = _load_font(font_path, font_size)

    # Paper / ink colors
    paper_col = random.choice(PAPER_COLORS)
    ink_col   = random.choice(INK_COLORS)

    # Determine image size
    text_to_render = source_text if source_text.strip() else label_text
    dummy_img  = Image.new("RGB", (800, 80), paper_col)
    dummy_draw = ImageDraw.Draw(dummy_img)
    try:
        bbox = dummy_draw.textbbox((0, 0), text_to_render, font=font)
        tw   = bbox[2] - bbox[0]
        th   = bbox[3] - bbox[1]
    except AttributeError:
        tw, th = dummy_draw.textsize(text_to_render, font=font)

    w = max(128, tw + random.randint(20, 60))
    h = max(48,  th + random.randint(16, 32))
    img  = Image.new("RGB", (w, h), paper_col)
    draw = ImageDraw.Draw(img)

    # Text position (slight random offset)
    x = random.randint(8, 20)
    y = random.randint(6, 14)

    # Optional baseline wobble
    if augment_level >= 2:
        for i, char in enumerate(text_to_render):
            cy = y + random.randint(-2, 2)
            try:
                cbox = draw.textbbox((0, 0), text_to_render[:i+1], font=font)
                cx = x + cbox[2] - cbox[0] - (draw.textbbox((0, 0), char, font=font)[2] - draw.textbbox((0, 0), char, font=font)[0])
            except Exception:
                cx = x + i * (font_size // 2)
            draw.text((cx, cy), char, fill=ink_col, font=font)
    else:
        draw.text((x, y), text_to_render, fill=ink_col, font=font)

    # Augmentations
    img_np = np.array(img)

    if augment_level >= 1:
        # Paper texture noise
        noise = np.random.normal(0, random.uniform(2, 8), img_np.shape).astype(np.int16)
        img_np = np.clip(img_np.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        # Brightness/contrast variation
        alpha = random.uniform(0.85, 1.15)
        beta  = random.uniform(-10, 10)
        img_np = np.clip(img_np.astype(np.float32) * alpha + beta, 0, 255).astype(np.uint8)

    if augment_level >= 2:
        img = Image.fromarray(img_np)
        # Slight blur
        if random.random() < 0.4:
            img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 0.7)))
        # Yellowing
        if random.random() < 0.5:
            y_layer = Image.new("RGB", img.size, (random.randint(230,255), random.randint(220,245), random.randint(180,210)))
            img = Image.blend(img, y_layer, alpha=random.uniform(0.05, 0.18))
        img_np = np.array(img)

    if augment_level >= 3:
        img = Image.fromarray(img_np)
        # JPEG compression artifact
        import io
        buf = io.BytesIO()
        quality = random.randint(60, 85)
        img.save(buf, format="JPEG", quality=quality)
        buf.seek(0)
        img = Image.open(buf)
        img_np = np.array(img)

    img = Image.fromarray(img_np)

    # Save
    filename = f"sample_{idx:06d}.png"
    img_path = os.path.join(output_dir, filename)
    img.save(img_path, "PNG", optimize=True)

    return img_path, label_text


def build_synthetic_dataset(
    output_dir:    str  = "./kaithi_dataset",
    num_samples:   int  = 10000,
    font_path:     str  = None,
    seed:          int  = 42,
    val_ratio:     float = 0.1,
    test_ratio:    float = 0.1,
):
    random.seed(seed)
    np.random.seed(seed)

    img_dir = os.path.join(output_dir, "images")
    os.makedirs(img_dir, exist_ok=True)

    samples = []
    pairs   = SENTENCE_PAIRS * max(1, num_samples // len(SENTENCE_PAIRS) + 1)
    random.shuffle(pairs)

    print(f"Generating {num_samples} synthetic samples...")
    for i, (kaithi, hindi) in enumerate(pairs[:num_samples]):
        aug = random.choices([0,1,2,3], weights=[5,30,50,15])[0]
        try:
            img_path, label = generate_sample(
                source_text=kaithi or hindi,
                label_text=hindi,
                font_path=font_path,
                output_dir=img_dir,
                idx=i,
                augment_level=aug,
            )
            samples.append({"image": img_path, "text": label, "source": "synthetic", "aug": aug})
        except Exception as e:
            print(f"  Sample {i} failed: {e}")

        if (i + 1) % 1000 == 0:
            print(f"  Generated {i+1}/{num_samples}")

    print(f"Total samples: {len(samples)}")

    # Split
    random.shuffle(samples)
    n   = len(samples)
    t1  = int(n * (1 - val_ratio - test_ratio))
    t2  = int(n * (1 - test_ratio))
    splits = {
        "train":      samples[:t1],
        "validation": samples[t1:t2],
        "test":       samples[t2:],
    }

    for name, data in splits.items():
        path = os.path.join(output_dir, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  Saved {name}: {len(data)} samples → {path}")

    # Try HuggingFace format
    try:
        from datasets import Dataset, DatasetDict
        hf_dir = os.path.join(output_dir, "hf_dataset")
        hf_ds  = DatasetDict({k: Dataset.from_list(v) for k, v in splits.items()})
        hf_ds.save_to_disk(hf_dir)
        print(f"  HuggingFace dataset saved: {hf_dir}")
    except ImportError:
        print("  HuggingFace datasets not installed — skipping HF format")

    print(f"\nDataset complete: {output_dir}")
    return splits


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir",  default="./kaithi_dataset")
    parser.add_argument("--num_samples", type=int, default=10000)
    parser.add_argument("--font_path",   default=None)
    parser.add_argument("--seed",        type=int, default=42)
    args = parser.parse_args()
    build_synthetic_dataset(
        output_dir=args.output_dir,
        num_samples=args.num_samples,
        font_path=args.font_path,
        seed=args.seed,
    )

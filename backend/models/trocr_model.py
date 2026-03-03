import torch
import numpy as np
from PIL import Image
from pathlib import Path
from typing import List, Tuple, Optional
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from loguru import logger


class KaithiTrOCR:
    def __init__(
        self,
        model_path: Optional[str] = None,
        base_model: str = "microsoft/trocr-base-handwritten",
        device: Optional[str] = None,
        batch_size: int = 8,
        num_beams: int = 4,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.batch_size = batch_size
        self.num_beams = num_beams

        src = base_model
        if model_path and Path(model_path).exists():
            src = model_path
            logger.info(f"[TrOCR] Loading fine-tuned model: {src}")
        else:
            logger.info(f"[TrOCR] Using base model: {src}")

        self.processor = TrOCRProcessor.from_pretrained(src)
        self.model = VisionEncoderDecoderModel.from_pretrained(src)
        self.model.to(self.device)
        self.model.eval()

        self.model.config.decoder_start_token_id = self.processor.tokenizer.cls_token_id
        self.model.config.pad_token_id = self.processor.tokenizer.pad_token_id
        self.model.config.eos_token_id = self.processor.tokenizer.sep_token_id
        self.model.config.max_new_tokens = 128
        self.model.config.early_stopping = True
        self.model.config.num_beams = num_beams

        logger.info(f"[TrOCR] Ready | device={self.device} | beams={num_beams}")

    def recognize_line(self, line_img: np.ndarray) -> Tuple[str, float]:
        pil = Image.fromarray(line_img).convert("RGB")
        pixel_values = self.processor(images=pil, return_tensors="pt").pixel_values.to(self.device)
        with torch.no_grad():
            outputs = self.model.generate(
                pixel_values, num_beams=self.num_beams, max_new_tokens=128,
                output_scores=True, return_dict_in_generate=True,
            )
        text = self.processor.batch_decode(outputs.sequences, skip_special_tokens=True)[0]
        confidence = self._extract_confidence(outputs)
        return text.strip(), confidence

    def recognize_batch(self, line_images: List[np.ndarray]) -> List[Tuple[str, float]]:
        results = []
        for i in range(0, len(line_images), self.batch_size):
            chunk = line_images[i:i + self.batch_size]
            pil_images = [Image.fromarray(img).convert("RGB") for img in chunk]
            pixel_values = self.processor(
                images=pil_images, return_tensors="pt", padding=True
            ).pixel_values.to(self.device)
            with torch.no_grad():
                outputs = self.model.generate(
                    pixel_values, num_beams=self.num_beams, max_new_tokens=128,
                    output_scores=True, return_dict_in_generate=True,
                )
            texts = self.processor.batch_decode(outputs.sequences, skip_special_tokens=True)
            conf = self._extract_confidence(outputs)
            for t in texts:
                results.append((t.strip(), conf))
        return results

    def _extract_confidence(self, outputs) -> float:
        if not hasattr(outputs, "scores") or not outputs.scores:
            return 0.80
        probs = []
        for step_scores in outputs.scores:
            step_probs = torch.softmax(step_scores, dim=-1)
            max_probs = step_probs.max(dim=-1).values
            probs.extend(max_probs.cpu().float().tolist())
        return float(np.mean(probs)) if probs else 0.80

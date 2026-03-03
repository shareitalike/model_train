import fitz
import numpy as np
from PIL import Image
from typing import Optional, List
from loguru import logger
from dataclasses import dataclass, field
import time
import io

from .preprocessing import DocumentPreprocessor
from .trocr_model import KaithiTrOCR
from .transliterator import KaithiTransliterator
from .language_corrector import LanguageCorrector
from ..core.config import get_settings

settings = get_settings()


@dataclass
class PageResult:
    page_number: int
    kaithi_text: str = ""
    hindi_text: str = ""
    corrected_text: str = ""
    confidence: float = 0.0
    word_boxes: List[dict] = field(default_factory=list)
    line_count: int = 0
    preprocessing_meta: dict = field(default_factory=dict)
    processing_time_ms: float = 0.0


@dataclass
class PipelineResult:
    pages: List[PageResult] = field(default_factory=list)
    full_hindi_text: str = ""
    overall_confidence: float = 0.0
    total_pages: int = 0
    region: str = "standard"
    processing_time_ms: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "pages": [
                {
                    "page_number": p.page_number,
                    "kaithi_text": p.kaithi_text,
                    "hindi_text": p.hindi_text,
                    "corrected_text": p.corrected_text,
                    "confidence": p.confidence,
                    "word_boxes": p.word_boxes,
                    "line_count": p.line_count,
                    "processing_time_ms": p.processing_time_ms,
                }
                for p in self.pages
            ],
            "full_hindi_text": self.full_hindi_text,
            "overall_confidence": self.overall_confidence,
            "total_pages": self.total_pages,
            "region": self.region,
            "processing_time_ms": self.processing_time_ms,
            "metadata": self.metadata,
        }


class KaithiOCRPipeline:
    def __init__(self, region: str = "standard"):
        self.region = region
        self.preprocessor = DocumentPreprocessor()
        self.ocr_model = KaithiTrOCR(
            model_path=settings.MODEL_PATH,
            base_model=settings.TROCR_BASE,
            batch_size=settings.OCR_BATCH_SIZE,
        )
        self.transliterator = KaithiTransliterator(region=region)
        self.corrector = LanguageCorrector()
        logger.info(f"[Pipeline] Initialized | region={region}")

    def process_pdf_bytes(
        self,
        pdf_bytes: bytes,
        dpi: int = None,
        page_range: Optional[tuple] = None,
        progress_callback=None,
    ) -> PipelineResult:
        dpi = dpi or settings.OCR_DPI
        t0 = time.time()
        result = PipelineResult(region=self.region)

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total = doc.page_count
        result.total_pages = total

        start_p = page_range[0] if page_range else 0
        end_p = page_range[1] if page_range else total
        confidences = []

        for i in range(start_p, end_p):
            if progress_callback:
                pct = int(((i - start_p) / max(1, end_p - start_p)) * 90)
                progress_callback(pct)
            logger.info(f"[Pipeline] Page {i+1}/{total}")
            page_result = self._process_page(doc[i], i, dpi)
            result.pages.append(page_result)
            confidences.append(page_result.confidence)

        doc.close()
        result.full_hindi_text = "\n\n--- पृष्ठ विभाजक ---\n\n".join(
            p.corrected_text or p.hindi_text for p in result.pages if p.hindi_text
        )
        result.overall_confidence = round(sum(confidences) / max(1, len(confidences)), 4)
        result.processing_time_ms = round((time.time() - t0) * 1000, 1)
        result.metadata = {
            "total_pages": total,
            "processed_pages": end_p - start_p,
            "region": self.region,
            "dpi": dpi,
        }
        return result

    def _process_page(self, pdf_page, page_idx: int, dpi: int) -> PageResult:
        t0 = time.time()
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = pdf_page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
        img_bytes = pix.tobytes("png")
        image = np.array(Image.open(io.BytesIO(img_bytes)).convert("L"))

        binary, prep_meta = self.preprocessor.full_pipeline(image)
        lines = self.preprocessor.extract_lines(binary)
        if not lines:
            return PageResult(page_number=page_idx + 1,
                              processing_time_ms=round((time.time() - t0) * 1000, 1))

        line_images = [l[0] for l in lines]
        line_boxes = [l[1] for l in lines]
        ocr_results = self.ocr_model.recognize_batch(line_images)

        text_lines = []
        all_word_boxes = []
        confidences = []

        for idx, (text, conf) in enumerate(ocr_results):
            text_lines.append(text)
            confidences.append(conf)
            y_offset = line_boxes[idx][1]
            boxes = self.preprocessor.get_word_boxes(line_images[idx], y_offset=y_offset)
            for b in boxes:
                b["confidence"] = conf
                b["line"] = idx
            all_word_boxes.extend(boxes)

        raw_text = "\n".join(text_lines)
        trans = self.transliterator.transliterate(raw_text)
        hindi = trans["hindi"]
        corrected = self.corrector.correct(hindi)
        avg_conf = round(sum(confidences) / max(1, len(confidences)), 4)

        return PageResult(
            page_number=page_idx + 1,
            kaithi_text=raw_text,
            hindi_text=hindi,
            corrected_text=corrected,
            confidence=avg_conf,
            word_boxes=all_word_boxes,
            line_count=len(lines),
            preprocessing_meta=prep_meta,
            processing_time_ms=round((time.time() - t0) * 1000, 1),
        )

    def process_image_bytes(self, image_bytes: bytes) -> PageResult:
        image = np.array(Image.open(io.BytesIO(image_bytes)).convert("L"))
        binary, meta = self.preprocessor.full_pipeline(image)
        lines = self.preprocessor.extract_lines(binary)
        if not lines:
            return PageResult(page_number=1)
        line_images = [l[0] for l in lines]
        ocr_results = self.ocr_model.recognize_batch(line_images)
        text = "\n".join(t for t, _ in ocr_results)
        trans = self.transliterator.transliterate(text)
        corrected = self.corrector.correct(trans["hindi"])
        conf = sum(c for _, c in ocr_results) / max(1, len(ocr_results))
        return PageResult(
            page_number=1,
            kaithi_text=text,
            hindi_text=trans["hindi"],
            corrected_text=corrected,
            confidence=round(conf, 4),
            line_count=len(lines),
        )

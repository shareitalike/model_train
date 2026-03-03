import cv2
import numpy as np
from PIL import Image
from typing import Tuple, List
from loguru import logger
import math


class DocumentPreprocessor:
    def __init__(self, target_min_dim: int = 1200, dpi: int = 300):
        self.target_min_dim = target_min_dim
        self.dpi = dpi

    def full_pipeline(self, image: np.ndarray) -> Tuple[np.ndarray, dict]:
        meta = {"original_shape": image.shape, "steps": []}
        gray = self._to_gray(image)
        meta["steps"].append("grayscale")
        gray, scale = self._ensure_min_resolution(gray)
        meta["scale"] = scale
        meta["steps"].append(f"upscale_{scale:.2f}x")
        gray, angle = self._deskew(gray)
        meta["skew_deg"] = angle
        meta["steps"].append(f"deskew_{angle:.2f}deg")
        gray = self._crop_scan_border(gray)
        meta["steps"].append("border_crop")
        denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
        meta["steps"].append("nlmeans_denoise")
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        meta["steps"].append("clahe")
        binary = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 15, 8
        )
        meta["steps"].append("adaptive_binarize")
        binary = self._morph_cleanup(binary)
        meta["steps"].append("morph_cleanup")
        meta["final_shape"] = binary.shape
        return binary, meta

    def _to_gray(self, img: np.ndarray) -> np.ndarray:
        if len(img.shape) == 2:
            return img
        if img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def _ensure_min_resolution(self, gray: np.ndarray) -> Tuple[np.ndarray, float]:
        h, w = gray.shape
        if min(h, w) >= self.target_min_dim:
            return gray, 1.0
        scale = self.target_min_dim / min(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        return cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_CUBIC), scale

    def _deskew(self, gray: np.ndarray) -> Tuple[np.ndarray, float]:
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=80)
        if lines is None:
            return gray, 0.0
        angles = []
        for line in lines[:100]:
            rho, theta = line[0]
            angle = np.degrees(theta) - 90.0
            if -45 <= angle <= 45:
                angles.append(angle)
        if not angles:
            return gray, 0.0
        median_angle = float(np.median(angles))
        if abs(median_angle) < 0.3:
            return gray, median_angle
        h, w = gray.shape
        M = cv2.getRotationMatrix2D((w // 2, h // 2), median_angle, 1.0)
        rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC,
                                  borderMode=cv2.BORDER_REPLICATE)
        return rotated, median_angle

    def _crop_scan_border(self, gray: np.ndarray) -> np.ndarray:
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return gray
        x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
        pad = 15
        x1, y1 = max(0, x - pad), max(0, y - pad)
        x2, y2 = min(gray.shape[1], x + w + pad), min(gray.shape[0], y + h + pad)
        return gray[y1:y2, x1:x2]

    def _morph_cleanup(self, binary: np.ndarray) -> np.ndarray:
        k_open = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, k_open)
        k_close = np.ones((1, 1), np.uint8)
        return cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, k_close)

    def extract_lines(self, binary: np.ndarray) -> List[Tuple[np.ndarray, Tuple]]:
        dark_rows = (binary < 128).astype(np.uint8)
        h_proj = dark_rows.sum(axis=1)
        threshold = max(3, h_proj.max() * 0.03)
        in_text = h_proj > threshold
        lines = []
        start = None
        min_height = 12
        for i, is_text in enumerate(in_text):
            if is_text and start is None:
                start = i
            elif not is_text and start is not None:
                if i - start > min_height:
                    y1 = max(0, start - 4)
                    y2 = min(binary.shape[0], i + 4)
                    lines.append((binary[y1:y2, :], (0, y1, binary.shape[1], y2)))
                start = None
        if start is not None:
            y1 = max(0, start - 4)
            y2 = binary.shape[0]
            if y2 - y1 > min_height:
                lines.append((binary[y1:y2, :], (0, y1, binary.shape[1], y2)))
        return lines

    def get_word_boxes(self, line_img: np.ndarray, y_offset: int = 0) -> List[dict]:
        inv = cv2.bitwise_not(line_img)
        kernel = np.ones((3, 25), np.uint8)
        dilated = cv2.dilate(inv, kernel, iterations=1)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        for c in sorted(contours, key=lambda cc: cv2.boundingRect(cc)[0]):
            x, y, w, h = cv2.boundingRect(c)
            if w > 5 and h > 5:
                boxes.append({"x": x, "y": y + y_offset, "w": w, "h": h, "confidence": None})
        return boxes

    @staticmethod
    def to_pil(arr: np.ndarray) -> Image.Image:
        return Image.fromarray(arr)

    @staticmethod
    def from_pil(img: Image.Image) -> np.ndarray:
        return np.array(img)

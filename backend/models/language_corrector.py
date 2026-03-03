import re
from loguru import logger


class LanguageCorrector:
    RULE_CORRECTIONS = [
        (r"  +", " "),
        (r"[।]+", "।"),
        (r"^़", ""),
        (r"(\s)़", r"\1"),
        (r"ंं", "ं"),
    ]

    def __init__(self, use_mlm: bool = False):
        self.mlm_enabled = False
        if use_mlm:
            try:
                from transformers import AutoTokenizer, AutoModelForMaskedLM
                import torch
                self.tokenizer = AutoTokenizer.from_pretrained("ai4bharat/indic-bert")
                self.mlm_model = AutoModelForMaskedLM.from_pretrained("ai4bharat/indic-bert")
                self.mlm_model.eval()
                self.torch = torch
                self.mlm_enabled = True
                logger.info("[LangCorrector] IndicBERT loaded")
            except Exception as e:
                logger.warning(f"[LangCorrector] MLM unavailable: {e}")

    def correct(self, text: str) -> str:
        if not text.strip():
            return text
        text = self._apply_rules(text)
        if self.mlm_enabled:
            try:
                text = self._mlm_pass(text)
            except Exception as e:
                logger.debug(f"[LangCorrector] MLM skipped: {e}")
        return text

    def _apply_rules(self, text: str) -> str:
        for pattern, repl in self.RULE_CORRECTIONS:
            text = re.sub(pattern, repl, text)
        return text.strip()

    def _mlm_pass(self, text: str) -> str:
        import torch
        inputs = self.tokenizer(text, return_tensors="pt", max_length=256, truncation=True)
        with torch.no_grad():
            logits = self.mlm_model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)
        ids = inputs["input_ids"][0].clone()
        for i in range(1, len(ids) - 1):
            orig_id = ids[i].item()
            if probs[0, i, orig_id].item() < 0.05:
                best_id = probs[0, i].argmax().item()
                if probs[0, i, best_id].item() > 0.90 and best_id != orig_id:
                    ids[i] = best_id
        return self.tokenizer.decode(ids, skip_special_tokens=True)

"""
Complete Kaithi Script to Hindi (Devanagari) Transliteration Engine
Unicode Kaithi Block: U+11080-U+110CF
Unicode Devanagari:   U+0900-U+097F
"""
import unicodedata
import re
from typing import Optional, List, Tuple, Dict
from loguru import logger

# ═══════════════════════════════════════════════════════════════════════════════
# COMPLETE KAITHI TO DEVANAGARI CHARACTER MAP
# ═══════════════════════════════════════════════════════════════════════════════

KAITHI_TO_DEVANAGARI: Dict[str, str] = {
    # Independent Vowels
    "\U00011083": "अ",
    "\U00011084": "आ",
    "\U00011085": "इ",
    "\U00011086": "ई",
    "\U00011087": "उ",
    "\U00011088": "ऊ",
    "\U00011089": "ऋ",
    "\U0001108A": "ए",
    "\U0001108B": "ऐ",
    "\U0001108C": "ओ",
    "\U0001108D": "औ",

    # Consonants
    "\U0001108F": "क",
    "\U00011090": "ख",
    "\U00011091": "ग",
    "\U00011092": "घ",
    "\U00011093": "ङ",
    "\U00011094": "च",
    "\U00011095": "छ",
    "\U00011096": "ज",
    "\U00011097": "झ",
    "\U00011098": "ञ",
    "\U00011099": "ट",
    "\U0001109A": "ठ",
    "\U0001109B": "ड",
    "\U0001109C": "ढ",
    "\U0001109D": "ण",
    "\U0001109E": "त",
    "\U0001109F": "थ",
    "\U000110A0": "द",
    "\U000110A1": "ध",
    "\U000110A2": "न",
    "\U000110A3": "प",
    "\U000110A4": "फ",
    "\U000110A5": "ब",
    "\U000110A6": "भ",
    "\U000110A7": "म",
    "\U000110A8": "य",
    "\U000110A9": "र",
    "\U000110AA": "ल",
    "\U000110AB": "व",
    "\U000110AC": "श",
    "\U000110AD": "ष",
    "\U000110AE": "स",
    "\U000110AF": "ह",

    # Dependent Vowel Signs (Matras)
    "\U000110B0": "ा",
    "\U000110B1": "ि",
    "\U000110B2": "ी",
    "\U000110B3": "ु",
    "\U000110B4": "ू",
    "\U000110B5": "े",
    "\U000110B6": "ै",
    "\U000110B7": "ो",
    "\U000110B8": "ौ",

    # Special Signs
    "\U000110B9": "्",
    "\U000110BA": "़",
    "\U000110BB": "ँ",
    "\U000110BC": "ं",
    "\U000110BD": "ः",
    "\U000110BE": "।",
    "\U000110BF": "॥",
    "\U000110C0": ".",
    "\U000110C1": "़",

    # Numerals
    "\U000110F0": "०",
    "\U000110F1": "१",
    "\U000110F2": "२",
    "\U000110F3": "३",
    "\U000110F4": "४",
    "\U000110F5": "५",
    "\U000110F6": "६",
    "\U000110F7": "७",
    "\U000110F8": "८",
    "\U000110F9": "९",
}

KAITHI_CONJUNCTS: Dict[str, str] = {
    "\U0001108F\U000110B9\U00011094": "क्च",
    "\U0001108F\U000110B9\U0001108F": "क्क",
    "\U0001108F\U000110B9\U000110AE": "क्स",
    "\U0001108F\U000110B9\U000110A9": "क्र",
    "\U0001108F\U000110B9\U000110AB": "क्व",
    "\U0001108F\U000110B9\U000110AA": "क्ल",
    "\U000110AE\U000110B9\U000110A9": "स्र",
    "\U000110AE\U000110B9\U000110AA": "स्ल",
    "\U000110AE\U000110B9\U000110AB": "स्व",
    "\U000110AE\U000110B9\U000110AE": "स्स",
    "\U0001109E\U000110B9\U000110A9": "त्र",
    "\U0001109E\U000110B9\U000110AB": "त्व",
    "\U0001109E\U000110B9\U000110AE": "त्स",
    "\U000110A2\U000110B9\U000110A2": "न्न",
    "\U000110A7\U000110B9\U000110A7": "म्म",
}

REGIONAL_VARIANTS: Dict[str, Dict[str, str]] = {
    "standard": {},
    "tirhut": {
        "\U0001108F\U000110AC": "क्ष",
        "\U0001109E\U000110B9\U0001109E": "त्त",
        "\U000110A2\U000110B9\U000110A2": "न्न",
    },
    "bhojpur": {
        "\U00011099\U000110BA": "ड़",
        "\U000110A9\U000110BA": "ऱ",
    },
    "magadh": {
        "\U0001109E\U000110B9\U0001109B": "त्ड",
        "\U000110A2\U000110B9\U000110A9": "न्र",
    },
    "mithila": {
        "\U000110B5\U000110B0": "ेआ",
        "\U000110B5\U000110B1": "एि",
    },
}

LAND_RECORD_VOCAB: Dict[str, List[str]] = {
    "खेत":       ["खेट", "खेद", "खेत्र"],
    "जमीन":      ["जमीं", "ज़मीन", "जमीना"],
    "बीघा":      ["बीगा", "बिघा", "बीगहा"],
    "खाता":      ["खाटा", "खात", "खात्र"],
    "मालगुजारी": ["मालगुज़ारी", "मालगुजारि"],
    "रैयत":      ["रइयत", "रयत", "रियत"],
    "जमींदार":   ["जमिंदार", "ज़मींदार"],
    "परगना":     ["परगाना", "परगानह"],
    "तहसील":     ["तसील", "तहसिल"],
    "मौजा":      ["मौज़ा", "मोजा"],
    "चकबंदी":    ["चकबन्दी", "चकबंदि"],
    "पट्टा":     ["पटा", "पट"],
    "लगान":      ["लगाण", "लगाना"],
    "ऋण":        ["रिण", "रण"],
    "सर्वे":     ["सर्व"],
    "खसरा":      ["खसर", "खसरह"],
    "खतौनी":     ["खतोनी", "खतौनि"],
    "पैमाइश":    ["पैमाइस", "पैमायश"],
    "बंदोबस्त":  ["बंदोबस्ट"],
    "रकबा":      ["रकब", "रकबह"],
    "नंबर":      ["नम्बर", "नंबरह"],
    "सीमा":      ["सिमा", "सीम"],
    "हदबंदी":    ["हदबन्दी"],
    "दाखिल":     ["दाखिला", "दाखल"],
    "खारिज":     ["खारिज़", "खारज"],
    "फर्द":      ["फर्ड", "फर्दह"],
    "मिसल":      ["मिसाल", "मिसलह"],
    "अर्जी":     ["अरजी", "अर्जि"],
}

KEYBOARD_LAYOUT = {
    "vowels": [
        {"k": "\U00011083", "d": "अ",  "l": "A"},
        {"k": "\U00011084", "d": "आ",  "l": "AA"},
        {"k": "\U00011085", "d": "इ",  "l": "I"},
        {"k": "\U00011086", "d": "ई",  "l": "II"},
        {"k": "\U00011087", "d": "उ",  "l": "U"},
        {"k": "\U00011088", "d": "ऊ",  "l": "UU"},
        {"k": "\U00011089", "d": "ऋ",  "l": "RI"},
        {"k": "\U0001108A", "d": "ए",  "l": "E"},
        {"k": "\U0001108B", "d": "ऐ",  "l": "AI"},
        {"k": "\U0001108C", "d": "ओ",  "l": "O"},
        {"k": "\U0001108D", "d": "औ",  "l": "AU"},
    ],
    "consonants": [
        {"k": "\U0001108F", "d": "क",  "l": "KA"},
        {"k": "\U00011090", "d": "ख",  "l": "KHA"},
        {"k": "\U00011091", "d": "ग",  "l": "GA"},
        {"k": "\U00011092", "d": "घ",  "l": "GHA"},
        {"k": "\U00011093", "d": "ङ",  "l": "NGA"},
        {"k": "\U00011094", "d": "च",  "l": "CA"},
        {"k": "\U00011095", "d": "छ",  "l": "CHA"},
        {"k": "\U00011096", "d": "ज",  "l": "JA"},
        {"k": "\U00011097", "d": "झ",  "l": "JHA"},
        {"k": "\U00011098", "d": "ञ",  "l": "NYA"},
        {"k": "\U00011099", "d": "ट",  "l": "TTA"},
        {"k": "\U0001109A", "d": "ठ",  "l": "TTHA"},
        {"k": "\U0001109B", "d": "ड",  "l": "DDA"},
        {"k": "\U0001109C", "d": "ढ",  "l": "DDHA"},
        {"k": "\U0001109D", "d": "ण",  "l": "NNA"},
        {"k": "\U0001109E", "d": "त",  "l": "TA"},
        {"k": "\U0001109F", "d": "थ",  "l": "THA"},
        {"k": "\U000110A0", "d": "द",  "l": "DA"},
        {"k": "\U000110A1", "d": "ध",  "l": "DHA"},
        {"k": "\U000110A2", "d": "न",  "l": "NA"},
        {"k": "\U000110A3", "d": "प",  "l": "PA"},
        {"k": "\U000110A4", "d": "फ",  "l": "PHA"},
        {"k": "\U000110A5", "d": "ब",  "l": "BA"},
        {"k": "\U000110A6", "d": "भ",  "l": "BHA"},
        {"k": "\U000110A7", "d": "म",  "l": "MA"},
        {"k": "\U000110A8", "d": "य",  "l": "YA"},
        {"k": "\U000110A9", "d": "र",  "l": "RA"},
        {"k": "\U000110AA", "d": "ल",  "l": "LA"},
        {"k": "\U000110AB", "d": "व",  "l": "VA"},
        {"k": "\U000110AC", "d": "श",  "l": "SHA"},
        {"k": "\U000110AD", "d": "ष",  "l": "SSA"},
        {"k": "\U000110AE", "d": "स",  "l": "SA"},
        {"k": "\U000110AF", "d": "ह",  "l": "HA"},
    ],
    "vowel_signs": [
        {"k": "\U000110B0", "d": "ा",  "l": "AA-M"},
        {"k": "\U000110B1", "d": "ि",  "l": "I-M"},
        {"k": "\U000110B2", "d": "ी",  "l": "II-M"},
        {"k": "\U000110B3", "d": "ु",  "l": "U-M"},
        {"k": "\U000110B4", "d": "ू",  "l": "UU-M"},
        {"k": "\U000110B5", "d": "े",  "l": "E-M"},
        {"k": "\U000110B6", "d": "ै",  "l": "AI-M"},
        {"k": "\U000110B7", "d": "ो",  "l": "O-M"},
        {"k": "\U000110B8", "d": "ौ",  "l": "AU-M"},
        {"k": "\U000110B9", "d": "्",  "l": "HAL"},
        {"k": "\U000110BC", "d": "ं",  "l": "ANU"},
        {"k": "\U000110BB", "d": "ँ",  "l": "CBI"},
        {"k": "\U000110BD", "d": "ः",  "l": "VIS"},
    ],
    "numerals": [
        {"k": "\U000110F0", "d": "०",  "l": "0"},
        {"k": "\U000110F1", "d": "१",  "l": "1"},
        {"k": "\U000110F2", "d": "२",  "l": "2"},
        {"k": "\U000110F3", "d": "३",  "l": "3"},
        {"k": "\U000110F4", "d": "४",  "l": "4"},
        {"k": "\U000110F5", "d": "५",  "l": "5"},
        {"k": "\U000110F6", "d": "६",  "l": "6"},
        {"k": "\U000110F7", "d": "७",  "l": "7"},
        {"k": "\U000110F8", "d": "८",  "l": "8"},
        {"k": "\U000110F9", "d": "९",  "l": "9"},
    ],
    "punctuation": [
        {"k": "\U000110BE", "d": "।",  "l": "DAN"},
        {"k": "\U000110BF", "d": "॥",  "l": "DDN"},
        {"k": " ",          "d": " ",  "l": "SPC"},
    ],
}

DEVANAGARI_TO_KAITHI: Dict[str, str] = {}
for _k, _v in KAITHI_TO_DEVANAGARI.items():
    if _v not in DEVANAGARI_TO_KAITHI:
        DEVANAGARI_TO_KAITHI[_v] = _k


class KaithiTransliterator:
    def __init__(self, region: str = "standard"):
        self.region = region if region in REGIONAL_VARIANTS else "standard"
        self.char_map = dict(KAITHI_TO_DEVANAGARI)
        self.conjunct_map = dict(KAITHI_CONJUNCTS)
        self.regional_map = REGIONAL_VARIANTS.get(self.region, {})

    def transliterate(self, kaithi_text: str) -> Dict:
        if not kaithi_text or not kaithi_text.strip():
            return {"hindi": "", "confidence": 1.0, "char_mappings": [], "region": self.region}

        text = self._apply_regional_variants(kaithi_text)
        text, conjunct_hits = self._resolve_conjuncts(text)
        hindi, char_mappings = self._map_characters(text)
        hindi = self._fix_matra_order(hindi)
        hindi = self._apply_halant_rules(hindi)
        hindi = unicodedata.normalize("NFC", hindi)
        hindi = self._apply_vocab_correction(hindi)
        hindi = self._cleanup(hindi)
        confidence = self._score_confidence(char_mappings)

        return {
            "hindi": hindi,
            "confidence": confidence,
            "char_mappings": char_mappings,
            "conjunct_hits": conjunct_hits,
            "region": self.region,
        }

    def transliterate_text(self, text: str) -> str:
        return self.transliterate(text)["hindi"]

    def _apply_regional_variants(self, text: str) -> str:
        for variant, standard in self.regional_map.items():
            text = text.replace(variant, standard)
        return text

    def _resolve_conjuncts(self, text: str) -> Tuple[str, int]:
        hits = 0
        for seq, conj in sorted(self.conjunct_map.items(), key=lambda x: -len(x[0])):
            if seq in text:
                text = text.replace(seq, conj)
                hits += 1
        return text, hits

    def _map_characters(self, text: str) -> Tuple[str, List[Dict]]:
        result = []
        mappings = []
        i = 0
        while i < len(text):
            char = text[i]
            cp = ord(char)
            if i + 2 < len(text):
                tri = text[i:i+3]
                if tri in self.char_map:
                    m = self.char_map[tri]
                    result.append(m)
                    mappings.append({"src": tri, "dst": m, "conf": 1.0, "type": "trigram"})
                    i += 3
                    continue
            if i + 1 < len(text):
                bi = text[i:i+2]
                if bi in self.char_map:
                    m = self.char_map[bi]
                    result.append(m)
                    mappings.append({"src": bi, "dst": m, "conf": 1.0, "type": "bigram"})
                    i += 2
                    continue
            if 0x11080 <= cp <= 0x110CF:
                if char in self.char_map:
                    m = self.char_map[char]
                    result.append(m)
                    mappings.append({"src": char, "dst": m, "conf": 1.0, "type": "direct"})
                else:
                    result.append("◌")
                    mappings.append({"src": char, "dst": "◌", "conf": 0.0, "type": "unknown"})
            else:
                result.append(char)
                mappings.append({"src": char, "dst": char, "conf": 1.0, "type": "passthrough"})
            i += 1
        return "".join(result), mappings

    def _fix_matra_order(self, text: str) -> str:
        consonant_range = r"[\u0915-\u0939\u0958-\u095F]"
        text = re.sub(r"(ि)(" + consonant_range + r")", r"\2\1", text)
        return text

    def _apply_halant_rules(self, text: str) -> str:
        text = re.sub(r"(्)\1+", "्", text)
        text = re.sub(r"्(\s|$|।|॥)", r"\1", text)
        text = re.sub(r"([ािीुूेैोौ])्", r"\1", text)
        return text

    def _apply_vocab_correction(self, text: str) -> str:
        words = text.split()
        corrected = []
        for word in words:
            stripped = word.rstrip("।॥,.!?")
            suffix = word[len(stripped):]
            found = False
            for correct, variants in LAND_RECORD_VOCAB.items():
                if stripped in variants:
                    corrected.append(correct + suffix)
                    found = True
                    break
            if not found:
                corrected.append(word)
        return " ".join(corrected)

    def _cleanup(self, text: str) -> str:
        text = re.sub(r" +", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _score_confidence(self, mappings: List[Dict]) -> float:
        if not mappings:
            return 0.0
        return round(sum(m["conf"] for m in mappings) / len(mappings), 4)


class HindiToKaithiConverter:
    def __init__(self):
        self.rev_map = dict(DEVANAGARI_TO_KAITHI)

    def convert(self, hindi_text: str) -> Dict:
        result = []
        mappings = []
        for char in hindi_text:
            if char in self.rev_map:
                k = self.rev_map[char]
                result.append(k)
                mappings.append({"src": char, "dst": k})
            else:
                result.append(char)
                mappings.append({"src": char, "dst": char})
        return {"kaithi": "".join(result), "mappings": mappings}


def get_keyboard_layout() -> Dict:
    return KEYBOARD_LAYOUT

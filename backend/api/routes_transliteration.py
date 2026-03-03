from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from ..models.transliterator import (
    KaithiTransliterator, HindiToKaithiConverter,
    get_keyboard_layout, REGIONAL_VARIANTS, LAND_RECORD_VOCAB, KAITHI_TO_DEVANAGARI
)

router = APIRouter()


class KaithiRequest(BaseModel):
    text: str
    region: Optional[str] = "standard"


class HindiRequest(BaseModel):
    hindi_text: str


@router.post("/kaithi-to-hindi")
async def kaithi_to_hindi(req: KaithiRequest):
    t = KaithiTransliterator(region=req.region or "standard")
    return t.transliterate(req.text)


@router.post("/hindi-to-kaithi")
async def hindi_to_kaithi(req: HindiRequest):
    c = HindiToKaithiConverter()
    return c.convert(req.hindi_text)


@router.get("/keyboard-layout")
async def keyboard_layout():
    return get_keyboard_layout()


@router.get("/regions")
async def list_regions():
    return {
        "regions": [
            {"id": "standard", "name": "Standard Kaithi",       "area": "General"},
            {"id": "tirhut",   "name": "Tirhut / Mithilanchal", "area": "North Bihar"},
            {"id": "bhojpur",  "name": "Bhojpur (Western)",     "area": "West Bihar"},
            {"id": "magadh",   "name": "Magadh (Central)",      "area": "Patna/Gaya"},
            {"id": "mithila",  "name": "Mithila",               "area": "Maithili region"},
        ]
    }


@router.get("/character-map")
async def character_map():
    return {
        "total": len(KAITHI_TO_DEVANAGARI),
        "map": [
            {
                "kaithi":     k,
                "kaithi_cp":  f"U+{ord(k):04X}" if len(k) == 1 else "multi",
                "devanagari": v,
                "deva_cp":    f"U+{ord(v):04X}" if len(v) == 1 else "multi",
            }
            for k, v in KAITHI_TO_DEVANAGARI.items()
        ]
    }


@router.get("/land-record-vocabulary")
async def land_vocab():
    return {
        "total_terms": len(LAND_RECORD_VOCAB),
        "vocabulary": [
            {"correct": k, "variants": v}
            for k, v in LAND_RECORD_VOCAB.items()
        ]
    }

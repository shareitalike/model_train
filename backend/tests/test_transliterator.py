import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.transliterator import (
    KaithiTransliterator, HindiToKaithiConverter,
    KAITHI_TO_DEVANAGARI, LAND_RECORD_VOCAB
)


@pytest.fixture
def t():  return KaithiTransliterator(region="standard")

@pytest.fixture
def rev(): return HindiToKaithiConverter()


# ── Basic ────────────────────────────────────────────────────────────────────

def test_empty_input(t):
    r = t.transliterate("")
    assert r["hindi"] == ""
    assert r["confidence"] == 1.0

def test_whitespace_input(t):
    r = t.transliterate("   ")
    assert r["hindi"].strip() == ""

def test_single_consonant_ka(t):
    r = t.transliterate("\U0001108F")
    assert "क" in r["hindi"]

def test_single_consonant_ma(t):
    r = t.transliterate("\U000110A7")
    assert "म" in r["hindi"]

def test_vowel_aa(t):
    r = t.transliterate("\U00011084")
    assert "आ" in r["hindi"]

def test_matra_ka_aa(t):
    r = t.transliterate("\U0001108F\U000110B0")
    assert "का" in r["hindi"]

def test_danda(t):
    r = t.transliterate("\U000110BE")
    assert "।" in r["hindi"]

def test_double_danda(t):
    r = t.transliterate("\U000110BF")
    assert "॥" in r["hindi"]

def test_space_passthrough(t):
    r = t.transliterate("\U0001108F \U000110A7")
    assert " " in r["hindi"]

def test_ascii_passthrough(t):
    r = t.transliterate("ABC 123")
    assert "ABC" in r["hindi"]

def test_all_numerals(t):
    nums = "".join(chr(0x110F0 + i) for i in range(10))
    r = t.transliterate(nums)
    for d in "०१२३४५६७८९":
        assert d in r["hindi"]


# ── Confidence ───────────────────────────────────────────────────────────────

def test_confidence_all_known(t):
    r = t.transliterate("\U0001108F\U000110A7")
    assert r["confidence"] == 1.0

def test_confidence_range(t):
    r = t.transliterate("\U0001108F\u4e00")
    assert 0.0 <= r["confidence"] <= 1.0


# ── Regions ──────────────────────────────────────────────────────────────────

def test_standard_region():
    t = KaithiTransliterator(region="standard")
    assert t.region == "standard"

def test_tirhut_region():
    t = KaithiTransliterator(region="tirhut")
    assert t.region == "tirhut"

def test_unknown_region_fallback():
    t = KaithiTransliterator(region="xyz")
    assert t.region == "standard"

def test_region_in_result():
    t = KaithiTransliterator(region="tirhut")
    r = t.transliterate("\U0001108F")
    assert r["region"] == "tirhut"


# ── Vocab correction ─────────────────────────────────────────────────────────

def test_vocab_loaded():
    assert len(LAND_RECORD_VOCAB) >= 20

def test_vocab_correction(t):
    text = "खेट बीगा"
    corrected = t._apply_vocab_correction(text)
    assert "खेत" in corrected
    assert "बीघा" in corrected

def test_vocab_correct_unchanged(t):
    text = "खेत बीघा"
    assert t._apply_vocab_correction(text) == text


# ── Halant rules ─────────────────────────────────────────────────────────────

def test_trailing_halant_removed(t):
    r = t._apply_halant_rules("कत्")
    assert not r.endswith("्")

def test_double_halant_collapsed(t):
    r = t._apply_halant_rules("क्् ्")
    assert "् ्" not in r


# ── Reverse ──────────────────────────────────────────────────────────────────

def test_reverse_single_char(rev):
    r = rev.convert("क")
    assert r["kaithi"] == "\U0001108F"

def test_reverse_empty(rev):
    r = rev.convert("")
    assert r["kaithi"] == ""

def test_reverse_unknown_passthrough(rev):
    r = rev.convert("Z")
    assert r["kaithi"] == "Z"


# ── Coverage ─────────────────────────────────────────────────────────────────

def test_all_consonants(t):
    for cp in range(0x1108F, 0x110B0):
        char = chr(cp)
        if char in KAITHI_TO_DEVANAGARI:
            r = t.transliterate(char)
            assert r["hindi"] != ""

def test_all_numerals_mapped(t):
    for cp in range(0x110F0, 0x110FA):
        char = chr(cp)
        r = t.transliterate(char)
        expected = chr(0x0966 + (cp - 0x110F0))
        assert expected in r["hindi"]

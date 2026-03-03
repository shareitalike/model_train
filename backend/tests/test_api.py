import pytest
import json
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="module")
def client():
    from main import app
    with TestClient(app) as c:
        yield c


def minimal_pdf() -> bytes:
    return b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
190
%%EOF"""


SAMPLE = {
    "metadata":   {"total_pages": 1, "region": "standard", "filename": "test.pdf"},
    "overall_confidence": 0.85,
    "full_hindi_text": "यह परीक्षण है।",
    "pages": [{
        "page_number": 1, "kaithi_text": "test", "hindi_text": "यह परीक्षण है।",
        "corrected_text": "यह परीक्षण है।", "confidence": 0.85,
        "word_boxes": [], "line_count": 1,
    }],
}


# ── System ───────────────────────────────────────────────────────────────────

def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"

def test_stats(client):
    r = client.get("/api/v1/stats")
    assert r.status_code == 200
    assert "total_documents" in r.json()

def test_swagger_docs(client):
    r = client.get("/api/docs")
    assert r.status_code == 200

def test_openapi(client):
    r = client.get("/api/openapi.json")
    assert r.status_code == 200
    assert "paths" in r.json()


# ── Transliteration ──────────────────────────────────────────────────────────

def test_kaithi_to_hindi(client):
    r = client.post("/api/v1/transliterate/kaithi-to-hindi",
                    json={"text": "\U0001108F\U000110A7", "region": "standard"})
    assert r.status_code == 200
    d = r.json()
    assert "hindi" in d
    assert "क" in d["hindi"]
    assert "म" in d["hindi"]

def test_hindi_to_kaithi(client):
    r = client.post("/api/v1/transliterate/hindi-to-kaithi",
                    json={"hindi_text": "क"})
    assert r.status_code == 200
    assert "\U0001108F" in r.json()["kaithi"]

def test_keyboard_layout(client):
    r = client.get("/api/v1/transliterate/keyboard-layout")
    assert r.status_code == 200
    d = r.json()
    assert "consonants" in d

def test_character_map(client):
    r = client.get("/api/v1/transliterate/character-map")
    assert r.status_code == 200
    assert r.json()["total"] > 50

def test_regions_list(client):
    r = client.get("/api/v1/transliterate/regions")
    assert r.status_code == 200
    assert len(r.json()["regions"]) == 5

def test_land_vocab(client):
    r = client.get("/api/v1/transliterate/land-record-vocabulary")
    assert r.status_code == 200
    assert r.json()["total_terms"] >= 20


# ── OCR ──────────────────────────────────────────────────────────────────────

def test_upload_invalid_type(client):
    r = client.post("/api/v1/ocr/upload",
                    files={"file": ("test.txt", b"not a pdf", "text/plain")})
    assert r.status_code == 400

def test_process_sync_invalid(client):
    r = client.post("/api/v1/ocr/process-sync",
                    files={"file": ("test.txt", b"not pdf", "text/plain")})
    assert r.status_code == 400

def test_status_not_found(client):
    r = client.get("/api/v1/ocr/status/nonexistent-id")
    assert r.status_code == 404


# ── Export ───────────────────────────────────────────────────────────────────

def test_export_json(client):
    r = client.post("/api/v1/export/download",
                    json={"result_data": SAMPLE, "format": "json"})
    assert r.status_code == 200
    assert "application/json" in r.headers["content-type"]
    assert "full_hindi_text" in r.json()

def test_export_txt(client):
    r = client.post("/api/v1/export/download",
                    json={"result_data": SAMPLE, "format": "txt"})
    assert r.status_code == 200
    assert "text/plain" in r.headers["content-type"]
    assert "परीक्षण" in r.text

def test_export_pdf(client):
    r = client.post("/api/v1/export/download",
                    json={"result_data": SAMPLE, "format": "pdf"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"

def test_export_docx(client):
    r = client.post("/api/v1/export/download",
                    json={"result_data": SAMPLE, "format": "docx"})
    assert r.status_code == 200
    assert "officedocument" in r.headers["content-type"]
    assert r.content[:2] == b"PK"

def test_export_invalid_format(client):
    r = client.post("/api/v1/export/download",
                    json={"result_data": SAMPLE, "format": "xyz"})
    assert r.status_code == 400


# ── Search ───────────────────────────────────────────────────────────────────

def test_search_empty(client):
    r = client.get("/api/v1/search?q=")
    assert r.status_code in [400, 422]

def test_search_valid(client):
    r = client.get("/api/v1/search?q=खेत")
    assert r.status_code == 200
    d = r.json()
    assert "results" in d
    assert "total" in d
    assert d["query"] == "खेत"

def test_search_suggestions(client):
    r = client.get("/api/v1/search/suggestions?q=खेत")
    assert r.status_code == 200
    assert "suggestions" in r.json()

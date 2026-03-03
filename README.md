# 🏛️ कैथी OCR सिस्टम — Kaithi Lipi Digitization Platform

Government-grade system for converting handwritten Kaithi manuscripts to searchable Hindi (Devanagari Unicode).

## Quick Start

```bash
git clone https://github.com/your-org/kaithi-ocr
cd kaithi-ocr
cp backend/.env.example backend/.env
# Edit .env and change SECRET_KEY to a secure value
make up
```

Open **http://localhost** in your browser.

## Services

| Service      | URL                       | Purpose                    |
|--------------|---------------------------|----------------------------|
| Frontend     | http://localhost          | React Web UI               |
| API Docs     | http://localhost/api/docs | Swagger / OpenAPI          |
| MinIO        | http://localhost:9001     | File storage console       |
| Flower       | http://localhost:5555     | Celery task monitor        |

## Features

- **PDF OCR** — Upload handwritten Kaithi PDFs → searchable Hindi Unicode
- **Real-time Transliteration** — Kaithi ↔ Hindi bidirectional
- **5 Regional Variants** — Standard, Tirhut, Bhojpur, Magadh, Mithila
- **Confidence Scoring** — Word-level confidence heatmap
- **Exports** — Searchable PDF, DOCX, JSON, Plain Text
- **Virtual Keyboard** — Compose Kaithi text in browser
- **Full-text Search** — Search inside processed documents
- **Land Record Vocabulary** — 30+ domain-specific corrections

## Project Structure

```
kaithi-ocr/
├── backend/
│   ├── main.py               # FastAPI application entry point
│   ├── core/                 # Config, database, security, storage
│   ├── models/               # OCR pipeline, TrOCR, transliterator
│   ├── api/                  # Route handlers (OCR, export, users, search)
│   ├── exports/              # PDF, DOCX exporters
│   ├── tasks/                # Celery async tasks
│   └── tests/                # Unit + integration tests
├── frontend/
│   └── src/
│       ├── App.jsx            # Main application
│       ├── components/        # React components
│       └── utils/             # API client, keyboard data
├── training/
│   ├── train_trocr.py         # TrOCR fine-tuning
│   ├── synthetic_data_gen.py  # Synthetic dataset generator
│   └── evaluate.py            # Model evaluation
├── docker/                    # Nginx configs
├── scripts/                   # DB init, health check
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
├── docker-compose.gpu.yml
└── Makefile
```

## Training Custom Model

```bash
# 1. Generate 10,000 synthetic training samples
make synth-data

# 2. Fine-tune TrOCR (30 epochs — target CER < 5%)
make train

# 3. Evaluate
make eval
```

## API Usage

```python
import requests

# Transliterate Kaithi to Hindi (real-time)
resp = requests.post("http://localhost/api/v1/transliterate/kaithi-to-hindi",
    json={"text": "\U0001108F\U000110A7", "region": "standard"})
print(resp.json()["hindi"])  # → "कम"

# Upload PDF for async OCR
with open("document.pdf", "rb") as f:
    resp = requests.post("http://localhost/api/v1/ocr/upload?region=tirhut",
                         files={"file": f})
doc_id = resp.json()["doc_id"]

# Poll for result
import time
while True:
    status = requests.get(f"http://localhost/api/v1/ocr/status/{doc_id}").json()
    if status["status"] == "completed":
        print(status["full_hindi_text"])
        break
    time.sleep(3)
```

## Hardware Requirements

| Environment    | Spec                          | Speed       |
|----------------|-------------------------------|-------------|
| Development    | 4 CPU, 16GB RAM               | ~45s/page   |
| Production CPU | c5.2xlarge (8 CPU, 16GB)     | ~25s/page   |
| Production GPU | g4dn.xlarge (T4 GPU, 16GB)   | ~8s/page    |
| High Volume    | g4dn.2xlarge (V100 GPU)      | ~4s/page    |

## GPU Deployment

```bash
make prod-gpu
```

Requires NVIDIA Container Toolkit installed on host.

## Security Notes

Before production deployment:
1. Change `SECRET_KEY` in `.env` to a strong 256-bit random value: `openssl rand -hex 32`
2. Change `MINIO_SECRET_KEY` to a strong password
3. Set `DEBUG=false`
4. Restrict CORS origins in `backend/main.py` to your domain
5. Enable SSL/TLS (certificates in `docker/ssl/`)

## License

Government Open Data License (GODL) — India  
https://data.gov.in/government-open-data-license-india

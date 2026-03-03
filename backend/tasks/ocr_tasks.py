from celery import current_task
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger
import os

from .celery_app import celery_app

DATABASE_SYNC_URL = os.environ.get(
    "DATABASE_SYNC_URL",
    "postgresql://kaithi:kaithi123@postgres:5432/kaithi_db"
)

sync_engine = create_engine(DATABASE_SYNC_URL, pool_pre_ping=True)
SyncSession = sessionmaker(bind=sync_engine)


@celery_app.task(bind=True, name="tasks.process_pdf", max_retries=2)
def process_pdf_task(self, doc_id: str, storage_path: str, region: str):
    db = SyncSession()
    try:
        from core.database import Document, OCRResult, Base
        Base.metadata.create_all(sync_engine)

        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise ValueError(f"Document {doc_id} not found")

        doc.status = "processing"
        db.commit()

        from core.storage import download_file
        pdf_bytes = download_file(storage_path)

        def on_progress(pct):
            self.update_state(state="PROGRESS", meta={"current": pct, "total": 100})

        from models.ocr_pipeline import KaithiOCRPipeline
        pipeline = KaithiOCRPipeline(region=region)
        result = pipeline.process_pdf_bytes(pdf_bytes, progress_callback=on_progress)

        for page in result.pages:
            ocr = OCRResult(
                document_id=doc_id,
                page_number=page.page_number,
                kaithi_text=page.kaithi_text,
                hindi_text=page.hindi_text,
                corrected_text=page.corrected_text,
                confidence_overall=page.confidence,
                confidence_scores={"overall": page.confidence},
                word_boxes=page.word_boxes,
                line_count=page.line_count,
                processing_time_ms=page.processing_time_ms,
            )
            db.add(ocr)

        doc.status = "completed"
        doc.page_count = result.total_pages
        doc.completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"[Task] Completed doc={doc_id} pages={result.total_pages}")
        return {"doc_id": doc_id, "status": "completed", "pages": result.total_pages}

    except Exception as exc:
        logger.error(f"[Task] Failed doc={doc_id}: {exc}")
        try:
            from core.database import Document
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc:
                doc.status = "failed"
                doc.error_message = str(exc)
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()

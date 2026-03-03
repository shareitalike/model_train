from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import uuid
from datetime import datetime
from loguru import logger

from ..core.config import get_settings
from ..core.database import get_db, Document, OCRResult, User
from ..core.security import get_optional_user
from ..core.storage import upload_file as storage_upload, download_file

settings = get_settings()
router = APIRouter()


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    region: str = Query("standard"),
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(413, f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit")

    doc_id = str(uuid.uuid4())
    storage_path = f"uploads/{doc_id}/{file.filename}"

    try:
        storage_upload(content, storage_path, "application/pdf")
    except Exception as e:
        logger.error(f"Storage upload failed: {e}")
        raise HTTPException(500, "File storage failed")

    doc = Document(
        id=doc_id,
        user_id=user.id if user else "anonymous",
        original_filename=file.filename,
        storage_path=storage_path,
        status="queued",
        region_variant=region,
        file_size_bytes=len(content),
    )
    db.add(doc)
    await db.commit()

    from ..tasks.ocr_tasks import process_pdf_task
    task = process_pdf_task.delay(doc_id=doc_id, storage_path=storage_path, region=region)

    await db.execute(update(Document).where(Document.id == doc_id).values(task_id=task.id))
    await db.commit()

    return {
        "doc_id": doc_id,
        "task_id": task.id,
        "status": "queued",
        "filename": file.filename,
        "size_mb": round(size_mb, 2),
        "region": region,
        "estimated_s": max(15, int(size_mb * 20)),
    }


@router.post("/process-sync")
async def process_sync(
    file: UploadFile = File(...),
    region: str = Query("standard"),
):
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, "Use /upload for files >5MB")
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted")
    from ..models.ocr_pipeline import KaithiOCRPipeline
    pipeline = KaithiOCRPipeline(region=region)
    result = pipeline.process_pdf_bytes(content)
    return result.to_dict()


@router.get("/status/{doc_id}")
async def get_status(doc_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")

    response = {
        "doc_id": doc.id,
        "status": doc.status,
        "filename": doc.original_filename,
        "region": doc.region_variant,
        "created": doc.created_at.isoformat() if doc.created_at else None,
    }

    if doc.status == "completed":
        pages_result = await db.execute(
            select(OCRResult).where(OCRResult.document_id == doc_id)
        )
        pages = pages_result.scalars().all()
        response["pages"] = [
            {
                "page_number": p.page_number,
                "kaithi_text": p.kaithi_text,
                "hindi_text": p.hindi_text,
                "corrected_text": p.corrected_text,
                "confidence": p.confidence_overall,
                "word_boxes": p.word_boxes,
                "line_count": p.line_count,
            }
            for p in sorted(pages, key=lambda x: x.page_number)
        ]
        response["full_hindi_text"] = "\n\n".join(
            p.get("corrected_text") or p.get("hindi_text", "")
            for p in response["pages"]
        )
        response["overall_confidence"] = (
            sum(p.get("confidence") or 0 for p in response["pages"]) /
            max(1, len(response["pages"]))
        )
        response["metadata"] = {
            "total_pages": doc.page_count,
            "region": doc.region_variant,
            "filename": doc.original_filename,
        }
    elif doc.status == "failed":
        response["error"] = doc.error_message

    return response


@router.post("/feedback/{ocr_result_id}")
async def submit_feedback(
    ocr_result_id: str,
    corrected_text: str,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    from ..core.database import CorrectionFeedback
    result = await db.execute(select(OCRResult).where(OCRResult.id == ocr_result_id))
    ocr = result.scalar_one_or_none()
    if not ocr:
        raise HTTPException(404, "OCR result not found")
    feedback = CorrectionFeedback(
        ocr_result_id=ocr_result_id,
        user_id=user.id if user else "anonymous",
        original_text=ocr.hindi_text or "",
        corrected_text=corrected_text,
    )
    db.add(feedback)
    await db.commit()
    return {"status": "feedback_recorded", "id": feedback.id}


@router.post("/process-image")
async def process_image(
    file: UploadFile = File(...),
    region: str = Query("standard"),
):
    content = await file.read()
    from ..models.ocr_pipeline import KaithiOCRPipeline
    pipeline = KaithiOCRPipeline(region=region)
    result = pipeline.process_image_bytes(content)
    return {
        "page_number": result.page_number,
        "kaithi_text": result.kaithi_text,
        "hindi_text": result.hindi_text,
        "corrected_text": result.corrected_text,
        "confidence": result.confidence,
        "line_count": result.line_count,
    }

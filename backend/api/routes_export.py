from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db, Document, OCRResult
from ..exports.pdf_exporter import PDFExporter
from ..exports.docx_exporter import DocxExporter

router = APIRouter()


class ExportRequest(BaseModel):
    result_data: dict
    format: str
    include_confidence: Optional[bool] = True
    filename_prefix: Optional[str] = "kaithi_ocr"


@router.post("/download")
async def export_download(req: ExportRequest):
    fmt = req.format.lower().strip()
    prefix = req.filename_prefix or "kaithi_ocr"

    if fmt == "pdf":
        data = PDFExporter().export(req.result_data, req.include_confidence)
        return Response(content=data, media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="{prefix}.pdf"'})
    elif fmt == "docx":
        data = DocxExporter().export(req.result_data)
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{prefix}.docx"'}
        )
    elif fmt == "json":
        data = json.dumps(req.result_data, ensure_ascii=False, indent=2).encode("utf-8")
        return Response(content=data, media_type="application/json; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{prefix}.json"'})
    elif fmt in ("txt", "text"):
        text = req.result_data.get("full_hindi_text", "")
        if not text:
            text = "\n\n".join(
                p.get("corrected_text") or p.get("hindi_text", "")
                for p in req.result_data.get("pages", [])
            )
        return Response(content=text.encode("utf-8"), media_type="text/plain; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{prefix}.txt"'})
    else:
        raise HTTPException(400, f"Unsupported format: {fmt}")


@router.get("/document/{doc_id}/{format}")
async def export_by_doc_id(doc_id: str, format: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.status != "completed":
        raise HTTPException(400, f"Document status is '{doc.status}'")

    pages_result = await db.execute(
        select(OCRResult).where(OCRResult.document_id == doc_id).order_by(OCRResult.page_number)
    )
    pages = pages_result.scalars().all()
    result_data = {
        "metadata": {"total_pages": doc.page_count, "region": doc.region_variant,
                     "filename": doc.original_filename},
        "overall_confidence": sum(p.confidence_overall or 0 for p in pages) / max(1, len(pages)),
        "pages": [
            {"page_number": p.page_number, "kaithi_text": p.kaithi_text,
             "hindi_text": p.hindi_text, "corrected_text": p.corrected_text,
             "confidence": p.confidence_overall, "word_boxes": p.word_boxes,
             "line_count": p.line_count}
            for p in pages
        ],
        "full_hindi_text": "\n\n".join(p.corrected_text or p.hindi_text or "" for p in pages),
    }
    req = ExportRequest(
        result_data=result_data, format=format,
        filename_prefix=doc.original_filename.replace(".pdf", "")
    )
    return await export_download(req)

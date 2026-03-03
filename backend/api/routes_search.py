from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from ..core.database import get_db, OCRResult, Document

router = APIRouter()


@router.get("")
async def search_documents(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    region: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    if not q.strip():
        raise HTTPException(400, "Search query cannot be empty")
    offset = (page - 1) * limit
    pattern = f"%{q.strip()}%"
    query = (
        select(OCRResult.id, OCRResult.document_id, OCRResult.page_number,
               OCRResult.corrected_text, OCRResult.hindi_text, OCRResult.confidence_overall,
               Document.original_filename, Document.region_variant, Document.created_at)
        .join(Document, Document.id == OCRResult.document_id)
        .where(
            (OCRResult.corrected_text.ilike(pattern)) | (OCRResult.hindi_text.ilike(pattern))
        )
        .where(Document.status == "completed")
        .order_by(OCRResult.confidence_overall.desc())
        .offset(offset).limit(limit)
    )
    if region:
        query = query.where(Document.region_variant == region)

    rows = (await db.execute(query)).all()
    count_q = (
        select(func.count()).select_from(OCRResult)
        .join(Document, Document.id == OCRResult.document_id)
        .where(
            (OCRResult.corrected_text.ilike(pattern)) | (OCRResult.hindi_text.ilike(pattern))
        )
        .where(Document.status == "completed")
    )
    total = (await db.execute(count_q)).scalar() or 0

    results = []
    for row in rows:
        body = row.corrected_text or row.hindi_text or ""
        snippet = _extract_snippet(body, q)
        results.append({
            "id": row.id, "doc_id": row.document_id,
            "page_number": row.page_number, "filename": row.original_filename,
            "region": row.region_variant, "confidence": row.confidence_overall,
            "snippet": snippet,
            "created": row.created_at.isoformat() if row.created_at else None,
        })

    return {"query": q, "total": total, "page": page, "limit": limit,
            "pages": (total + limit - 1) // limit, "results": results}


@router.get("/suggestions")
async def search_suggestions(q: str = Query(..., min_length=1), db: AsyncSession = Depends(get_db)):
    pattern = f"%{q.strip()}%"
    result = await db.execute(
        select(OCRResult.corrected_text).where(OCRResult.corrected_text.ilike(pattern)).limit(10)
    )
    rows = result.scalars().all()
    suggestions = set()
    for text_content in rows:
        if not text_content:
            continue
        for word in text_content.split():
            if q.lower() in word.lower() and len(word) > 1:
                suggestions.add(word.strip("।॥,.!?"))
                if len(suggestions) >= 8:
                    break
    return {"query": q, "suggestions": list(suggestions)[:8]}


def _extract_snippet(text: str, query: str, window: int = 120) -> str:
    if not text:
        return ""
    idx = text.lower().find(query.lower())
    if idx == -1:
        return text[:window] + ("..." if len(text) > window else "")
    start = max(0, idx - window // 2)
    end = min(len(text), idx + len(query) + window // 2)
    snippet = ("..." if start > 0 else "") + text[start:end] + ("..." if end < len(text) else "")
    return snippet

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger
import sys
import time

from core.config import get_settings
from core.database import init_db
from api.routes_ocr import router as ocr_router
from api.routes_transliteration import router as trans_router
from api.routes_export import router as export_router
from api.routes_user import router as user_router
from api.routes_search import router as search_router

settings = get_settings()

logger.remove()
logger.add(sys.stdout, level="INFO",
           format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
           colorize=True)
logger.add("/app/logs/kaithi_{time:YYYY-MM-DD}.log", rotation="100 MB",
           retention="30 days", level="DEBUG", encoding="utf-8", compression="gz")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    await init_db()
    logger.info("Database initialized")
    try:
        from core.storage import get_minio_client
        get_minio_client()
        logger.info("MinIO storage ready")
    except Exception as e:
        logger.warning(f"MinIO not available: {e}")
    yield
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    description="Government-Grade Kaithi Lipi → Hindi Digitization API",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(CORSMiddleware,
                   allow_origins=["*"],
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"])
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(f"{request.method} {request.url.path} → {response.status_code} [{ms:.1f}ms]")
    response.headers["X-Process-Time-Ms"] = f"{ms:.1f}"
    return response


@app.exception_handler(404)
async def not_found(request: Request, exc):
    return JSONResponse(status_code=404, content={"error": "Not found", "path": str(request.url.path)})


@app.exception_handler(Exception)
async def global_exc(request: Request, exc: Exception):
    logger.exception(f"Unhandled: {exc}")
    return JSONResponse(status_code=500, content={"error": "Internal server error", "detail": str(exc)})


p = settings.API_PREFIX
app.include_router(ocr_router,    prefix=f"{p}/ocr",           tags=["OCR"])
app.include_router(trans_router,  prefix=f"{p}/transliterate", tags=["Transliteration"])
app.include_router(export_router, prefix=f"{p}/export",        tags=["Export"])
app.include_router(user_router,   prefix=f"{p}/users",         tags=["Users"])
app.include_router(search_router, prefix=f"{p}/search",        tags=["Search"])


@app.get(f"{p}/health", tags=["System"])
async def health():
    import torch
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "app": settings.APP_NAME,
        "gpu": torch.cuda.is_available(),
    }


@app.get(f"{p}/stats", tags=["System"])
async def stats():
    from core.database import AsyncSessionLocal, Document, OCRResult
    from sqlalchemy import func, select
    async with AsyncSessionLocal() as db:
        total = (await db.execute(select(func.count(Document.id)))).scalar() or 0
        done  = (await db.execute(
            select(func.count(Document.id)).where(Document.status == "completed")
        )).scalar() or 0
        avg_c = (await db.execute(select(func.avg(OCRResult.confidence_overall)))).scalar()
    return {"total_documents": total, "completed": done,
            "avg_confidence": round(float(avg_c or 0), 4)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)

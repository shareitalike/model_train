from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Text,
    ForeignKey, JSON, Boolean
)
from sqlalchemy.sql import func
from .config import get_settings
import uuid

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    department = Column(String(255), nullable=True)
    designation = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    api_key = Column(String(64), unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    documents = relationship("Document", back_populates="user", lazy="select")


class Document(Base):
    __tablename__ = "documents"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    original_filename = Column(String(512), nullable=False)
    storage_path = Column(String(512), nullable=False)
    status = Column(String(32), default="pending", index=True)
    page_count = Column(Integer, default=0)
    region_variant = Column(String(32), default="standard")
    file_size_bytes = Column(Integer, nullable=True)
    task_id = Column(String(36), nullable=True, index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    user = relationship("User", back_populates="documents")
    ocr_results = relationship("OCRResult", back_populates="document", lazy="select")


class OCRResult(Base):
    __tablename__ = "ocr_results"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    kaithi_text = Column(Text, nullable=True)
    hindi_text = Column(Text, nullable=True)
    corrected_text = Column(Text, nullable=True)
    confidence_overall = Column(Float, nullable=True)
    confidence_scores = Column(JSON, nullable=True)
    word_boxes = Column(JSON, nullable=True)
    line_count = Column(Integer, nullable=True)
    processing_time_ms = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    document = relationship("Document", back_populates="ocr_results")


class CorrectionFeedback(Base):
    __tablename__ = "correction_feedback"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ocr_result_id = Column(String(36), ForeignKey("ocr_results.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    original_text = Column(Text, nullable=False)
    corrected_text = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    is_reviewed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ExportedFile(Base):
    __tablename__ = "exported_files"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    format = Column(String(10), nullable=False)
    storage_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

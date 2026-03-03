from minio import Minio
from minio.error import S3Error
import io
from loguru import logger
from .config import get_settings

settings = get_settings()
_client = None


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        try:
            if not _client.bucket_exists(settings.MINIO_BUCKET):
                _client.make_bucket(settings.MINIO_BUCKET)
                logger.info(f"Created MinIO bucket: {settings.MINIO_BUCKET}")
        except S3Error as e:
            logger.error(f"MinIO bucket init error: {e}")
    return _client


def upload_file(data: bytes, object_name: str, content_type: str = "application/octet-stream") -> str:
    client = get_minio_client()
    client.put_object(
        settings.MINIO_BUCKET, object_name,
        io.BytesIO(data), length=len(data),
        content_type=content_type,
    )
    return object_name


def download_file(object_name: str) -> bytes:
    client = get_minio_client()
    response = client.get_object(settings.MINIO_BUCKET, object_name)
    data = response.read()
    response.close()
    return data


def get_presigned_url(object_name: str, expires_seconds: int = 3600) -> str:
    from datetime import timedelta
    client = get_minio_client()
    return client.presigned_get_object(
        settings.MINIO_BUCKET, object_name,
        expires=timedelta(seconds=expires_seconds),
    )

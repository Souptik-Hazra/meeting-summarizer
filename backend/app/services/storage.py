import os
import re
import logging
from typing import Optional
from fastapi import UploadFile
from supabase import Client
from app.config import settings
from app.services.database import get_supabase_client

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Exception raised when an operation against Supabase Storage fails."""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class FileValidationError(Exception):
    """Exception raised when uploaded audio fails format, size, or metadata validation."""
    pass


def extract_safe_extension(filename: Optional[str]) -> str:
    """
    Extracts and normalizes the extension from a filename.
    Raises FileValidationError if filename is missing or extension is invalid.
    """
    if not filename or not filename.strip():
        raise FileValidationError("Filename is required.")

    # Strip path components to prevent path traversal
    base_name = os.path.basename(filename.strip())
    _, ext = os.path.splitext(base_name)
    ext_lower = ext.lower()

    if not ext_lower or ext_lower not in settings.ALLOWED_AUDIO_EXTENSIONS:
        allowed = ", ".join(sorted(settings.ALLOWED_AUDIO_EXTENSIONS))
        raise FileValidationError(
            f"Unsupported audio format '{ext_lower or 'unknown'}'. Allowed formats: {allowed}"
        )

    return ext_lower


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes user filename for safe storage as metadata.
    Removes path traversal components and unsafe characters.
    """
    base_name = os.path.basename(filename.strip())
    # Remove control characters and limit length
    safe_name = re.sub(r'[^\w\s\.\-_]', '', base_name)[:200]
    return safe_name or "recording.mp3"


def generate_safe_storage_path(meeting_id: str, original_filename: str) -> str:
    """
    Generates a deterministic, isolated storage path for Supabase Storage.
    Pattern: meetings/{meeting_id}/audio{extension}
    """
    ext = extract_safe_extension(original_filename)
    clean_meeting_id = re.sub(r'[^a-zA-Z0-9\-_]', '', meeting_id)
    return f"meetings/{clean_meeting_id}/audio{ext}"


async def read_and_validate_file_content(
    file: UploadFile, 
    max_bytes: Optional[int] = None
) -> bytes:
    """
    Reads upload stream with bounded chunking to enforce file-size limits safely.
    Validates non-empty file and size constraint.
    """
    limit = max_bytes if max_bytes is not None else settings.MAX_FILE_SIZE_BYTES
    chunk_size = 64 * 1024  # 64 KB chunks
    total_bytes = 0
    chunks = []

    try:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            total_bytes += len(chunk)
            if total_bytes > limit:
                max_mb = limit / (1024 * 1024)
                size_str = f"{max_mb:.1f} MB" if max_mb >= 1 else f"{limit} bytes"
                raise FileValidationError(
                    f"File exceeds maximum allowed size of {size_str}."
                )
            chunks.append(chunk)
    finally:
        await file.seek(0)

    if total_bytes == 0:
        raise FileValidationError("Uploaded file is empty (0 bytes).")

    return b"".join(chunks)


def upload_audio_file(
    meeting_id: str,
    file_content: bytes,
    original_filename: str,
    content_type: Optional[str] = None,
    client: Optional[Client] = None
) -> str:
    """
    Uploads audio binary bytes to the Supabase Storage bucket at a safe path.
    Returns the final storage path on success.
    """
    db = client or get_supabase_client()
    storage_path = generate_safe_storage_path(meeting_id, original_filename)
    bucket_name = settings.SUPABASE_STORAGE_BUCKET

    # Supporting content-type fallback
    safe_content_type = content_type if (content_type and content_type.startswith("audio/")) else "audio/mpeg"

    try:
        response = db.storage.from_(bucket_name).upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": safe_content_type, "upsert": "false"}
        )
        return storage_path
    except Exception as e:
        logger.error(f"Failed to upload audio to Supabase Storage at {storage_path}: {str(e)}")
        raise StorageError("Failed to store audio file in cloud storage.", original_error=e)


def delete_audio_file(
    storage_path: str, 
    client: Optional[Client] = None
) -> bool:
    """
    Deletes an audio object from Supabase Storage (e.g. cleanup on database failure).
    Returns True if deletion succeeded, False otherwise.
    """
    db = client or get_supabase_client()
    bucket_name = settings.SUPABASE_STORAGE_BUCKET

    try:
        db.storage.from_(bucket_name).remove([storage_path])
        logger.info(f"Cleaned up storage file at {storage_path}")
        return True
    except Exception as e:
        logger.warning(f"Failed to clean up storage file at {storage_path}: {str(e)}")
        return False

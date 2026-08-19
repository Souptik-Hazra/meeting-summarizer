import uuid
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.schemas.meeting import MeetingCreate, MeetingStatus
from app.services.storage import (
    FileValidationError,
    StorageError,
    extract_safe_extension,
    sanitize_filename,
    read_and_validate_file_content,
    upload_audio_file,
    delete_audio_file,
)
from app.services.database import create_meeting_record, DatabaseError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/meetings", tags=["Meetings"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_meeting(file: UploadFile = File(...)):
    """
    Receives meeting audio recording, validates format and size, stores in Supabase Storage,
    creates the initial database record with status PENDING, and returns meeting ID and status.
    """
    if not file or not file.filename or not file.filename.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file is required."
        )

    # 1. Validate audio format / extension
    try:
        extract_safe_extension(file.filename)
    except FileValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # 2. Bounded read and file size/emptiness validation
    try:
        file_content = await read_and_validate_file_content(file)
    except FileValidationError as e:
        status_code = (
            status.HTTP_413_CONTENT_TOO_LARGE 
            if "exceeds maximum allowed size" in str(e) 
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=str(e))

    # 3. Generate unique meeting ID and sanitize metadata
    meeting_id = str(uuid.uuid4())
    safe_original_name = sanitize_filename(file.filename)

    # 4. Upload audio to Supabase Storage
    try:
        storage_path = upload_audio_file(
            meeting_id=meeting_id,
            file_content=file_content,
            original_filename=file.filename,
            content_type=file.content_type,
        )
    except StorageError as e:
        logger.error(f"Storage upload error for meeting {meeting_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cloud storage service failed to save the audio file."
        )
    except Exception as e:
        logger.error(f"Unexpected error during storage upload for meeting {meeting_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while uploading audio."
        )

    # 5. Create meeting record in Supabase PostgreSQL
    try:
        meeting_data = MeetingCreate(
            meeting_id=meeting_id,
            original_filename=safe_original_name,
            storage_path=storage_path,
            status=MeetingStatus.PENDING,
        )
        created_record = create_meeting_record(meeting_data)
    except DatabaseError as e:
        logger.error(f"Database error creating meeting {meeting_id}, cleaning up storage: {str(e)}")
        # Clean up uploaded storage file to prevent orphaned objects
        delete_audio_file(storage_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist meeting record in database."
        )
    except Exception as e:
        logger.error(f"Unexpected database error for meeting {meeting_id}, cleaning up storage: {str(e)}")
        delete_audio_file(storage_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected database error occurred."
        )

    return {
        "meeting_id": created_record.get("meeting_id", meeting_id),
        "original_filename": created_record.get("original_filename", safe_original_name),
        "status": created_record.get("status", MeetingStatus.PENDING.value),
    }

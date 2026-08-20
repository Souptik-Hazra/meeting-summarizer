import uuid
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, status
from app.schemas.meeting import MeetingCreate, MeetingStatus, MeetingResponse, MeetingStatusResponse
from app.schemas.summary import MeetingSummarizeResponse
from app.services.storage import (
    FileValidationError,
    StorageError,
    extract_safe_extension,
    sanitize_filename,
    read_and_validate_file_content,
    upload_audio_file,
    delete_audio_file,
)
from app.services.database import (
    create_meeting_record,
    get_meeting_record,
    DatabaseError,
)
from app.services.transcription import process_transcription_for_meeting, TranscriptionError
from app.services.summarization import process_summarization_for_meeting, SummarizationError
from app.services.pipeline import process_meeting_pipeline, PipelineError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/meetings", tags=["Meetings"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_meeting(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Receives meeting audio recording, validates format and size, stores in Supabase Storage,
    creates the initial database record with status PENDING, schedules the automated background pipeline,
    and returns HTTP 201 immediately with meeting ID and status.
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

    # 6. ONLY AFTER successful storage + DB record creation, schedule the background pipeline task
    background_tasks.add_task(process_meeting_pipeline, meeting_id)

    return {
        "meeting_id": created_record.get("meeting_id", meeting_id),
        "original_filename": created_record.get("original_filename", safe_original_name),
        "status": created_record.get("status", MeetingStatus.PENDING.value),
    }


@router.get("/{meeting_id}/status", response_model=MeetingStatusResponse, status_code=status.HTTP_200_OK)
async def get_meeting_processing_status(meeting_id: str):
    """
    Returns the live processing status and failure information for a meeting.
    Used for frontend polling.
    """
    try:
        record = get_meeting_record(meeting_id)
    except DatabaseError as e:
        logger.error(f"Database error fetching status for {meeting_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error retrieving meeting status."
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching status for {meeting_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred."
        )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting with ID '{meeting_id}' not found."
        )

    return MeetingStatusResponse(
        meeting_id=record.get("meeting_id", meeting_id),
        status=record.get("status", MeetingStatus.PENDING),
        failure_stage=record.get("failure_stage"),
        error_message=record.get("error_message"),
        created_at=record.get("created_at"),
        updated_at=record.get("updated_at"),
    )


@router.get("/{meeting_id}", response_model=MeetingResponse, status_code=status.HTTP_200_OK)
async def get_meeting_details(meeting_id: str):
    """
    Returns complete meeting record with structured intelligence, transcript, and telemetry timings.
    """
    try:
        record = get_meeting_record(meeting_id)
    except DatabaseError as e:
        logger.error(f"Database error fetching details for {meeting_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error retrieving meeting details."
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching details for {meeting_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred."
        )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting with ID '{meeting_id}' not found."
        )

    return MeetingResponse(
        meeting_id=record.get("meeting_id", meeting_id),
        original_filename=record.get("original_filename", ""),
        storage_path=record.get("storage_path"),
        status=record.get("status", MeetingStatus.PENDING),
        transcript=record.get("transcript"),
        summary=record.get("summary"),
        key_points=record.get("key_points") or [],
        decisions=record.get("decisions") or [],
        action_items=record.get("action_items") or [],
        model_name=record.get("model_name"),
        prompt_version=record.get("prompt_version"),
        transcription_time=record.get("transcription_time"),
        summarization_time=record.get("summarization_time"),
        processing_time=record.get("processing_time"),
        failure_stage=record.get("failure_stage"),
        error_message=record.get("error_message"),
        created_at=record.get("created_at"),
        updated_at=record.get("updated_at"),
    )


@router.post("/{meeting_id}/transcribe", status_code=status.HTTP_200_OK)
async def transcribe_meeting(meeting_id: str):
    """
    Direct endpoint to trigger Whisper transcription for stored meeting audio.
    """
    try:
        updated_record = process_transcription_for_meeting(meeting_id)
        return {
            "meeting_id": updated_record.get("meeting_id", meeting_id),
            "status": updated_record.get("status", MeetingStatus.SUMMARIZING.value),
            "transcript": updated_record.get("transcript", ""),
            "transcription_time": updated_record.get("transcription_time"),
        }
    except TranscriptionError as e:
        err_msg = str(e)
        if "not found" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meeting with ID '{meeting_id}' not found."
            )
        logger.error(f"Transcription failed for meeting {meeting_id}: {err_msg}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Transcription service failed to process meeting audio."
        )
    except Exception as e:
        logger.error(f"Unexpected error transcribing meeting {meeting_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during transcription."
        )


@router.post("/{meeting_id}/summarize", response_model=MeetingSummarizeResponse, status_code=status.HTTP_200_OK)
async def summarize_meeting(meeting_id: str):
    """
    Direct endpoint to trigger Gemini structured summarization for a meeting in SUMMARIZING state.
    """
    try:
        updated_record = process_summarization_for_meeting(meeting_id)
        return MeetingSummarizeResponse(
            meeting_id=updated_record.get("meeting_id", meeting_id),
            status=updated_record.get("status", MeetingStatus.COMPLETED.value),
            summary=updated_record.get("summary"),
            key_points=updated_record.get("key_points") or [],
            decisions=updated_record.get("decisions") or [],
            action_items=updated_record.get("action_items") or [],
            summarization_time=updated_record.get("summarization_time"),
            model_name=updated_record.get("model_name"),
            prompt_version=updated_record.get("prompt_version"),
        )
    except SummarizationError as e:
        err_msg = str(e)
        if "not found" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meeting with ID '{meeting_id}' not found."
            )
        if "requires status 'summarizing'" in err_msg.lower() or "no transcript available" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg
            )
        logger.error(f"Summarization error for meeting {meeting_id}: {err_msg}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Summarization service failed to generate structured intelligence."
        )
    except Exception as e:
        logger.error(f"Unexpected error summarizing meeting {meeting_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during meeting summarization."
        )

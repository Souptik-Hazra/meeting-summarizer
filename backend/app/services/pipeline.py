import time
import logging
from typing import Optional, Dict, Any
from supabase import Client
from app.config import settings
from app.schemas.meeting import MeetingStatus
from app.schemas.summary import MeetingSummaryOutput
from app.services.database import (
    get_supabase_client,
    get_meeting_record,
    update_meeting_status,
    update_meeting_record,
    DatabaseError,
)
from app.services.storage import download_audio_file, StorageError
from app.services.transcription import (
    get_groq_client,
    transcribe_audio,
    normalize_transcript,
    TranscriptionError,
)
from app.services.summarization import (
    get_gemini_client,
    generate_meeting_summary,
    SummarizationError,
)

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Exception raised when an error occurs during background meeting processing."""
    def __init__(self, message: str, failure_stage: str = "pipeline", original_error: Optional[Exception] = None):
        super().__init__(message)
        self.failure_stage = failure_stage
        self.original_error = original_error


def _safe_update_status(
    meeting_id: str,
    status: MeetingStatus,
    failure_stage: Optional[str] = None,
    error_message: Optional[str] = None,
    client: Optional[Client] = None
) -> None:
    """Safely updates meeting status in DB, logging without crashing if the database is unreachable."""
    try:
        update_meeting_status(
            meeting_id=meeting_id,
            status=status,
            failure_stage=failure_stage,
            error_message=error_message,
            client=client
        )
    except Exception as db_err:
        logger.error(f"Critical: Failed to update meeting status to '{status.value}' for {meeting_id}: {str(db_err)}")


def process_meeting_pipeline(
    meeting_id: str,
    supabase_client: Optional[Client] = None,
    groq_client: Optional[Any] = None,
    gemini_client: Optional[Any] = None,
    prompt_version: str = "v1"
) -> Dict[str, Any]:
    """
    Automated Background Processing Pipeline:
    1. Starts total monotonic timer.
    2. Validates meeting exists and is in PENDING state.
    3. Transitions PENDING -> TRANSCRIBING.
    4. Downloads audio from Supabase Storage and transcribes via Groq Whisper.
    5. Normalizes and persists transcript with transcription_time.
    6. Transitions TRANSCRIBING -> SUMMARIZING.
    7. Generates structured intelligence via Gemini Flash with 1 automatic retry on failure.
    8. Measures total monotonic processing_time.
    9. Persists structured intelligence, model metadata, and total processing_time.
    10. Transitions SUMMARIZING -> COMPLETED.
    """
    db = supabase_client or get_supabase_client()
    pipeline_start_time = time.perf_counter()

    # Step 1: Retrieve and validate meeting record
    try:
        record = get_meeting_record(meeting_id, client=db)
    except Exception as e:
        logger.error(f"Failed to fetch meeting record {meeting_id}: {str(e)}")
        raise PipelineError("Database failure retrieving initial meeting record.", failure_stage="storage", original_error=e)

    if not record:
        logger.error(f"Meeting with ID '{meeting_id}' not found for background pipeline.")
        raise PipelineError(f"Meeting with ID '{meeting_id}' not found.", failure_stage="storage")

    current_status = record.get("status")
    # Prevent duplicate / invalid concurrent execution
    if current_status != MeetingStatus.PENDING.value and current_status != MeetingStatus.PENDING:
        logger.warning(f"Meeting {meeting_id} is in status '{current_status}'. Skipping pipeline execution.")
        return record

    storage_path = record.get("storage_path")
    original_filename = record.get("original_filename", "audio.wav")

    if not storage_path:
        _safe_update_status(
            meeting_id=meeting_id,
            status=MeetingStatus.FAILED,
            failure_stage="storage",
            error_message="Meeting record is missing audio storage path.",
            client=db
        )
        raise PipelineError("Missing audio storage path in meeting record.", failure_stage="storage")

    # Step 2: Transition PENDING -> TRANSCRIBING
    _safe_update_status(meeting_id=meeting_id, status=MeetingStatus.TRANSCRIBING, client=db)

    # Step 3: Download audio and transcribe via Groq Whisper
    try:
        audio_bytes = download_audio_file(storage_path, client=db)
    except StorageError as e:
        logger.error(f"Storage download failed for meeting {meeting_id}: {str(e)}")
        _safe_update_status(
            meeting_id=meeting_id,
            status=MeetingStatus.FAILED,
            failure_stage="storage",
            error_message="Failed to retrieve audio file from storage.",
            client=db
        )
        raise PipelineError("Failed to retrieve audio file from storage.", failure_stage="storage", original_error=e)
    except Exception as e:
        logger.error(f"Unexpected storage error for meeting {meeting_id}: {str(e)}")
        _safe_update_status(
            meeting_id=meeting_id,
            status=MeetingStatus.FAILED,
            failure_stage="storage",
            error_message="Unexpected cloud storage error during audio download.",
            client=db
        )
        raise PipelineError("Unexpected cloud storage error.", failure_stage="storage", original_error=e)

    try:
        whisper_client = groq_client or get_groq_client()
        raw_transcript, transcription_time = transcribe_audio(
            audio_bytes=audio_bytes,
            filename=original_filename,
            client=whisper_client
        )
        normalized_transcript = normalize_transcript(raw_transcript)
        
        # Persist transcript and transcription_time
        update_meeting_record(
            meeting_id=meeting_id,
            update_fields={
                "transcript": normalized_transcript,
                "transcription_time": transcription_time,
            },
            client=db
        )
    except TranscriptionError as e:
        logger.error(f"Transcription failed for meeting {meeting_id}: {str(e)}")
        _safe_update_status(
            meeting_id=meeting_id,
            status=MeetingStatus.FAILED,
            failure_stage="transcription",
            error_message="Speech recognition failed during transcription.",
            client=db
        )
        raise PipelineError("Speech recognition failed during transcription.", failure_stage="transcription", original_error=e)
    except Exception as e:
        logger.error(f"Unexpected transcription error for meeting {meeting_id}: {str(e)}")
        _safe_update_status(
            meeting_id=meeting_id,
            status=MeetingStatus.FAILED,
            failure_stage="transcription",
            error_message="Unexpected error occurred during transcription.",
            client=db
        )
        raise PipelineError("Unexpected error during transcription.", failure_stage="transcription", original_error=e)

    # Step 4: Transition TRANSCRIBING -> SUMMARIZING
    _safe_update_status(meeting_id=meeting_id, status=MeetingStatus.SUMMARIZING, client=db)

    # Step 5: Summarize with Gemini Flash (with 1 automatic retry on failure)
    summary_output: Optional[MeetingSummaryOutput] = None
    summarization_time: Optional[float] = None
    last_summarization_error: Optional[Exception] = None
    is_validation_failure = False

    flash_client = gemini_client or get_gemini_client()

    # Attempt 1
    try:
        summary_output, summarization_time = generate_meeting_summary(
            transcript=normalized_transcript,
            client=flash_client,
            prompt_version=prompt_version
        )
    except Exception as exc1:
        last_summarization_error = exc1
        err_str = str(exc1).lower()
        if "validation" in err_str or "structured output" in err_str:
            is_validation_failure = True
        logger.warning(f"Summarization Attempt 1 failed for meeting {meeting_id}: {str(exc1)}. Retrying once in 1.5s...")
        time.sleep(1.5)
        
        # Attempt 2 (Retry Once)
        try:
            summary_output, summarization_time = generate_meeting_summary(
                transcript=normalized_transcript,
                client=flash_client,
                prompt_version=prompt_version
            )
        except Exception as exc2:
            last_summarization_error = exc2
            err_str2 = str(exc2).lower()
            if "validation" in err_str2 or "structured output" in err_str2:
                is_validation_failure = True
            logger.error(f"Summarization Attempt 2 (Retry) failed for meeting {meeting_id}: {str(exc2)}")

    if not summary_output:
        stage = "validation" if is_validation_failure else "summarization"
        safe_msg = "Structured output validation failed." if is_validation_failure else "Generative AI summarization failed."
        _safe_update_status(
            meeting_id=meeting_id,
            status=MeetingStatus.FAILED,
            failure_stage=stage,
            error_message=safe_msg,
            client=db
        )
        raise PipelineError(safe_msg, failure_stage=stage, original_error=last_summarization_error)

    # Step 6: Persist structured intelligence and total processing_time -> COMPLETED
    total_processing_time = round(time.perf_counter() - pipeline_start_time, 2)

    try:
        final_payload = {
            "summary": summary_output.summary,
            "key_points": summary_output.key_points,
            "decisions": summary_output.decisions,
            "action_items": [item.model_dump() for item in summary_output.action_items],
            "model_name": settings.GEMINI_MODEL,
            "prompt_version": prompt_version,
            "summarization_time": summarization_time,
            "processing_time": total_processing_time,
            "status": MeetingStatus.COMPLETED.value,
            "failure_stage": None,
            "error_message": None,
        }
        completed_record = update_meeting_record(meeting_id, final_payload, client=db)
        if not completed_record:
            raise DatabaseError("Failed to persist final meeting intelligence record.")
        return completed_record
    except Exception as e:
        logger.error(f"Failed to persist final completed intelligence for meeting {meeting_id}: {str(e)}")
        _safe_update_status(
            meeting_id=meeting_id,
            status=MeetingStatus.FAILED,
            failure_stage="summarization",
            error_message="Failed to persist completed summary record in database.",
            client=db
        )
        raise PipelineError("Database failure persisting final meeting record.", failure_stage="summarization", original_error=e)

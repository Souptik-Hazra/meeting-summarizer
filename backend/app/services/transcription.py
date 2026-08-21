import os
import re
import time
import logging
from typing import Optional, Tuple, Dict, Any
from groq import Groq
from supabase import Client
from app.config import settings
from app.schemas.meeting import MeetingStatus
from app.services.database import (
    get_supabase_client,
    get_meeting_record,
    update_meeting_status,
    update_meeting_record,
    DatabaseError,
)
from app.services.storage import download_audio_file

logger = logging.getLogger(__name__)

# Global client cache
_groq_client: Optional[Groq] = None


class TranscriptionError(Exception):
    """Exception raised when speech-to-text transcription fails."""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


def get_groq_client() -> Groq:
    """
    Initializes and returns the Groq API client using the configured GROQ_API_KEY.
    """
    global _groq_client
    if _groq_client is not None:
        return _groq_client

    if not settings.GROQ_API_KEY:
        raise TranscriptionError("Groq API key must be configured in environment variables.")

    try:
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
        return _groq_client
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {str(e)}")
        raise TranscriptionError("Failed to initialize speech-to-text service client.", original_error=e)


def normalize_transcript(raw_text: str) -> str:
    """
    Performs conservative transcript normalization:
    - Trims leading/trailing whitespace
    - Normalizes multiple spaces/tabs into a single space per line
    - Normalizes excessive blank lines (3+ into 2)
    - Strictly preserves spoken words, punctuation, numbers, and sentence structure.
    """
    if not raw_text or not raw_text.strip():
        return ""

    lines = raw_text.splitlines()
    cleaned_lines = []
    for line in lines:
        cleaned = re.sub(r'[ \t]+', ' ', line).strip()
        cleaned_lines.append(cleaned)

    normalized = "\n".join(cleaned_lines)
    # Collapse 3 or more consecutive linebreaks into 2
    normalized = re.sub(r'\n{3,}', '\n\n', normalized).strip()
    return normalized


def transcribe_audio(
    audio_bytes: bytes,
    filename: str = "audio.mp3",
    client: Optional[Groq] = None
) -> Tuple[str, float]:
    """
    Calls Groq Whisper (whisper-large-v3) to transcribe the given audio bytes.
    Measures duration with monotonic perf_counter and returns (normalized_transcript, elapsed_seconds).
    """
    groq = client or get_groq_client()
    model_name = settings.GROQ_MODEL  # Strictly "whisper-large-v3"

    if not audio_bytes:
        raise TranscriptionError("Cannot transcribe empty audio data.")

    start_time = time.perf_counter()

    try:
        response = groq.audio.transcriptions.create(
            file=(filename, audio_bytes),
            model=model_name,
            response_format="verbose_json"
        )
    except Exception as e:
        logger.error(f"Groq Whisper transcription API failed: {str(e)}")
        raise TranscriptionError("Speech-to-text transcription service failed.", original_error=e)

    elapsed_time = round(time.perf_counter() - start_time, 2)

    # Extract text from response
    raw_text = getattr(response, "text", "") or ""
    if not raw_text and isinstance(response, dict):
        raw_text = response.get("text", "")

    if not raw_text or not raw_text.strip():
        logger.warning(f"Whisper returned empty transcript for file {filename}")
        raw_text = ""

    normalized_text = normalize_transcript(raw_text)
    return normalized_text, elapsed_time


def process_transcription_for_meeting(
    meeting_id: str,
    groq_client: Optional[Groq] = None,
    supabase_client: Optional[Client] = None
) -> Dict[str, Any]:
    """
    Orchestrates the Phase 5 transcription flow:
    1. Retrieves meeting record.
    2. Updates status to TRANSCRIBING.
    3. Downloads stored audio from Supabase Storage.
    4. Calls Groq Whisper (whisper-large-v3) and normalizes transcript.
    5. Persists transcript and transcription_time, transitioning status to SUMMARIZING.
    6. On failure: logs failure_stage='transcription' and sets status to FAILED.
    """
    db = supabase_client or get_supabase_client()

    # 1. Retrieve meeting record
    try:
        meeting_record = get_meeting_record(meeting_id, client=db)
    except Exception as e:
        logger.error(f"Failed to fetch meeting record {meeting_id}: {str(e)}")
        raise TranscriptionError(f"Database failure retrieving meeting {meeting_id}.", original_error=e)

    if not meeting_record:
        raise TranscriptionError(f"Meeting with ID '{meeting_id}' not found.")

    storage_path = meeting_record.get("storage_path")
    if not storage_path:
        # Mark FAILED since audio cannot be retrieved
        update_meeting_status(
            meeting_id=meeting_id,
            status=MeetingStatus.FAILED,
            failure_stage="transcription",
            error_message="Meeting record has no associated audio storage path.",
            client=db
        )
        raise TranscriptionError(f"Meeting {meeting_id} has no storage path associated.")

    # 2. Update status to TRANSCRIBING
    try:
        update_meeting_status(
            meeting_id=meeting_id,
            status=MeetingStatus.TRANSCRIBING,
            client=db
        )
    except Exception as e:
        logger.error(f"Failed to update status to TRANSCRIBING for {meeting_id}: {str(e)}")

    # 3. Download stored audio
    try:
        audio_bytes = download_audio_file(storage_path, client=db)
    except Exception as e:
        safe_msg = "Failed to download audio recording from storage."
        logger.error(f"Storage download failed for meeting {meeting_id}: {str(e)}")
        update_meeting_status(
            meeting_id=meeting_id,
            status=MeetingStatus.FAILED,
            failure_stage="transcription",
            error_message=safe_msg,
            client=db
        )
        raise TranscriptionError(safe_msg, original_error=e)

    # 4. Transcribe audio with Groq Whisper
    filename = os.path.basename(storage_path) or "audio.mp3"
    try:
        transcript, elapsed_time = transcribe_audio(
            audio_bytes=audio_bytes,
            filename=filename,
            client=groq_client
        )
    except Exception as e:
        safe_msg = "Speech recognition failed during transcription stage."
        logger.error(f"Groq Whisper transcription failed for meeting {meeting_id}: {str(e)}")
        update_meeting_status(
            meeting_id=meeting_id,
            status=MeetingStatus.FAILED,
            failure_stage="transcription",
            error_message=safe_msg,
            client=db
        )
        raise TranscriptionError(safe_msg, original_error=e)

    # 5. Persist transcript & transition status to SUMMARIZING for next pipeline phase
    try:
        update_payload = {
            "transcript": transcript,
            "transcription_time": elapsed_time,
            "status": MeetingStatus.SUMMARIZING.value,
            "failure_stage": None,
            "error_message": None,
        }
        updated_record = update_meeting_record(meeting_id, update_payload, client=db)
        if not updated_record:
            raise DatabaseError(f"Failed to persist transcript for meeting {meeting_id}")
        return updated_record
    except Exception as e:
        safe_msg = "Failed to persist completed transcript in database."
        logger.error(f"Database persistence failure for meeting {meeting_id}: {str(e)}")
        update_meeting_status(
            meeting_id=meeting_id,
            status=MeetingStatus.FAILED,
            failure_stage="transcription",
            error_message=safe_msg,
            client=db
        )
        raise TranscriptionError(safe_msg, original_error=e)

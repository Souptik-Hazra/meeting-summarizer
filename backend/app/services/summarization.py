import os
import time
import json
import logging
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
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

logger = logging.getLogger(__name__)

# Global client cache
_gemini_client: Optional[Any] = None


class SummarizationError(Exception):
    """Exception raised when meeting summarization fails."""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


def get_gemini_client() -> Any:
    """
    Initializes and returns the official Google GenAI client using GEMINI_API_KEY.
    """
    global _gemini_client
    if _gemini_client is not None:
        return _gemini_client

    if not settings.GEMINI_API_KEY:
        raise SummarizationError("Gemini API key must be configured in environment variables.")

    try:
        from google import genai
        _gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return _gemini_client
    except Exception as e:
        logger.error(f"Failed to initialize Google GenAI client: {str(e)}")
        raise SummarizationError("Failed to initialize summarization service client.", original_error=e)


def load_prompt_template(version: str = "v1") -> str:
    """
    Loads the versioned meeting summary prompt template from backend/app/prompts/.
    """
    prompts_dir = Path(__file__).resolve().parent.parent / "prompts"
    prompt_file = prompts_dir / f"meeting_summary_{version}.txt"

    if not prompt_file.exists():
        raise SummarizationError(f"Prompt template version '{version}' not found at {prompt_file}")

    try:
        return prompt_file.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to read prompt template {prompt_file}: {str(e)}")
        raise SummarizationError(f"Failed to load prompt template version '{version}'.", original_error=e)


def generate_meeting_summary(
    transcript: str,
    client: Optional[Any] = None,
    prompt_version: str = "v1"
) -> Tuple[MeetingSummaryOutput, float]:
    """
    Calls Gemini 2.5 Flash with native structured output schema (MeetingSummaryOutput).
    Validates output through Pydantic as the final gate and measures execution time.
    """
    if not transcript or not transcript.strip():
        raise SummarizationError("Cannot summarize empty or whitespace-only transcript.")

    gemini = client or get_gemini_client()
    system_instruction = load_prompt_template(prompt_version)
    model_name = settings.GEMINI_MODEL  # Strictly "gemini-2.5-flash"

    prompt_user_content = (
        "Analyze the following meeting transcript and produce the structured meeting intelligence output.\n\n"
        "--- BEGIN MEETING TRANSCRIPT (UNTRUSTED DATA) ---\n"
        f"{transcript}\n"
        "--- END MEETING TRANSCRIPT ---"
    )

    start_time = time.perf_counter()

    try:
        from google.genai import types
        response = gemini.models.generate_content(
            model=model_name,
            contents=prompt_user_content,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=MeetingSummaryOutput,
                temperature=0.2,
            ),
        )
    except Exception as e:
        logger.error(f"Gemini 2.5 Flash API generation error: {str(e)}")
        raise SummarizationError("Generative AI summarization service failed.", original_error=e)

    elapsed_time = round(time.perf_counter() - start_time, 2)

    # Validate output through Pydantic final gate
    validated_output: Optional[MeetingSummaryOutput] = None

    try:
        if hasattr(response, "parsed") and response.parsed is not None:
            if isinstance(response.parsed, MeetingSummaryOutput):
                validated_output = response.parsed
            elif isinstance(response.parsed, dict):
                validated_output = MeetingSummaryOutput.model_validate(response.parsed)
            else:
                validated_output = MeetingSummaryOutput.model_validate(response.parsed)
        elif hasattr(response, "text") and response.text:
            validated_output = MeetingSummaryOutput.model_validate_json(response.text)
        else:
            raise ValueError("No structured text or parsed data in Gemini response.")
    except Exception as validation_exc:
        logger.error(f"Pydantic structured output validation failed on Gemini response: {str(validation_exc)}")
        raise SummarizationError("Gemini response failed structured output validation.", original_error=validation_exc)

    return validated_output, elapsed_time


def process_summarization_for_meeting(
    meeting_id: str,
    gemini_client: Optional[Any] = None,
    supabase_client: Optional[Client] = None,
    prompt_version: str = "v1"
) -> Dict[str, Any]:
    """
    Orchestrates the Phase 6 summarization flow:
    1. Retrieves meeting record.
    2. Validates state is strictly SUMMARIZING.
    3. Validates transcript is non-empty.
    4. Calls Gemini 2.5 Flash and validates via Pydantic.
    5. Persists structured intelligence and summarization_time, transitioning status to COMPLETED.
    6. On failure: logs failure_stage='summarization' and sets status to FAILED.
    """
    db = supabase_client or get_supabase_client()

    # 1. Retrieve meeting record
    try:
        meeting_record = get_meeting_record(meeting_id, client=db)
    except Exception as e:
        logger.error(f"Database error fetching meeting {meeting_id}: {str(e)}")
        raise SummarizationError(f"Database failure retrieving meeting {meeting_id}.", original_error=e)

    if not meeting_record:
        raise SummarizationError(f"Meeting with ID '{meeting_id}' not found.")

    # 2. Strict State Validation
    current_status = meeting_record.get("status")
    if current_status != MeetingStatus.SUMMARIZING.value and current_status != MeetingStatus.SUMMARIZING:
        raise SummarizationError(
            f"Meeting '{meeting_id}' is in status '{current_status}'. Summarization requires status 'SUMMARIZING'."
        )

    # 3. Validate transcript
    transcript = meeting_record.get("transcript")
    if not transcript or not transcript.strip():
        # Persist failure since prerequisite data is missing
        update_meeting_status(
            meeting_id=meeting_id,
            status=MeetingStatus.FAILED,
            failure_stage="summarization",
            error_message="Meeting has no transcript available for summarization.",
            client=db
        )
        raise SummarizationError(f"Meeting '{meeting_id}' has no transcript available for summarization.")

    # 4. Generate structured summary with Gemini 2.5 Flash
    try:
        summary_output, elapsed_time = generate_meeting_summary(
            transcript=transcript,
            client=gemini_client,
            prompt_version=prompt_version
        )
    except Exception as e:
        safe_msg = "Generative AI summarization failed during processing."
        logger.error(f"Summarization failed for meeting {meeting_id}: {str(e)}")
        update_meeting_status(
            meeting_id=meeting_id,
            status=MeetingStatus.FAILED,
            failure_stage="summarization",
            error_message=safe_msg,
            client=db
        )
        raise SummarizationError(safe_msg, original_error=e)

    # 5. Persist intelligence and transition status to COMPLETED
    try:
        update_payload = {
            "summary": summary_output.summary,
            "key_points": summary_output.key_points,
            "decisions": summary_output.decisions,
            "action_items": [item.model_dump() for item in summary_output.action_items],
            "model_name": settings.GEMINI_MODEL,
            "prompt_version": prompt_version,
            "summarization_time": elapsed_time,
            "status": MeetingStatus.COMPLETED.value,
            "failure_stage": None,
            "error_message": None,
        }
        updated_record = update_meeting_record(meeting_id, update_payload, client=db)
        if not updated_record:
            raise DatabaseError(f"Failed to persist summary record for meeting {meeting_id}")
        return updated_record
    except Exception as e:
        safe_msg = "Failed to persist completed summary in database."
        logger.error(f"Database persistence failure for meeting {meeting_id}: {str(e)}")
        update_meeting_status(
            meeting_id=meeting_id,
            status=MeetingStatus.FAILED,
            failure_stage="summarization",
            error_message=safe_msg,
            client=db
        )
        raise SummarizationError(safe_msg, original_error=e)

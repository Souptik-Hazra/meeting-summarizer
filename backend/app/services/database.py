import logging
from typing import Optional, Dict, Any
from supabase import create_client, Client
from app.config import settings
from app.schemas.meeting import MeetingCreate, MeetingStatus

logger = logging.getLogger(__name__)

# Global client cache
_supabase_client: Optional[Client] = None


class DatabaseError(Exception):
    """Custom exception for database operation failures that safely hides sensitive details."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


def get_supabase_client() -> Client:
    """
    Initializes and returns the Supabase PostgREST client.
    Raises DatabaseError if credentials are not configured.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise DatabaseError(
            "Supabase URL and Key must be configured in environment variables."
        )

    try:
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        return _supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        raise DatabaseError(
            "Failed to establish connection to database service.", original_error=e
        )


def create_meeting_record(
    meeting_data: MeetingCreate, client: Optional[Client] = None
) -> Dict[str, Any]:
    """
    Creates a new meeting record in the Supabase PostgreSQL database.
    """
    db = client or get_supabase_client()
    payload = {
        "meeting_id": meeting_data.meeting_id,
        "original_filename": meeting_data.original_filename,
        "storage_path": meeting_data.storage_path,
        "status": (
            meeting_data.status.value
            if isinstance(meeting_data.status, MeetingStatus)
            else meeting_data.status
        ),
    }

    try:
        response = db.table("meetings").insert(payload).execute()
        if not response.data or len(response.data) == 0:
            raise DatabaseError(
                f"No record returned after creating meeting: {meeting_data.meeting_id}"
            )
        return response.data[0]
    except DatabaseError:
        raise
    except Exception as e:
        logger.error(
            f"Database error creating meeting record {meeting_data.meeting_id}: {str(e)}"
        )
        raise DatabaseError(
            "Failed to create meeting persistence record.", original_error=e
        )


def get_meeting_record(
    meeting_id: str, client: Optional[Client] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieves a meeting record by meeting_id.
    Returns None if the meeting is not found.
    """
    db = client or get_supabase_client()
    try:
        response = (
            db.table("meetings").select("*").eq("meeting_id", meeting_id).execute()
        )
        if not response.data or len(response.data) == 0:
            return None
        return response.data[0]
    except Exception as e:
        logger.error(f"Database error retrieving meeting record {meeting_id}: {str(e)}")
        raise DatabaseError(
            f"Failed to fetch meeting record for {meeting_id}.", original_error=e
        )


def update_meeting_status(
    meeting_id: str,
    status: MeetingStatus,
    failure_stage: Optional[str] = None,
    error_message: Optional[str] = None,
    client: Optional[Client] = None,
) -> Optional[Dict[str, Any]]:
    """
    Updates the status and optional failure metadata of a meeting record.
    """
    db = client or get_supabase_client()
    status_val = status.value if isinstance(status, MeetingStatus) else status
    update_payload: Dict[str, Any] = {"status": status_val}

    if failure_stage is not None:
        update_payload["failure_stage"] = failure_stage
    if error_message is not None:
        update_payload["error_message"] = error_message

    try:
        response = (
            db.table("meetings")
            .update(update_payload)
            .eq("meeting_id", meeting_id)
            .execute()
        )
        if not response.data or len(response.data) == 0:
            return None
        return response.data[0]
    except Exception as e:
        logger.error(f"Database error updating meeting status {meeting_id}: {str(e)}")
        raise DatabaseError(
            f"Failed to update status for meeting {meeting_id}.", original_error=e
        )


def update_meeting_record(
    meeting_id: str, update_fields: Dict[str, Any], client: Optional[Client] = None
) -> Optional[Dict[str, Any]]:
    """
    Updates arbitrary persisted fields on a meeting record.
    """
    db = client or get_supabase_client()
    try:
        response = (
            db.table("meetings")
            .update(update_fields)
            .eq("meeting_id", meeting_id)
            .execute()
        )
        if not response.data or len(response.data) == 0:
            return None
        return response.data[0]
    except Exception as e:
        logger.error(f"Database error updating meeting record {meeting_id}: {str(e)}")
        raise DatabaseError(
            f"Failed to update meeting record for {meeting_id}.", original_error=e
        )

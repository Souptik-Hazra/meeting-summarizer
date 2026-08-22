import pytest
from pydantic import ValidationError
from app.schemas.meeting import (
    MeetingStatus,
    MeetingCreate,
    MeetingStatusUpdate,
    MeetingStatusResponse,
    MeetingResponse,
)


def test_meeting_status_enum():
    assert MeetingStatus.PENDING == "PENDING"
    assert MeetingStatus.TRANSCRIBING == "TRANSCRIBING"
    assert MeetingStatus.SUMMARIZING == "SUMMARIZING"
    assert MeetingStatus.COMPLETED == "COMPLETED"
    assert MeetingStatus.FAILED == "FAILED"

    # Test valid and invalid conversion
    assert MeetingStatus("PENDING") == MeetingStatus.PENDING
    with pytest.raises(ValueError):
        MeetingStatus("INVALID_STATUS")


def test_meeting_create_schema():
    data = {
        "meeting_id": "meet_123",
        "original_filename": "team_sync.mp3",
        "storage_path": "meetings/meet_123/audio/team_sync.mp3",
        "status": "PENDING",
    }
    meeting = MeetingCreate(**data)
    assert meeting.meeting_id == "meet_123"
    assert meeting.original_filename == "team_sync.mp3"
    assert meeting.status == MeetingStatus.PENDING

    # Test default status
    minimal = MeetingCreate(meeting_id="meet_456", original_filename="recording.wav")
    assert minimal.status == MeetingStatus.PENDING
    assert minimal.storage_path is None


def test_meeting_status_update_schema():
    update = MeetingStatusUpdate(
        status=MeetingStatus.FAILED,
        failure_stage="transcription",
        error_message="Network error",
    )
    assert update.status == MeetingStatus.FAILED
    assert update.failure_stage == "transcription"
    assert update.error_message == "Network error"


def test_meeting_response_schema():
    data = {
        "meeting_id": "meet_789",
        "original_filename": "board_meeting.mp3",
        "status": "COMPLETED",
        "transcript": "Hello everyone...",
        "summary": "The board discussed Q3 results.",
        "key_points": ["Revenue up 20%", "Hiring approved"],
        "decisions": ["Approved 2026 budget"],
        "action_items": [
            {"task": "Prepare report", "owner": "Alice", "deadline": "Friday"}
        ],
        "processing_time": 12.5,
    }
    response = MeetingResponse(**data)
    assert response.meeting_id == "meet_789"
    assert response.status == MeetingStatus.COMPLETED
    assert len(response.key_points) == 2
    assert len(response.action_items) == 1
    assert response.processing_time == 12.5

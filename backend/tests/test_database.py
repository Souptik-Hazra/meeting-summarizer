import pytest
from unittest.mock import MagicMock
from app.schemas.meeting import MeetingCreate, MeetingStatus
from app.services.database import (
    DatabaseError,
    create_meeting_record,
    get_meeting_record,
    update_meeting_status,
    update_meeting_record,
)


@pytest.fixture
def mock_supabase():
    mock_client = MagicMock()
    return mock_client


def test_create_meeting_record_success(mock_supabase):
    meeting_input = MeetingCreate(
        meeting_id="test_meet_001",
        original_filename="standup.mp3",
        storage_path="meetings/test_meet_001/audio/standup.mp3",
        status=MeetingStatus.PENDING,
    )

    expected_return = {
        "meeting_id": "test_meet_001",
        "original_filename": "standup.mp3",
        "storage_path": "meetings/test_meet_001/audio/standup.mp3",
        "status": "PENDING",
    }

    # Mock response
    mock_execute = MagicMock()
    mock_execute.data = [expected_return]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = (
        mock_execute
    )

    result = create_meeting_record(meeting_input, client=mock_supabase)
    assert result["meeting_id"] == "test_meet_001"
    assert result["status"] == "PENDING"
    mock_supabase.table.assert_called_with("meetings")


def test_create_meeting_record_failure(mock_supabase):
    meeting_input = MeetingCreate(
        meeting_id="test_meet_002", original_filename="sync.wav"
    )

    mock_supabase.table.return_value.insert.return_value.execute.side_effect = (
        Exception("DB Connection Timeout")
    )

    with pytest.raises(DatabaseError) as exc_info:
        create_meeting_record(meeting_input, client=mock_supabase)
    assert "Failed to create meeting persistence record" in str(exc_info.value)


def test_get_meeting_record_found(mock_supabase):
    expected_data = {
        "meeting_id": "test_meet_003",
        "original_filename": "client_call.m4a",
        "status": "PENDING",
    }

    mock_execute = MagicMock()
    mock_execute.data = [expected_data]
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
        mock_execute
    )

    record = get_meeting_record("test_meet_003", client=mock_supabase)
    assert record is not None
    assert record["meeting_id"] == "test_meet_003"


def test_get_meeting_record_not_found(mock_supabase):
    mock_execute = MagicMock()
    mock_execute.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
        mock_execute
    )

    record = get_meeting_record("nonexistent_id", client=mock_supabase)
    assert record is None


def test_update_meeting_status_success(mock_supabase):
    updated_data = {"meeting_id": "test_meet_004", "status": "TRANSCRIBING"}

    mock_execute = MagicMock()
    mock_execute.data = [updated_data]
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
        mock_execute
    )

    result = update_meeting_status(
        "test_meet_004", status=MeetingStatus.TRANSCRIBING, client=mock_supabase
    )
    assert result is not None
    assert result["status"] == "TRANSCRIBING"
    mock_supabase.table.return_value.update.assert_called_with(
        {"status": "TRANSCRIBING"}
    )


def test_update_meeting_status_failure_stage(mock_supabase):
    updated_data = {
        "meeting_id": "test_meet_005",
        "status": "FAILED",
        "failure_stage": "transcription",
        "error_message": "Audio corrupted",
    }

    mock_execute = MagicMock()
    mock_execute.data = [updated_data]
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
        mock_execute
    )

    result = update_meeting_status(
        "test_meet_005",
        status=MeetingStatus.FAILED,
        failure_stage="transcription",
        error_message="Audio corrupted",
        client=mock_supabase,
    )
    assert result["status"] == "FAILED"
    mock_supabase.table.return_value.update.assert_called_with(
        {
            "status": "FAILED",
            "failure_stage": "transcription",
            "error_message": "Audio corrupted",
        }
    )


def test_update_meeting_record_arbitrary_fields(mock_supabase):
    mock_execute = MagicMock()
    mock_execute.data = [{"meeting_id": "test_meet_006", "transcription_time": 4.5}]
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
        mock_execute
    )

    result = update_meeting_record(
        "test_meet_006", {"transcription_time": 4.5}, client=mock_supabase
    )
    assert result["transcription_time"] == 4.5

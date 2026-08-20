import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.storage import StorageError
from app.services.database import DatabaseError
from app.services.transcription import TranscriptionError
from app.config import settings

client = TestClient(app)


def test_upload_meeting_success():
    fake_audio = io.BytesIO(b"RIFF" + b"\x00" * 200)
    fake_audio.name = "weekly_sync.mp3"

    with patch("app.routes.meeting.upload_audio_file") as mock_upload, \
         patch("app.routes.meeting.create_meeting_record") as mock_create_db:
        
        mock_upload.return_value = "meetings/mock-id/audio.mp3"
        mock_create_db.return_value = {
            "meeting_id": "mock-id",
            "original_filename": "weekly_sync.mp3",
            "status": "PENDING"
        }

        response = client.post(
            "/api/meetings/upload",
            files={"file": ("weekly_sync.mp3", fake_audio, "audio/mpeg")}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["meeting_id"] == "mock-id"
        assert data["status"] == "PENDING"
        assert data["original_filename"] == "weekly_sync.mp3"
        mock_upload.assert_called_once()
        mock_create_db.assert_called_once()


def test_upload_meeting_invalid_format():
    fake_file = io.BytesIO(b"fake text content")
    response = client.post(
        "/api/meetings/upload",
        files={"file": ("notes.txt", fake_file, "text/plain")}
    )
    assert response.status_code == 400
    assert "Unsupported audio format" in response.json()["detail"]


def test_upload_meeting_empty_file():
    empty_file = io.BytesIO(b"")
    response = client.post(
        "/api/meetings/upload",
        files={"file": ("silent.mp3", empty_file, "audio/mpeg")}
    )
    assert response.status_code == 400
    assert "Uploaded file is empty" in response.json()["detail"]


def test_upload_meeting_oversized_file():
    with patch("app.services.storage.settings.MAX_FILE_SIZE_BYTES", 100):
        large_file = io.BytesIO(b"x" * 200)
        response = client.post(
            "/api/meetings/upload",
            files={"file": ("large.wav", large_file, "audio/wav")}
        )
        assert response.status_code == 413
        assert "exceeds maximum allowed size" in response.json()["detail"]


def test_upload_meeting_storage_failure():
    fake_audio = io.BytesIO(b"RIFF" + b"\x00" * 100)

    with patch("app.routes.meeting.upload_audio_file") as mock_upload:
        mock_upload.side_effect = StorageError("Supabase Storage Down")

        response = client.post(
            "/api/meetings/upload",
            files={"file": ("standup.m4a", fake_audio, "audio/mp4")}
        )

        assert response.status_code == 502
        assert "storage" in response.json()["detail"].lower()


def test_upload_meeting_database_failure_with_cleanup():
    fake_audio = io.BytesIO(b"RIFF" + b"\x00" * 100)

    with patch("app.routes.meeting.upload_audio_file") as mock_upload, \
         patch("app.routes.meeting.create_meeting_record") as mock_create_db, \
         patch("app.routes.meeting.delete_audio_file") as mock_delete:
        
        mock_upload.return_value = "meetings/temp-id/audio.flac"
        mock_create_db.side_effect = DatabaseError("Database write error")

        response = client.post(
            "/api/meetings/upload",
            files={"file": ("interview.flac", fake_audio, "audio/flac")}
        )

        assert response.status_code == 500
        assert "database" in response.json()["detail"].lower()
        mock_delete.assert_called_once_with("meetings/temp-id/audio.flac")


def test_transcribe_meeting_success():
    with patch("app.routes.meeting.process_transcription_for_meeting") as mock_process:
        mock_process.return_value = {
            "meeting_id": "test-meet-123",
            "status": "SUMMARIZING",
            "transcript": "Meeting discussion notes transcript.",
            "transcription_time": 4.12
        }

        response = client.post("/api/meetings/test-meet-123/transcribe")
        assert response.status_code == 200
        data = response.json()
        assert data["meeting_id"] == "test-meet-123"
        assert data["status"] == "SUMMARIZING"
        assert data["transcript"] == "Meeting discussion notes transcript."
        assert data["transcription_time"] == 4.12


def test_transcribe_meeting_not_found():
    with patch("app.routes.meeting.process_transcription_for_meeting") as mock_process:
        mock_process.side_effect = TranscriptionError("Meeting with ID 'missing-id' not found.")

        response = client.post("/api/meetings/missing-id/transcribe")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_transcribe_meeting_service_failure():
    with patch("app.routes.meeting.process_transcription_for_meeting") as mock_process:
        mock_process.side_effect = TranscriptionError("Speech recognition failed during transcription.")

        response = client.post("/api/meetings/err-id/transcribe")
        assert response.status_code == 502
        assert "transcription service failed" in response.json()["detail"].lower()


def test_summarize_meeting_success():
    with patch("app.routes.meeting.process_summarization_for_meeting") as mock_process:
        mock_process.return_value = {
            "meeting_id": "test-sum-123",
            "status": "COMPLETED",
            "summary": "Meeting summary text.",
            "key_points": ["Point 1", "Point 2"],
            "decisions": ["Decision 1"],
            "action_items": [{"task": "Task 1", "owner": "Alice", "deadline": "Friday"}],
            "summarization_time": 3.14,
            "model_name": settings.GEMINI_MODEL,
            "prompt_version": "v1"
        }

        response = client.post("/api/meetings/test-sum-123/summarize")
        assert response.status_code == 200
        data = response.json()
        assert data["meeting_id"] == "test-sum-123"
        assert data["status"] == "COMPLETED"
        assert data["summary"] == "Meeting summary text."
        assert len(data["key_points"]) == 2
        assert len(data["decisions"]) == 1
        assert len(data["action_items"]) == 1
        assert data["summarization_time"] == 3.14
        assert data["model_name"] == settings.GEMINI_MODEL


def test_summarize_meeting_not_found():
    from app.services.summarization import SummarizationError
    with patch("app.routes.meeting.process_summarization_for_meeting") as mock_process:
        mock_process.side_effect = SummarizationError("Meeting with ID 'missing-id' not found.")

        response = client.post("/api/meetings/missing-id/summarize")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_summarize_meeting_invalid_state():
    from app.services.summarization import SummarizationError
    with patch("app.routes.meeting.process_summarization_for_meeting") as mock_process:
        mock_process.side_effect = SummarizationError("Meeting 'm1' is in status 'PENDING'. Summarization requires status 'SUMMARIZING'.")

        response = client.post("/api/meetings/m1/summarize")
        assert response.status_code == 400
        assert "requires status 'summarizing'" in response.json()["detail"].lower()


def test_summarize_meeting_missing_transcript():
    from app.services.summarization import SummarizationError
    with patch("app.routes.meeting.process_summarization_for_meeting") as mock_process:
        mock_process.side_effect = SummarizationError("Meeting 'm2' has no transcript available for summarization.")

        response = client.post("/api/meetings/m2/summarize")
        assert response.status_code == 400
        assert "no transcript available" in response.json()["detail"].lower()


def test_summarize_meeting_service_failure():
    from app.services.summarization import SummarizationError
    with patch("app.routes.meeting.process_summarization_for_meeting") as mock_process:
        mock_process.side_effect = SummarizationError("Gemini API generation failed.")

        response = client.post("/api/meetings/err-id/summarize")
        assert response.status_code == 502
        assert "summarization service failed" in response.json()["detail"].lower()


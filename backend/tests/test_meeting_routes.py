import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.storage import StorageError
from app.services.database import DatabaseError

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

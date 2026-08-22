import pytest
import io
from unittest.mock import MagicMock
from fastapi import UploadFile
from app.services.storage import (
    FileValidationError,
    StorageError,
    extract_safe_extension,
    sanitize_filename,
    generate_safe_storage_path,
    read_and_validate_file_content,
    upload_audio_file,
    delete_audio_file,
)


def test_extract_safe_extension_valid():
    assert extract_safe_extension("meeting.mp3") == ".mp3"
    assert extract_safe_extension("CALL_RECORDING.WAV") == ".wav"
    assert extract_safe_extension("notes.m4a") == ".m4a"
    assert extract_safe_extension("audio.flac") == ".flac"
    assert extract_safe_extension("speech.aac") == ".aac"
    assert extract_safe_extension("track.ogg") == ".ogg"


def test_extract_safe_extension_invalid():
    with pytest.raises(FileValidationError) as exc:
        extract_safe_extension("script.py")
    assert "Unsupported audio format" in str(exc.value)

    with pytest.raises(FileValidationError) as exc:
        extract_safe_extension("document.pdf")
    assert "Unsupported audio format" in str(exc.value)

    with pytest.raises(FileValidationError) as exc:
        extract_safe_extension("")
    assert "Filename is required" in str(exc.value)


def test_sanitize_filename():
    assert sanitize_filename("../../../etc/passwd.mp3") == "passwd.mp3"
    assert sanitize_filename("safe_meeting.wav") == "safe_meeting.wav"
    assert sanitize_filename("complex/nested\\path/file.m4a") == "file.m4a"


def test_generate_safe_storage_path():
    meeting_id = "test-meet-1234"
    path = generate_safe_storage_path(meeting_id, "user-recording.mp3")
    assert path == "meetings/test-meet-1234/audio.mp3"

    # Test with path traversal attempt in meeting_id
    path_traversal = generate_safe_storage_path("../bad-id/", "test.wav")
    assert path_traversal == "meetings/bad-id/audio.wav"


@pytest.mark.anyio
async def test_read_and_validate_file_content_success():
    data = b"RIFF" + b"\x00" * 100
    upload = UploadFile(filename="test.wav", file=io.BytesIO(data))
    content = await read_and_validate_file_content(upload, max_bytes=1024)
    assert content == data


@pytest.mark.anyio
async def test_read_and_validate_file_content_empty():
    upload = UploadFile(filename="empty.mp3", file=io.BytesIO(b""))
    with pytest.raises(FileValidationError) as exc:
        await read_and_validate_file_content(upload)
    assert "Uploaded file is empty" in str(exc.value)


@pytest.mark.anyio
async def test_read_and_validate_file_content_oversized():
    data = b"x" * 200
    upload = UploadFile(filename="large.mp3", file=io.BytesIO(data))
    with pytest.raises(FileValidationError) as exc:
        await read_and_validate_file_content(upload, max_bytes=100)
    assert "File exceeds maximum allowed size" in str(exc.value)


def test_upload_audio_file_success():
    mock_client = MagicMock()
    mock_storage = MagicMock()
    mock_client.storage.from_.return_value = mock_storage
    mock_storage.upload.return_value = {"Key": "meetings/m1/audio.mp3"}

    path = upload_audio_file(
        meeting_id="m1",
        file_content=b"test_audio",
        original_filename="sample.mp3",
        client=mock_client
    )

    assert path == "meetings/m1/audio.mp3"
    mock_client.storage.from_.assert_called_with("meeting-audio")
    mock_storage.upload.assert_called_once()


def test_upload_audio_file_failure():
    mock_client = MagicMock()
    mock_storage = MagicMock()
    mock_client.storage.from_.return_value = mock_storage
    mock_storage.upload.side_effect = Exception("Storage Bucket Access Denied")

    with pytest.raises(StorageError) as exc:
        upload_audio_file(
            meeting_id="m2",
            file_content=b"test_audio",
            original_filename="sample.wav",
            client=mock_client
        )
    assert "Failed to store audio file in cloud storage" in str(exc.value)


def test_delete_audio_file():
    mock_client = MagicMock()
    mock_storage = MagicMock()
    mock_client.storage.from_.return_value = mock_storage
    
    assert delete_audio_file("meetings/m1/audio.mp3", client=mock_client) is True
    mock_storage.remove.assert_called_with(["meetings/m1/audio.mp3"])

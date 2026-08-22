import pytest
from unittest.mock import MagicMock, patch
from app.services.transcription import (
    TranscriptionError,
    normalize_transcript,
    transcribe_audio,
    process_transcription_for_meeting,
)
from app.schemas.meeting import MeetingStatus


def test_normalize_transcript_basic():
    raw = "  Hello   world!  \n\n\n\nThis is a   test.  "
    expected = "Hello world!\n\nThis is a test."
    assert normalize_transcript(raw) == expected


def test_normalize_transcript_empty():
    assert normalize_transcript("") == ""
    assert normalize_transcript("   \n\n   ") == ""


def test_normalize_transcript_preserves_content_and_punctuation():
    raw = "Speaker 1: Are we on track for Q3? Yes, 100% on track!\n   Speaker 2: Great."
    expected = (
        "Speaker 1: Are we on track for Q3? Yes, 100% on track!\nSpeaker 2: Great."
    )
    assert normalize_transcript(raw) == expected


def test_transcribe_audio_success():
    mock_groq = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "   This is the meeting transcript.   "
    mock_groq.audio.transcriptions.create.return_value = mock_response

    audio_bytes = b"FAKE_AUDIO_BYTES"
    transcript, elapsed = transcribe_audio(
        audio_bytes=audio_bytes, filename="test.mp3", client=mock_groq
    )

    assert transcript == "This is the meeting transcript."
    assert isinstance(elapsed, float)
    assert elapsed >= 0
    mock_groq.audio.transcriptions.create.assert_called_once_with(
        file=("test.mp3", audio_bytes),
        model="whisper-large-v3",
        response_format="verbose_json",
    )


def test_transcribe_audio_empty_bytes():
    mock_groq = MagicMock()
    with pytest.raises(TranscriptionError) as exc:
        transcribe_audio(audio_bytes=b"", client=mock_groq)
    assert "empty audio data" in str(exc.value)


def test_transcribe_audio_api_failure():
    mock_groq = MagicMock()
    mock_groq.audio.transcriptions.create.side_effect = Exception(
        "Groq API rate limit exceeded"
    )

    with pytest.raises(TranscriptionError) as exc:
        transcribe_audio(audio_bytes=b"AUDIO", client=mock_groq)
    assert "Speech-to-text transcription service failed" in str(exc.value)


def test_process_transcription_for_meeting_success():
    meeting_id = "meet-test-123"
    mock_db = MagicMock()
    mock_groq = MagicMock()

    # Mock get_meeting_record
    mock_select_response = MagicMock()
    mock_select_response.data = [
        {
            "meeting_id": meeting_id,
            "original_filename": "team_sync.mp3",
            "storage_path": "meetings/meet-test-123/audio.mp3",
            "status": "PENDING",
        }
    ]
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = (
        mock_select_response
    )

    # Mock download_audio_file
    mock_db.storage.from_.return_value.download.return_value = b"VALID_AUDIO_BYTES"

    # Mock transcribe_audio
    mock_transcription_response = MagicMock()
    mock_transcription_response.text = "Discussed Q3 release roadmap."
    mock_groq.audio.transcriptions.create.return_value = mock_transcription_response

    # Mock update_meeting_record
    mock_update_response = MagicMock()
    mock_update_response.data = [
        {
            "meeting_id": meeting_id,
            "transcript": "Discussed Q3 release roadmap.",
            "transcription_time": 3.45,
            "status": "SUMMARIZING",
        }
    ]
    mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = (
        mock_update_response
    )

    result = process_transcription_for_meeting(
        meeting_id=meeting_id, groq_client=mock_groq, supabase_client=mock_db
    )

    assert result["meeting_id"] == meeting_id
    assert result["status"] == "SUMMARIZING"
    assert result["transcript"] == "Discussed Q3 release roadmap."


def test_process_transcription_for_meeting_not_found():
    mock_db = MagicMock()
    mock_select_response = MagicMock()
    mock_select_response.data = []
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = (
        mock_select_response
    )

    with pytest.raises(TranscriptionError) as exc:
        process_transcription_for_meeting(
            meeting_id="nonexistent-id", supabase_client=mock_db
        )
    assert "not found" in str(exc.value)


def test_process_transcription_for_meeting_storage_download_failure():
    meeting_id = "meet-storage-fail"
    mock_db = MagicMock()

    mock_select_response = MagicMock()
    mock_select_response.data = [
        {
            "meeting_id": meeting_id,
            "storage_path": "meetings/meet-storage-fail/audio.wav",
            "status": "PENDING",
        }
    ]
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = (
        mock_select_response
    )
    mock_db.storage.from_.return_value.download.side_effect = Exception(
        "Storage file missing"
    )

    with pytest.raises(TranscriptionError) as exc:
        process_transcription_for_meeting(
            meeting_id=meeting_id, supabase_client=mock_db
        )
    assert "Failed to download audio recording" in str(exc.value)

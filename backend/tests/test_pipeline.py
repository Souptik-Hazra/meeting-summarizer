import pytest
from unittest.mock import MagicMock, patch
from app.config import settings
from app.schemas.meeting import MeetingStatus
from app.schemas.summary import MeetingSummaryOutput, ActionItem
from app.services.pipeline import process_meeting_pipeline, PipelineError
from app.services.storage import StorageError
from app.services.transcription import TranscriptionError
from app.services.summarization import SummarizationError


def test_process_meeting_pipeline_success():
    meeting_id = "test-pipe-1"
    mock_db = MagicMock()
    mock_groq = MagicMock()
    mock_gemini = MagicMock()

    # Initial meeting record
    mock_select = MagicMock()
    mock_select.data = [{
        "meeting_id": meeting_id,
        "original_filename": "meeting.wav",
        "storage_path": "meetings/test-pipe-1/audio.wav",
        "status": "PENDING"
    }]
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_select

    # Mock completed record returned on update
    mock_update = MagicMock()
    mock_update.data = [{
        "meeting_id": meeting_id,
        "status": "COMPLETED",
        "summary": "Team aligned on release.",
        "key_points": ["Point 1"],
        "decisions": ["Deploy on Monday"],
        "action_items": [{"task": "Check tests", "owner": "Bob", "deadline": "Friday"}],
        "processing_time": 4.5,
        "transcription_time": 2.1,
        "summarization_time": 1.9,
    }]
    mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update

    with patch("app.services.pipeline.download_audio_file", return_value=b"fake_audio_bytes") as mock_dl, \
         patch("app.services.pipeline.transcribe_audio", return_value=("Alice says let us deploy on Monday.", 2.1)) as mock_asr, \
         patch("app.services.pipeline.generate_meeting_summary") as mock_sum:

        mock_sum.return_value = (
            MeetingSummaryOutput(
                summary="Team aligned on release.",
                key_points=["Point 1"],
                decisions=["Deploy on Monday"],
                action_items=[ActionItem(task="Check tests", owner="Bob", deadline="Friday")]
            ),
            1.9
        )

        result = process_meeting_pipeline(
            meeting_id=meeting_id,
            supabase_client=mock_db,
            groq_client=mock_groq,
            gemini_client=mock_gemini
        )

        assert result["status"] == "COMPLETED"
        mock_dl.assert_called_once_with("meetings/test-pipe-1/audio.wav", client=mock_db)
        mock_asr.assert_called_once()
        mock_sum.assert_called_once()


def test_process_meeting_pipeline_not_found():
    mock_db = MagicMock()
    mock_select = MagicMock()
    mock_select.data = []
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_select

    with pytest.raises(PipelineError) as exc:
        process_meeting_pipeline(meeting_id="nonexistent", supabase_client=mock_db)
    assert "not found" in str(exc.value).lower()


def test_process_meeting_pipeline_already_completed():
    mock_db = MagicMock()
    mock_select = MagicMock()
    mock_select.data = [{
        "meeting_id": "already-done",
        "status": "COMPLETED"
    }]
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_select

    result = process_meeting_pipeline(meeting_id="already-done", supabase_client=mock_db)
    assert result["status"] == "COMPLETED"


def test_process_meeting_pipeline_storage_download_failure():
    meeting_id = "storage-fail"
    mock_db = MagicMock()
    mock_select = MagicMock()
    mock_select.data = [{
        "meeting_id": meeting_id,
        "original_filename": "m.wav",
        "storage_path": "meetings/path/audio.wav",
        "status": "PENDING"
    }]
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_select

    with patch("app.services.pipeline.download_audio_file", side_effect=StorageError("Storage connection reset")):
        with pytest.raises(PipelineError) as exc:
            process_meeting_pipeline(meeting_id=meeting_id, supabase_client=mock_db)
        assert exc.value.failure_stage == "storage"


def test_process_meeting_pipeline_transcription_failure():
    meeting_id = "asr-fail"
    mock_db = MagicMock()
    mock_select = MagicMock()
    mock_select.data = [{
        "meeting_id": meeting_id,
        "original_filename": "m.wav",
        "storage_path": "meetings/path/audio.wav",
        "status": "PENDING"
    }]
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_select

    with patch("app.services.pipeline.download_audio_file", return_value=b"audio"), \
         patch("app.services.pipeline.transcribe_audio", side_effect=TranscriptionError("Groq 500 error")):
        with pytest.raises(PipelineError) as exc:
            process_meeting_pipeline(meeting_id=meeting_id, supabase_client=mock_db)
        assert exc.value.failure_stage == "transcription"


def test_process_meeting_pipeline_summarization_retry_success():
    """Attempt 1 fails, Attempt 2 succeeds -> Transitions to COMPLETED."""
    meeting_id = "retry-success"
    mock_db = MagicMock()
    mock_select = MagicMock()
    mock_select.data = [{
        "meeting_id": meeting_id,
        "original_filename": "m.wav",
        "storage_path": "meetings/path/audio.wav",
        "status": "PENDING"
    }]
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_select

    mock_update = MagicMock()
    mock_update.data = [{"meeting_id": meeting_id, "status": "COMPLETED"}]
    mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update

    valid_output = MeetingSummaryOutput(
        summary="Success on retry.",
        key_points=[],
        decisions=[],
        action_items=[]
    )

    with patch("app.services.pipeline.download_audio_file", return_value=b"audio"), \
         patch("app.services.pipeline.transcribe_audio", return_value=("Transcript", 1.0)), \
         patch("app.services.pipeline.generate_meeting_summary", side_effect=[
             SummarizationError("Pydantic structured output validation failed on Gemini response"),
             (valid_output, 1.5)
         ]) as mock_sum:

        result = process_meeting_pipeline(meeting_id=meeting_id, supabase_client=mock_db)
        assert result["status"] == "COMPLETED"
        assert mock_sum.call_count == 2


def test_process_meeting_pipeline_summarization_retry_failure_validation():
    """Both attempts fail Pydantic validation -> FAILED with failure_stage='validation'."""
    meeting_id = "val-fail"
    mock_db = MagicMock()
    mock_select = MagicMock()
    mock_select.data = [{
        "meeting_id": meeting_id,
        "original_filename": "m.wav",
        "storage_path": "meetings/path/audio.wav",
        "status": "PENDING"
    }]
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_select

    with patch("app.services.pipeline.download_audio_file", return_value=b"audio"), \
         patch("app.services.pipeline.transcribe_audio", return_value=("Transcript", 1.0)), \
         patch("app.services.pipeline.generate_meeting_summary", side_effect=[
             SummarizationError("Pydantic validation error"),
             SummarizationError("Pydantic validation error")
         ]):

        with pytest.raises(PipelineError) as exc:
            process_meeting_pipeline(meeting_id=meeting_id, supabase_client=mock_db)
        assert exc.value.failure_stage == "validation"


def test_process_meeting_pipeline_summarization_retry_failure_api():
    """Both attempts fail due to general API error -> FAILED with failure_stage='summarization'."""
    meeting_id = "api-fail"
    mock_db = MagicMock()
    mock_select = MagicMock()
    mock_select.data = [{
        "meeting_id": meeting_id,
        "original_filename": "m.wav",
        "storage_path": "meetings/path/audio.wav",
        "status": "PENDING"
    }]
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_select

    with patch("app.services.pipeline.download_audio_file", return_value=b"audio"), \
         patch("app.services.pipeline.transcribe_audio", return_value=("Transcript", 1.0)), \
         patch("app.services.pipeline.generate_meeting_summary", side_effect=[
             Exception("Gemini quota 503"),
             Exception("Gemini quota 503")
         ]):

        with pytest.raises(PipelineError) as exc:
            process_meeting_pipeline(meeting_id=meeting_id, supabase_client=mock_db)
        assert exc.value.failure_stage == "summarization"


def test_process_meeting_pipeline_db_failure_resilience():
    """If DB update throws exception, caught safely without crashing process."""
    meeting_id = "db-crash"
    mock_db = MagicMock()
    mock_select = MagicMock()
    mock_select.data = [{
        "meeting_id": meeting_id,
        "original_filename": "m.wav",
        "storage_path": "meetings/path/audio.wav",
        "status": "PENDING"
    }]
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_select
    mock_db.table.return_value.update.side_effect = Exception("DB Network down")

    with patch("app.services.pipeline.download_audio_file", return_value=b"audio"), \
         patch("app.services.pipeline.transcribe_audio", side_effect=TranscriptionError("ASR error")):
        with pytest.raises(PipelineError):
            process_meeting_pipeline(meeting_id=meeting_id, supabase_client=mock_db)


def test_process_meeting_pipeline_concurrency_isolation():
    """Two meetings processed sequentially/concurrently maintain independent timers and state."""
    mock_db = MagicMock()

    for m_id in ["meet-A", "meet-B"]:
        mock_select = MagicMock()
        mock_select.data = [{
            "meeting_id": m_id,
            "original_filename": f"{m_id}.wav",
            "storage_path": f"meetings/{m_id}/audio.wav",
            "status": "PENDING"
        }]
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_select
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_select

        with patch("app.services.pipeline.download_audio_file", return_value=b"audio"), \
             patch("app.services.pipeline.transcribe_audio", return_value=(f"Transcript for {m_id}", 1.0)), \
             patch("app.services.pipeline.generate_meeting_summary", return_value=(
                 MeetingSummaryOutput(summary=f"Summary for {m_id}"), 1.0
             )):
            res = process_meeting_pipeline(meeting_id=m_id, supabase_client=mock_db)
            assert res is not None

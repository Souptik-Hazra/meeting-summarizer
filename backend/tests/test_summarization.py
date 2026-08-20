import pytest
from unittest.mock import MagicMock, patch
from app.config import settings
from app.schemas.summary import MeetingSummaryOutput, ActionItem
from app.schemas.meeting import MeetingStatus
from app.services.summarization import (
    SummarizationError,
    load_prompt_template,
    generate_meeting_summary,
    process_summarization_for_meeting,
)


def test_load_prompt_template_success():
    template = load_prompt_template("v1")
    assert "UNTRUSTED DATA" in template
    assert "ACTION ITEMS" in template
    assert "DECISIONS" in template


def test_load_prompt_template_missing():
    with pytest.raises(SummarizationError) as exc:
        load_prompt_template("v999_nonexistent")
    assert "not found" in str(exc.value).lower()


def test_generate_meeting_summary_success():
    mock_gemini = MagicMock()
    mock_response = MagicMock()
    mock_response.parsed = MeetingSummaryOutput(
        summary="Weekly sprint planning completed.",
        key_points=["Goal is to release MVP", "QA starts Wednesday"],
        decisions=["Ship MVP on Friday"],
        action_items=[ActionItem(task="Write integration tests", owner="Bob", deadline="Thursday")]
    )
    mock_gemini.models.generate_content.return_value = mock_response

    output, elapsed = generate_meeting_summary("Team discussed sprint goals.", client=mock_gemini)
    assert output.summary == "Weekly sprint planning completed."
    assert len(output.key_points) == 2
    assert len(output.decisions) == 1
    assert output.action_items[0].owner == "Bob"
    assert isinstance(elapsed, float)
    assert elapsed >= 0


def test_generate_meeting_summary_json_text_fallback():
    mock_gemini = MagicMock()
    mock_response = MagicMock()
    mock_response.parsed = None
    mock_response.text = '{"summary": "Fallback summary", "key_points": ["P1"], "decisions": [], "action_items": []}'
    mock_gemini.models.generate_content.return_value = mock_response

    output, elapsed = generate_meeting_summary("Transcript content", client=mock_gemini)
    assert output.summary == "Fallback summary"
    assert output.key_points == ["P1"]


def test_generate_meeting_summary_empty_transcript():
    mock_gemini = MagicMock()
    with pytest.raises(SummarizationError) as exc:
        generate_meeting_summary("", client=mock_gemini)
    assert "empty or whitespace" in str(exc.value).lower()


def test_generate_meeting_summary_api_failure():
    mock_gemini = MagicMock()
    mock_gemini.models.generate_content.side_effect = Exception("Gemini quota exceeded")

    with pytest.raises(SummarizationError) as exc:
        generate_meeting_summary("Transcript content", client=mock_gemini)
    assert "Generative AI summarization service failed" in str(exc.value)


def test_generate_meeting_summary_invalid_structured_output():
    mock_gemini = MagicMock()
    mock_response = MagicMock()
    mock_response.parsed = None
    mock_response.text = '{"invalid_structure": "malformed data without summary"}'
    mock_gemini.models.generate_content.return_value = mock_response

    with pytest.raises(SummarizationError) as exc:
        generate_meeting_summary("Transcript content", client=mock_gemini)
    assert "structured output validation" in str(exc.value).lower()


def test_process_summarization_for_meeting_success():
    meeting_id = "meet-sum-123"
    mock_db = MagicMock()
    mock_gemini = MagicMock()

    # Mock get_meeting_record
    mock_select = MagicMock()
    mock_select.data = [{
        "meeting_id": meeting_id,
        "status": "SUMMARIZING",
        "transcript": "Speaker 1: We agreed to launch the beta next week."
    }]
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_select

    # Mock Gemini response
    mock_response = MagicMock()
    mock_response.parsed = MeetingSummaryOutput(
        summary="Team agreed to launch the beta next week.",
        key_points=["Beta launch next week"],
        decisions=["Launch beta"],
        action_items=[ActionItem(task="Prepare beta build", owner="Alice", deadline="Monday")]
    )
    mock_gemini.models.generate_content.return_value = mock_response

    # Mock DB update response
    mock_update = MagicMock()
    mock_update.data = [{
        "meeting_id": meeting_id,
        "status": "COMPLETED",
        "summary": "Team agreed to launch the beta next week.",
        "key_points": ["Beta launch next week"],
        "decisions": ["Launch beta"],
        "action_items": [{"task": "Prepare beta build", "owner": "Alice", "deadline": "Monday"}],
        "model_name": settings.GEMINI_MODEL,
        "prompt_version": "v1",
        "summarization_time": 2.15
    }]
    mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update

    result = process_summarization_for_meeting(
        meeting_id=meeting_id,
        gemini_client=mock_gemini,
        supabase_client=mock_db
    )

    assert result["meeting_id"] == meeting_id
    assert result["status"] == "COMPLETED"
    assert result["summary"] == "Team agreed to launch the beta next week."


def test_process_summarization_for_meeting_not_found():
    mock_db = MagicMock()
    mock_select = MagicMock()
    mock_select.data = []
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_select

    with pytest.raises(SummarizationError) as exc:
        process_summarization_for_meeting(meeting_id="nonexistent-id", supabase_client=mock_db)
    assert "not found" in str(exc.value).lower()


def test_process_summarization_for_meeting_invalid_state():
    mock_db = MagicMock()
    mock_select = MagicMock()
    mock_select.data = [{
        "meeting_id": "meet-wrong-state",
        "status": "PENDING",  # Must strictly be SUMMARIZING
        "transcript": "Transcript exists."
    }]
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_select

    with pytest.raises(SummarizationError) as exc:
        process_summarization_for_meeting(meeting_id="meet-wrong-state", supabase_client=mock_db)
    assert "requires status 'SUMMARIZING'" in str(exc.value)


def test_process_summarization_for_meeting_missing_transcript():
    mock_db = MagicMock()
    mock_select = MagicMock()
    mock_select.data = [{
        "meeting_id": "meet-no-transcript",
        "status": "SUMMARIZING",
        "transcript": ""  # Missing transcript
    }]
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_select

    with pytest.raises(SummarizationError) as exc:
        process_summarization_for_meeting(meeting_id="meet-no-transcript", supabase_client=mock_db)
    assert "no transcript available" in str(exc.value).lower()

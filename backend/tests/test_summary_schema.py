import pytest
from pydantic import ValidationError
from app.schemas.summary import ActionItem, MeetingSummaryOutput, MeetingSummarizeResponse


def test_action_item_valid():
    item = ActionItem(task="Deploy staging environment", owner="Alice", deadline="Friday")
    assert item.task == "Deploy staging environment"
    assert item.owner == "Alice"
    assert item.deadline == "Friday"


def test_action_item_nullable_fields():
    item = ActionItem(task="Review PR")
    assert item.task == "Review PR"
    assert item.owner is None
    assert item.deadline is None


def test_action_item_missing_task():
    with pytest.raises(ValidationError):
        ActionItem(owner="Bob")


def test_meeting_summary_output_valid():
    data = {
        "summary": "The team discussed the Q3 product release.",
        "key_points": ["Backend API is ready", "Frontend styling updated"],
        "decisions": ["Deploy on Monday"],
        "action_items": [
            {"task": "Run end-to-end tests", "owner": "John", "deadline": "Sunday"}
        ]
    }
    output = MeetingSummaryOutput.model_validate(data)
    assert output.summary == "The team discussed the Q3 product release."
    assert len(output.key_points) == 2
    assert len(output.decisions) == 1
    assert len(output.action_items) == 1
    assert output.action_items[0].owner == "John"


def test_meeting_summary_output_defaults():
    output = MeetingSummaryOutput(summary="Quick sync on architecture.")
    assert output.summary == "Quick sync on architecture."
    assert output.key_points == []
    assert output.decisions == []
    assert output.action_items == []


def test_meeting_summary_output_missing_summary():
    with pytest.raises(ValidationError):
        MeetingSummaryOutput(key_points=["Topic 1"])


def test_meeting_summary_output_invalid_types():
    with pytest.raises(ValidationError):
        MeetingSummaryOutput(summary=12345, key_points="Not a list")


def test_meeting_summarize_response():
    resp = MeetingSummarizeResponse(
        meeting_id="meet-123",
        status="COMPLETED",
        summary="Brief summary",
        key_points=["Point 1"],
        decisions=["Decision 1"],
        action_items=[{"task": "Do X", "owner": None, "deadline": None}],
        summarization_time=2.45,
        model_name="gemini-2.5-flash",
        prompt_version="v1"
    )
    assert resp.meeting_id == "meet-123"
    assert resp.status == "COMPLETED"
    assert resp.model_name == "gemini-2.5-flash"

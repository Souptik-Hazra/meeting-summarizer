from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


class ActionItem(BaseModel):
    """Structured action item extracted from meeting transcript."""

    model_config = ConfigDict(extra="ignore")

    task: str = Field(..., description="Actionable task description")
    owner: Optional[str] = Field(
        None, description="Person responsible, or None if unstated"
    )
    deadline: Optional[str] = Field(
        None, description="Due date or timeframe, or None if unstated"
    )


class MeetingSummaryOutput(BaseModel):
    """Structured meeting intelligence output from Gemini 2.5 Flash."""

    model_config = ConfigDict(extra="ignore")

    summary: str = Field(..., description="Concise executive meeting summary")
    key_points: List[str] = Field(
        default_factory=list, description="Key discussion topics and takeaways"
    )
    decisions: List[str] = Field(
        default_factory=list, description="Explicit decisions made in the meeting"
    )
    action_items: List[ActionItem] = Field(
        default_factory=list, description="Assigned action items and tasks"
    )


class MeetingSummarizeResponse(BaseModel):
    """API response schema for meeting summarization endpoint."""

    model_config = ConfigDict(from_attributes=True)

    meeting_id: str
    status: str
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    decisions: Optional[List[str]] = None
    action_items: Optional[List[Dict[str, Any]]] = None
    summarization_time: Optional[float] = None
    model_name: Optional[str] = None
    prompt_version: Optional[str] = None

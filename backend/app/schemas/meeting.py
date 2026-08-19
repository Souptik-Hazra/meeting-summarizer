from enum import Enum
from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class MeetingStatus(str, Enum):
    PENDING = "PENDING"
    TRANSCRIBING = "TRANSCRIBING"
    SUMMARIZING = "SUMMARIZING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MeetingBase(BaseModel):
    meeting_id: str
    original_filename: str
    storage_path: Optional[str] = None
    status: MeetingStatus = MeetingStatus.PENDING


class MeetingCreate(BaseModel):
    meeting_id: str
    original_filename: str
    storage_path: Optional[str] = None
    status: MeetingStatus = MeetingStatus.PENDING


class MeetingStatusUpdate(BaseModel):
    status: MeetingStatus
    failure_stage: Optional[str] = None
    error_message: Optional[str] = None


class MeetingStatusResponse(BaseModel):
    meeting_id: str
    status: MeetingStatus
    failure_stage: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MeetingResponse(BaseModel):
    meeting_id: str
    original_filename: str
    storage_path: Optional[str] = None
    status: MeetingStatus
    transcript: Optional[str] = None
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    decisions: Optional[List[str]] = None
    action_items: Optional[List[Dict[str, Any]]] = None
    model_name: Optional[str] = None
    prompt_version: Optional[str] = None
    transcription_time: Optional[float] = None
    summarization_time: Optional[float] = None
    processing_time: Optional[float] = None
    failure_stage: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


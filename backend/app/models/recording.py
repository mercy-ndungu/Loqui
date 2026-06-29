"""Recording request and response schemas."""

from datetime import datetime

from pydantic import BaseModel


class RecordingUploadResponse(BaseModel):
    """Response after a successful recording upload."""

    id: str
    video_url: str
    transcription: str
    created_at: datetime


class RecordingDetailResponse(BaseModel):
    """Full recording details returned by GET /recordings/{id}."""

    id: str
    presentation_id: str
    video_url: str
    transcription: str
    duration_seconds: int | None
    created_at: datetime


class DeleteRecordingResponse(BaseModel):
    """Response after deleting a recording."""

    message: str

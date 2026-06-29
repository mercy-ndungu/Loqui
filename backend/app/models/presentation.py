"""Presentation request and response schemas."""

from datetime import datetime

from pydantic import BaseModel


class PresentationUploadResponse(BaseModel):
    """Response after a successful presentation upload."""

    id: str
    title: str
    url: str
    created_at: datetime


class PresentationSummaryResponse(BaseModel):
    """Summary item returned by GET /presentations."""

    id: str
    title: str
    created_at: datetime
    file_url: str


class PresentationDetailResponse(BaseModel):
    """Full presentation details returned by GET /presentations/{id}."""

    id: str
    title: str
    presentation_type: str
    url: str | None = None
    created_at: datetime
    challenge_metadata: dict | None = None


class DeletePresentationResponse(BaseModel):
    """Response after deleting a presentation."""

    message: str

"""Challenge request and response schemas."""

from datetime import datetime

from pydantic import BaseModel

from app.models.feedback import FeedbackScores


class ImprovImage(BaseModel):
    """A single improv prompt image."""

    url: str
    alt: str


class ImprovChallengeResponse(BaseModel):
    """Response after generating an improv challenge."""

    challenge_id: str
    images: list[ImprovImage]


class RandomTopicChallengeResponse(BaseModel):
    """Response after generating a random topic challenge."""

    challenge_id: str
    topic: str


class ChallengeSummaryResponse(BaseModel):
    """Summary of a completed challenge for the dashboard."""

    id: str
    challenge_type: str
    title: str
    topic_or_images: str | None = None
    completed_at: datetime | None = None
    overall_score: int | None = None


class ChallengeUploadResponse(BaseModel):
    """Response after uploading and analyzing a challenge recording."""

    challenge_id: str
    feedback_scores: FeedbackScores
    overall_score: int
    improvements: list[str]
    strengths: list[str]
    feedback_text: dict[str, str]

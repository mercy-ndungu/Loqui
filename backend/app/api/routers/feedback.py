"""AI eloquence feedback routes (local spaCy + NLTK scoring)."""

import logging

from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import CurrentUser
from app.core.limiter import limiter
from app.models import FeedbackAnalyzeRequest, FeedbackAnalyzeResponse, FeedbackScores
from app.services import challenge_storage_service, feedback_service, language_score_service, recording_service
from app.services.language_score_service import EloquenceAnalysisResult
from app.utils.rate_limit import get_user_or_ip_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


def _require_owned_recording(recording_id: str, user_id: str) -> dict:
    """Load a recording and verify the authenticated user owns it."""
    recording = recording_service.get_recording_by_id(recording_id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found",
        )
    if not recording_service.user_owns_recording(recording, user_id):
        logger.warning(
            "Forbidden feedback request for recording_id=%s by user_id=%s",
            recording_id,
            user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )
    return recording


def _build_response(analysis: EloquenceAnalysisResult) -> FeedbackAnalyzeResponse:
    """Map local analysis to the API response schema."""
    feedback_text = {
        "grammar": analysis.grammar_feedback,
        "vocabulary": analysis.vocabulary_feedback,
        "pacing": analysis.pacing_feedback,
        "filler_words": analysis.filler_words.improvement,
    }
    return FeedbackAnalyzeResponse(
        scores=FeedbackScores(
            grammar=analysis.grammar_score,
            vocabulary=analysis.vocabulary_score,
            filler_words_count=analysis.filler_words.count,
            pacing=analysis.pacing_score,
            overall=analysis.overall_score,
        ),
        feedback_text=feedback_text,
        improvements=analysis.top_3_improvements,
        strengths=analysis.strengths,
    )


@router.post("/analyze", response_model=FeedbackAnalyzeResponse)
@limiter.limit("10/minute", key_func=get_user_or_ip_key)
async def analyze_feedback(
    request: Request,
    payload: FeedbackAnalyzeRequest,
    current_user: CurrentUser,
) -> FeedbackAnalyzeResponse:
    """
    Analyze a recording transcription with local spaCy/NLTK eloquence scoring.

    Free, on-server processing — no external API calls. Same metric for all
    challenge types (presentations, improv, topics).
    """
    _require_owned_recording(payload.recording_id, current_user.id)

    try:
        analysis = language_score_service.score_eloquence(payload.transcription)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analysis failed",
        )

    feedback_json = analysis.model_dump(by_alias=True)
    stored = feedback_service.create_feedback_record(
        recording_id=payload.recording_id,
        feedback_json=feedback_json,
    )
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analysis failed",
        )

    logger.info(
        "Local eloquence analysis stored user_id=%s recording_id=%s overall=%s feedback_id=%s",
        current_user.id,
        payload.recording_id,
        analysis.overall_score,
        stored["id"],
    )

    return _build_response(analysis)


def _feedback_from_json(feedback_json: dict) -> FeedbackAnalyzeResponse:
    """Rebuild API response from stored feedback_json."""
    analysis = EloquenceAnalysisResult.model_validate(feedback_json)
    return _build_response(analysis)


@router.get("/{recording_id}", response_model=FeedbackAnalyzeResponse)
@limiter.limit("60/minute", key_func=get_user_or_ip_key)
async def get_feedback(
    request: Request,
    recording_id: str,
    current_user: CurrentUser,
) -> FeedbackAnalyzeResponse:
    """Return stored eloquence feedback for a recording or challenge."""
    record = feedback_service.get_feedback_by_recording_id(recording_id)
    if record:
        recording = recording_service.get_recording_by_id(recording_id)
        if not recording or not recording_service.user_owns_recording(recording, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            )
        return _feedback_from_json(record["feedback_json"])

    challenge_record = feedback_service.get_feedback_by_challenge_id(recording_id)
    if challenge_record:
        challenge = challenge_storage_service.get_challenge_by_id(recording_id)
        if not challenge or not challenge_storage_service.user_can_submit_challenge(
            challenge, current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            )
        return _feedback_from_json(challenge_record["feedback_json"])

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Feedback not found",
    )

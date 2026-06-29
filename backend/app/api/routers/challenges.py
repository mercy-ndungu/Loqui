"""Challenge mode routes for improv and random topic practice."""

import logging

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status

from app.api.deps import CurrentUser, OptionalUser
from app.core.limiter import limiter
from app.models import (
    ChallengeSummaryResponse,
    ChallengeUploadResponse,
    FeedbackScores,
    ImprovChallengeResponse,
    RandomTopicChallengeResponse,
)
from app.services import audio_service, challenge_service
from app.services.language_score_service import EloquenceAnalysisResult
from app.utils.file_validation import MAX_UPLOAD_BYTES
from app.utils.streaming import read_upload_with_limit
from app.utils.video_validation import VideoValidationError, validate_video_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/challenges", tags=["challenges"])


def _build_upload_response(
    challenge_id: str,
    analysis: EloquenceAnalysisResult,
) -> ChallengeUploadResponse:
    """Map Claude analysis to the challenge upload response."""
    return ChallengeUploadResponse(
        challenge_id=challenge_id,
        feedback_scores=FeedbackScores(
            grammar=analysis.grammar_score,
            vocabulary=analysis.vocabulary_score,
            filler_words_count=analysis.filler_words.count,
            pacing=analysis.pacing_score,
            overall=analysis.overall_score,
        ),
        overall_score=analysis.overall_score,
        improvements=analysis.top_3_improvements,
        strengths=analysis.strengths,
        feedback_text={
            "grammar": analysis.grammar_feedback,
            "vocabulary": analysis.vocabulary_feedback,
            "pacing": analysis.pacing_feedback,
            "filler_words": analysis.filler_words.improvement,
        },
    )


def _generate_improv(user_id: str | None) -> ImprovChallengeResponse:
    """Shared logic for GET/POST improv generation."""
    result = challenge_service.generate_improv_challenge(user_id=user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not generate improv images. Please try again.",
        )
    logger.info(
        "Improv challenge created challenge_id=%s user_id=%s images=%d",
        result["challenge_id"],
        user_id,
        len(result["images"]),
    )
    return ImprovChallengeResponse(**result)


@router.get("", response_model=list[ChallengeSummaryResponse])
@limiter.limit("60/minute")
async def list_challenges(
    request: Request,
    current_user: CurrentUser,
) -> list[ChallengeSummaryResponse]:
    """Return recent completed challenges for the authenticated user."""
    records = challenge_service.list_recent_challenges(user_id=current_user.id)
    return [ChallengeSummaryResponse(**record) for record in records]


@router.get(
    "/improv/generate",
    response_model=ImprovChallengeResponse,
)
@limiter.limit("10/minute")
async def get_improv_challenge(
    request: Request,
    current_user: OptionalUser,
) -> ImprovChallengeResponse:
    """
    Generate an improv challenge with 5 random Unsplash images.

    Public endpoint — no login required.
    """
    user_id = current_user.id if current_user else None
    return _generate_improv(user_id)


@router.post(
    "/improv/generate",
    response_model=ImprovChallengeResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
async def post_improv_challenge(
    request: Request,
    current_user: OptionalUser,
) -> ImprovChallengeResponse:
    """POST alias for improv image generation (public)."""
    user_id = current_user.id if current_user else None
    return _generate_improv(user_id)


@router.post(
    "/topics/random",
    response_model=RandomTopicChallengeResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
async def generate_random_topic(
    request: Request,
    current_user: OptionalUser,
) -> RandomTopicChallengeResponse:
    """
    Generate a dynamic speaking topic via Claude API.

    Public endpoint — no login required.
    """
    user_id = current_user.id if current_user else None
    result = challenge_service.generate_dynamic_topic(user_id=user_id)
    if not result:
        logger.error("Topic generation failed user_id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not generate topic. Please try again.",
        )
    logger.info(
        "Topic challenge created challenge_id=%s user_id=%s topic=%r",
        result["challenge_id"],
        user_id,
        result["topic"][:80],
    )
    return RandomTopicChallengeResponse(**result)


@router.post(
    "/upload",
    response_model=ChallengeUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("2/minute")
async def upload_challenge_recording(
    request: Request,
    current_user: CurrentUser,
    challenge_id: str = Form(...),
    challenge_type: str = Form(...),
    duration_seconds: int = Form(...),
    video_file: UploadFile = File(...),
) -> ChallengeUploadResponse:
    """
    Upload a challenge recording, transcribe speech, and return eloquence feedback.

    Requires JWT authentication. Uses the same Claude eloquence scoring as presentations.
    """
    logger.info(
        "Challenge upload request user_id=%s challenge_id=%s type=%s duration=%s",
        current_user.id,
        challenge_id,
        challenge_type,
        duration_seconds,
    )

    if challenge_type not in challenge_service.VALID_UPLOAD_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid challenge type. Use 'improv' or 'topic'.",
        )

    if duration_seconds <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recording duration must be greater than zero.",
        )

    if not audio_service.ffmpeg_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Video processing is unavailable. ffmpeg is not installed on the server.",
        )

    try:
        content = await read_upload_with_limit(video_file, MAX_UPLOAD_BYTES)
        validated = validate_video_upload(
            filename=video_file.filename,
            content_type=video_file.content_type,
            content=content,
        )
    except VideoValidationError as exc:
        logger.warning(
            "Challenge video validation failed user_id=%s challenge_id=%s: %s",
            current_user.id,
            challenge_id,
            exc.message,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        ) from exc

    try:
        analysis, _updated = challenge_service.process_challenge_upload(
            user_id=current_user.id,
            challenge_id=challenge_id,
            challenge_type=challenge_type,
            video_content=content,
            filename=video_file.filename or "recording.webm",
            content_type=video_file.content_type,
            duration_seconds=duration_seconds,
            validated_mime=validated.mime_type,
            validated_extension=validated.extension,
            sanitized_filename=validated.sanitized_filename,
        )
    except ValueError as exc:
        logger.warning(
            "Challenge upload rejected user_id=%s challenge_id=%s: %s",
            current_user.id,
            challenge_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Challenge processing failed. Please try again.",
        )

    return _build_upload_response(challenge_id, analysis)

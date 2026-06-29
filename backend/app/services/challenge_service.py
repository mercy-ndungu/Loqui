"""Challenge generation, upload, transcription, and feedback orchestration."""

import logging
import random
from typing import Any

from app.data.improv_images import generate_improv_images
from app.data.topics import RANDOM_TOPICS
from app.services import (
    audio_service,
    challenge_storage_service,
    claude_service,
    feedback_service,
    language_score_service,
    transcription_service,
)
from app.services.language_score_service import EloquenceAnalysisResult
from app.utils.encryption import encrypt_text

logger = logging.getLogger(__name__)

CHALLENGE_TYPE_IMPROV = "improv"
CHALLENGE_TYPE_TOPIC = "topic"
VALID_UPLOAD_TYPES = frozenset({CHALLENGE_TYPE_IMPROV, CHALLENGE_TYPE_TOPIC})


def _fallback_topic() -> str:
    """Static fallback when Claude topic generation is unavailable."""
    return random.choice(RANDOM_TOPICS)


def generate_dynamic_topic(*, user_id: str | None = None) -> dict[str, Any] | None:
    """
    Generate a speaking topic via Claude API and persist a pending challenge row.

    Falls back to the static topic list if Claude is unavailable.
    """
    topic, usage = claude_service.generate_speaking_topic()
    if not topic:
        logger.warning("Claude topic generation failed; using static fallback topic")
        topic = _fallback_topic()
    elif usage:
        logger.info("Dynamic topic created via Claude model=%s", usage.model)

    record = challenge_storage_service.create_challenge_record(
        user_id=user_id,
        challenge_type=CHALLENGE_TYPE_TOPIC,
        title="Random Topic Challenge",
        topic_or_images=topic,
        metadata={"topic": topic, "generated_by": "claude" if usage else "fallback"},
    )
    if not record:
        return None

    return {
        "challenge_id": str(record["id"]),
        "topic": topic,
    }


def generate_improv_challenge(*, user_id: str | None = None) -> dict[str, Any] | None:
    """Create an improv challenge with 5 random Unsplash images."""
    images = generate_improv_images()
    logger.info("Improv challenge generated with %d images", len(images))
    record = challenge_storage_service.create_challenge_record(
        user_id=user_id,
        challenge_type=CHALLENGE_TYPE_IMPROV,
        title="Improv Pictures Challenge",
        topic_or_images=f"{len(images)} images",
        metadata={"images": images},
    )
    if not record:
        return None

    return {
        "challenge_id": str(record["id"]),
        "images": images,
    }


def list_recent_challenges(*, user_id: str) -> list[dict[str, Any]]:
    """Return recent completed challenges with optional feedback scores."""
    records = challenge_storage_service.list_completed_challenges(user_id)
    results: list[dict[str, Any]] = []
    for record in records:
        feedback = feedback_service.get_feedback_by_challenge_id(str(record["id"]))
        overall_score = None
        if feedback and feedback.get("feedback_json"):
            overall_score = feedback["feedback_json"].get("overall_score")
        results.append(
            {
                "id": str(record["id"]),
                "challenge_type": record["challenge_type"],
                "title": record["title"],
                "topic_or_images": record.get("topic_or_images"),
                "completed_at": record.get("completed_at"),
                "overall_score": overall_score,
            }
        )
    return results


def process_challenge_upload(
    *,
    user_id: str,
    challenge_id: str,
    challenge_type: str,
    video_content: bytes,
    filename: str,
    content_type: str | None,
    duration_seconds: int,
    validated_mime: str,
    validated_extension: str,
    sanitized_filename: str,
) -> tuple[EloquenceAnalysisResult | None, dict[str, Any] | None]:
    """
    Upload video, transcribe, analyze eloquence, and persist results.

    Returns (analysis, updated_challenge) or (None, None) on failure.
    Raises ValueError with helpful messages for client-facing errors.
    """
    logger.info(
        "Challenge upload started challenge_id=%s user_id=%s type=%s "
        "duration=%ss size=%d bytes mime=%s filename=%r",
        challenge_id,
        user_id,
        challenge_type,
        duration_seconds,
        len(video_content),
        validated_mime,
        sanitized_filename,
    )

    if not challenge_storage_service.bucket_accessible():
        logger.error(
            "Recordings bucket inaccessible during challenge upload challenge_id=%s",
            challenge_id,
        )
        raise ValueError(
            "Video storage is unavailable. Ensure the Supabase 'recordings' bucket "
            "exists and is configured as private."
        )

    challenge = challenge_storage_service.get_challenge_by_id(challenge_id)
    if not challenge:
        logger.error("Challenge not found challenge_id=%s", challenge_id)
        raise ValueError("Challenge not found.")
    if not challenge_storage_service.user_can_submit_challenge(challenge, user_id):
        logger.warning(
            "Challenge upload forbidden challenge_id=%s user_id=%s owner=%s",
            challenge_id,
            user_id,
            challenge.get("user_id"),
        )
        raise ValueError("You do not have access to this challenge.")
    if challenge["challenge_type"] != challenge_type:
        raise ValueError(
            f"Challenge type mismatch. Expected '{challenge['challenge_type']}'."
        )
    if challenge.get("completed_at"):
        raise ValueError("This challenge has already been submitted.")

    if challenge.get("user_id") is None:
        if not challenge_storage_service.assign_challenge_user(challenge_id, user_id):
            raise ValueError("Could not claim this challenge. Please generate a new one.")

    storage_path = challenge_storage_service.upload_video(
        user_id=user_id,
        challenge_id=challenge_id,
        filename=sanitized_filename,
        content=video_content,
        mime_type=validated_mime,
    )
    if not storage_path:
        logger.error(
            "Challenge video storage failed challenge_id=%s user_id=%s",
            challenge_id,
            user_id,
        )
        raise ValueError(
            "Could not save your video. Verify the Supabase 'recordings' bucket exists, "
            "is private, and that your service role key has storage access."
        )

    logger.info(
        "Challenge video stored challenge_id=%s storage_path=%s",
        challenge_id,
        storage_path,
    )

    audio_path = audio_service.extract_audio_to_wav(video_content, validated_extension)
    if not audio_path:
        challenge_storage_service.delete_storage_file(storage_path)
        logger.error("Audio extraction failed challenge_id=%s", challenge_id)
        raise ValueError(
            "Could not extract audio from the video. Re-record in MP4 or WebM format."
        )

    try:
        logger.info("Starting transcription challenge_id=%s", challenge_id)
        transcription = transcription_service.transcribe_audio(audio_path)
    finally:
        audio_service.cleanup_temp_dir(audio_path)

    if not transcription:
        challenge_storage_service.delete_storage_file(storage_path)
        logger.error("Transcription failed challenge_id=%s", challenge_id)
        raise ValueError(
            "Transcription failed. Speak clearly, reduce background noise, and try again."
        )

    logger.info(
        "Transcription complete challenge_id=%s chars=%d",
        challenge_id,
        len(transcription),
    )

    try:
        analysis = language_score_service.score_eloquence(transcription)
    except ValueError as exc:
        challenge_storage_service.delete_storage_file(storage_path)
        raise ValueError(str(exc)) from exc

    if not analysis:
        challenge_storage_service.delete_storage_file(storage_path)
        logger.error("Eloquence analysis failed challenge_id=%s", challenge_id)
        raise ValueError("Eloquence analysis failed. Please try again.")

    encrypted = encrypt_text(transcription)
    updated = challenge_storage_service.update_challenge_after_upload(
        challenge_id=challenge_id,
        storage_path=storage_path,
        duration_seconds=duration_seconds,
        transcription_encrypted=encrypted,
    )
    if not updated:
        challenge_storage_service.delete_storage_file(storage_path)
        raise ValueError("Could not save challenge results. Please try again.")

    stored_feedback = feedback_service.create_feedback_record(
        challenge_id=challenge_id,
        feedback_json=analysis.model_dump(by_alias=True),
    )
    if not stored_feedback:
        logger.error("Feedback storage failed for challenge_id=%s", challenge_id)

    logger.info(
        "Challenge upload complete challenge_id=%s user_id=%s type=%s overall=%s",
        challenge_id,
        user_id,
        challenge_type,
        analysis.overall_score,
    )
    return analysis, updated

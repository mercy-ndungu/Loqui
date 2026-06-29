"""Recording upload and management routes."""

import logging

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status

from app.api.deps import CurrentUser
from app.core.limiter import limiter
from app.models import (
    DeleteRecordingResponse,
    RecordingDetailResponse,
    RecordingUploadResponse,
)
from app.services import audio_service, recording_service, transcription_service
from app.utils.encryption import decrypt_text, encrypt_text
from app.utils.file_validation import MAX_UPLOAD_BYTES
from app.utils.streaming import read_upload_with_limit
from app.utils.video_validation import VideoValidationError, validate_video_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recordings", tags=["recordings"])


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
            "Forbidden access to recording id=%s by user_id=%s",
            recording_id,
            user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )
    return recording


@router.post(
    "/upload",
    response_model=RecordingUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("2/minute")
async def upload_recording(
    request: Request,
    current_user: CurrentUser,
    presentation_id: str = Form(...),
    duration_seconds: int = Form(...),
    video_file: UploadFile = File(...),
) -> RecordingUploadResponse:
    """
    Upload a practice recording video, transcribe speech, and store securely.

    Validates ownership of the presentation, uploads video to Supabase Storage,
    extracts audio via ffmpeg, transcribes with Whisper, and encrypts the
    transcription at rest.
    """
    if duration_seconds <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recording duration must be greater than zero.",
        )

    if not recording_service.bucket_accessible():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Video storage is unavailable. Ensure the Supabase 'recordings' bucket "
                "exists and is configured as private."
            ),
        )

    if not recording_service.user_owns_presentation(presentation_id, current_user.id):
        logger.warning(
            "Upload rejected: user_id=%s does not own presentation_id=%s",
            current_user.id,
            presentation_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )

    if not audio_service.ffmpeg_available():
        logger.error("ffmpeg unavailable during recording upload")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Video processing is unavailable. ffmpeg is not installed on the server.",
        )

    logger.info(
        "Recording upload started user_id=%s presentation_id=%s duration=%ss "
        "filename=%r content_type=%r",
        current_user.id,
        presentation_id,
        duration_seconds,
        video_file.filename,
        video_file.content_type,
    )

    try:
        content = await read_upload_with_limit(video_file, MAX_UPLOAD_BYTES)
        logger.info(
            "Recording file read user_id=%s presentation_id=%s size=%d bytes",
            current_user.id,
            presentation_id,
            len(content),
        )
        validated = validate_video_upload(
            filename=video_file.filename,
            content_type=video_file.content_type,
            content=content,
        )
    except VideoValidationError as exc:
        logger.warning(
            "Recording validation failed for user_id=%s presentation_id=%s: %s",
            current_user.id,
            presentation_id,
            exc.message,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        ) from exc

    storage_path = recording_service.upload_video(
        user_id=current_user.id,
        presentation_id=presentation_id,
        filename=validated.sanitized_filename,
        content=content,
        mime_type=validated.mime_type,
    )
    if not storage_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Could not save your video. Verify the Supabase 'recordings' bucket exists, "
                "is private, and that your service role key has storage access."
            ),
        )

    audio_path = audio_service.extract_audio_to_wav(content, validated.extension)
    if not audio_path:
        recording_service.delete_storage_file(storage_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract audio from the video. Re-record in MP4 or WebM format.",
        )

    try:
        transcription = transcription_service.transcribe_audio(audio_path)
    finally:
        audio_service.cleanup_temp_dir(audio_path)

    if not transcription:
        recording_service.delete_storage_file(storage_path)
        logger.error(
            "Transcription failed recording will be rolled back presentation_id=%s",
            presentation_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Transcription failed. Speak clearly, reduce background noise, and try again."
            ),
        )

    logger.info(
        "Transcription complete presentation_id=%s chars=%d",
        presentation_id,
        len(transcription),
    )

    encrypted = encrypt_text(transcription)
    record = recording_service.create_recording_record(
        presentation_id=presentation_id,
        storage_path=storage_path,
        duration_seconds=duration_seconds,
        transcription_encrypted=encrypted,
    )
    if not record:
        recording_service.delete_storage_file(storage_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload failed",
        )

    signed_url = recording_service.create_signed_url(storage_path)
    if not signed_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload failed",
        )

    logger.info(
        "Recording upload complete id=%s presentation_id=%s user_id=%s storage_path=%s",
        record["id"],
        presentation_id,
        current_user.id,
        storage_path,
    )

    return RecordingUploadResponse(
        id=str(record["id"]),
        video_url=signed_url,
        transcription=transcription,
        created_at=record["created_at"],
    )


@router.get("/{recording_id}", response_model=RecordingDetailResponse)
@limiter.limit("60/minute")
async def get_recording(
    request: Request,
    recording_id: str,
    current_user: CurrentUser,
) -> RecordingDetailResponse:
    """Return recording details with a signed video URL for the owner."""
    record = _require_owned_recording(recording_id, current_user.id)

    signed_url = recording_service.create_signed_url(record["storage_path"])
    if not signed_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload failed",
        )

    transcription = decrypt_text(record["transcription_encrypted"])
    if transcription is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    return RecordingDetailResponse(
        id=str(record["id"]),
        presentation_id=str(record["presentation_id"]),
        video_url=signed_url,
        transcription=transcription,
        duration_seconds=record["duration_seconds"],
        created_at=record["created_at"],
    )


@router.delete("/{recording_id}", response_model=DeleteRecordingResponse)
@limiter.limit("30/minute")
async def delete_recording(
    request: Request,
    recording_id: str,
    current_user: CurrentUser,
) -> DeleteRecordingResponse:
    """Delete a recording, its storage file, and related feedback."""
    record = _require_owned_recording(recording_id, current_user.id)
    storage_path = record["storage_path"]

    if not recording_service.delete_recording_record(recording_id):
        logger.error("Database delete failed for recording id=%s", recording_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delete failed",
        )

    if not recording_service.delete_storage_file(storage_path):
        logger.warning("Storage file not removed for recording id=%s", recording_id)

    logger.info("Recording deleted id=%s user_id=%s", recording_id, current_user.id)
    return DeleteRecordingResponse(message="Deleted")

"""Presentation upload and management routes."""

import logging

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status

from app.api.deps import CurrentUser
from app.core.limiter import limiter
from app.models import (
    DeletePresentationResponse,
    PresentationDetailResponse,
    PresentationSummaryResponse,
    PresentationUploadResponse,
)
from app.services import presentation_service
from app.utils.file_validation import PresentationType, validate_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/presentations", tags=["presentations"])


def _require_owned_presentation(presentation_id: str, user_id: str) -> dict:
    """Load a presentation and verify the authenticated user owns it."""
    presentation = presentation_service.get_presentation_by_id(presentation_id)
    if not presentation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Presentation not found",
        )
    if str(presentation["user_id"]) != user_id:
        logger.warning(
            "Forbidden access to presentation id=%s by user_id=%s",
            presentation_id,
            user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )
    return presentation


def _to_upload_response(record: dict, signed_url: str) -> PresentationUploadResponse:
    """Map a database record to an upload response."""
    return PresentationUploadResponse(
        id=str(record["id"]),
        title=record["title"],
        url=signed_url,
        created_at=record["created_at"],
    )


def _to_summary(record: dict, signed_url: str) -> PresentationSummaryResponse:
    """Map a database record to a list summary."""
    return PresentationSummaryResponse(
        id=str(record["id"]),
        title=record["title"],
        created_at=record["created_at"],
        file_url=signed_url,
    )


def _to_detail(record: dict, signed_url: str | None) -> PresentationDetailResponse:
    """Map a database record to a detail response."""
    return PresentationDetailResponse(
        id=str(record["id"]),
        title=record["title"],
        presentation_type=record["presentation_type"],
        url=signed_url,
        created_at=record["created_at"],
        challenge_metadata=record.get("challenge_metadata"),
    )


@router.post(
    "/upload",
    response_model=PresentationUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("2/minute")
async def upload_presentation(
    request: Request,
    current_user: CurrentUser,
    presentation_type: PresentationType = Form(...),
    file: UploadFile = File(...),
) -> PresentationUploadResponse:
    """
    Upload a PDF or PowerPoint presentation for the authenticated user.

    Validates file type, MIME type, and size before storing in Supabase Storage
    and creating a database record. Returns a signed URL valid for one hour.
    """
    try:
        content = await file.read()
        validated = validate_upload(
            filename=file.filename,
            content_type=file.content_type,
            content=content,
        )
    except ValueError as exc:
        logger.warning(
            "Upload validation failed for user_id=%s filename=%r",
            current_user.id,
            file.filename,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload failed",
        ) from exc

    title = presentation_service.build_title(validated.sanitized_filename)
    storage_path = presentation_service.upload_file(
        user_id=current_user.id,
        filename=validated.sanitized_filename,
        content=content,
        mime_type=validated.mime_type,
    )
    if not storage_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload failed",
        )

    record = presentation_service.create_presentation_record(
        user_id=current_user.id,
        title=title,
        presentation_type=presentation_type.value,
        storage_path=storage_path,
    )
    if not record:
        presentation_service.delete_storage_file(storage_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload failed",
        )

    signed_url = presentation_service.create_signed_url(storage_path)
    if not signed_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload failed",
        )

    logger.info(
        "Presentation uploaded id=%s user_id=%s type=%s",
        record["id"],
        current_user.id,
        presentation_type.value,
    )
    return _to_upload_response(record, signed_url)


@router.get("", response_model=list[PresentationSummaryResponse])
@limiter.limit("60/minute")
async def list_presentations(
    request: Request,
    current_user: CurrentUser,
) -> list[PresentationSummaryResponse]:
    """Return all presentations belonging to the authenticated user."""
    records = presentation_service.list_presentations_by_user(current_user.id)
    summaries: list[PresentationSummaryResponse] = []

    for record in records:
        signed_url = presentation_service.create_signed_url(record["storage_path"])
        if not signed_url:
            logger.error(
                "Could not sign URL for presentation id=%s",
                record["id"],
            )
            continue
        summaries.append(_to_summary(record, signed_url))

    return summaries


@router.get("/{presentation_id}", response_model=PresentationDetailResponse)
@limiter.limit("60/minute")
async def get_presentation(
    request: Request,
    presentation_id: str,
    current_user: CurrentUser,
) -> PresentationDetailResponse:
    """Return details for a single presentation owned by the current user."""
    record = _require_owned_presentation(presentation_id, current_user.id)

    storage_path = record.get("storage_path")
    signed_url = None
    if storage_path:
        signed_url = presentation_service.create_signed_url(storage_path)
        if not signed_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Upload failed",
            )

    return _to_detail(record, signed_url)


@router.delete("/{presentation_id}", response_model=DeletePresentationResponse)
@limiter.limit("30/minute")
async def delete_presentation(
    request: Request,
    presentation_id: str,
    current_user: CurrentUser,
) -> DeletePresentationResponse:
    """
    Delete a presentation, its storage file, and related recordings/feedback.

    Only the owning user may delete a presentation.
    """
    record = _require_owned_presentation(presentation_id, current_user.id)
    storage_path = record.get("storage_path")

    if not presentation_service.delete_presentation_record(presentation_id):
        logger.error(
            "Database delete failed for presentation id=%s",
            presentation_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delete failed",
        )

    if storage_path and not presentation_service.delete_storage_file(storage_path):
        logger.warning(
            "Storage file not removed for presentation id=%s path=%s",
            presentation_id,
            storage_path,
        )

    logger.info(
        "Presentation deleted id=%s user_id=%s",
        presentation_id,
        current_user.id,
    )
    return DeletePresentationResponse(message="Deleted")

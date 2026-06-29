"""Video upload validation utilities."""

from dataclasses import dataclass

from app.utils.file_validation import MAX_UPLOAD_BYTES, sanitize_filename

ALLOWED_VIDEO_EXTENSIONS = frozenset({".mp4", ".webm"})

ALLOWED_VIDEO_MIME_TYPES = frozenset({
    "video/mp4",
    "video/webm",
})

MAX_UPLOAD_MB = MAX_UPLOAD_BYTES // (1024 * 1024)

_VIDEO_MAGIC: dict[str, tuple[bytes, ...]] = {
    ".mp4": (b"\x00\x00\x00", b"ftyp"),
    ".webm": (b"\x1a\x45\xdf\xa3",),
}


class VideoValidationError(ValueError):
    """Raised when a video upload fails validation with a client-safe message."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class ValidatedVideoUpload:
    """Result of a successful video file validation."""

    extension: str
    mime_type: str
    original_filename: str
    sanitized_filename: str


def _extension(filename: str) -> str:
    dot = filename.rfind(".")
    if dot == -1:
        return ""
    return filename[dot:].lower()


def _is_mp4(content: bytes) -> bool:
    """Detect MP4/MOV by scanning for an ftyp box in the first 32 bytes."""
    return len(content) >= 8 and content[4:8] == b"ftyp"


def _matches_video_magic(content: bytes, extension: str) -> bool:
    if extension == ".webm":
        return content.startswith(_VIDEO_MAGIC[".webm"])
    if extension == ".mp4":
        return _is_mp4(content)
    return False


def validate_video_upload(
    *,
    filename: str | None,
    content_type: str | None,
    content: bytes,
) -> ValidatedVideoUpload:
    """
    Validate a video upload's extension, MIME type, size, and magic bytes.

    Raises VideoValidationError with a helpful message for the client.
    """
    if not filename:
        raise VideoValidationError("A video file is required.")

    if len(content) == 0:
        raise VideoValidationError("The uploaded video file is empty.")

    if len(content) > MAX_UPLOAD_BYTES:
        raise VideoValidationError(
            f"Video exceeds the {MAX_UPLOAD_MB} MB size limit. "
            "Try recording a shorter clip or compress the file."
        )

    extension = _extension(filename)
    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        raise VideoValidationError(
            "Only MP4 and WebM videos are supported. "
            "Please export or re-record in one of those formats."
        )

    mime_type = (content_type or "application/octet-stream").split(";")[0].strip().lower()
    if mime_type not in ALLOWED_VIDEO_MIME_TYPES:
        raise VideoValidationError(
            f"Invalid video type '{mime_type}'. "
            "Only video/mp4 and video/webm are accepted."
        )

    if not _matches_video_magic(content, extension):
        raise VideoValidationError(
            "The file does not appear to be a valid MP4 or WebM video. "
            "Please re-record or convert the file."
        )

    sanitized = sanitize_filename(filename)
    if _extension(sanitized) not in ALLOWED_VIDEO_EXTENSIONS:
        sanitized = f"{sanitized}{extension}"

    return ValidatedVideoUpload(
        extension=extension,
        mime_type=mime_type,
        original_filename=filename,
        sanitized_filename=sanitized,
    )


def build_recording_storage_path(
    user_id: str,
    presentation_id: str,
    sanitized_filename: str,
    timestamp: int,
) -> str:
    """Build a unique storage path: user_id/presentation_id/timestamp_filename."""
    return f"{user_id}/{presentation_id}/{timestamp}_{sanitized_filename}"


def build_challenge_storage_path(
    user_id: str,
    challenge_id: str,
    sanitized_filename: str,
    timestamp: int,
) -> str:
    """Build a unique storage path for challenge recordings."""
    return f"{user_id}/challenges/{challenge_id}/{timestamp}_{sanitized_filename}"

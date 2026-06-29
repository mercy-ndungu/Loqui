"""File upload validation utilities."""

import re
from dataclasses import dataclass
from enum import Enum

MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # 500 MB

ALLOWED_EXTENSIONS = frozenset({".pdf", ".ppt", ".pptx"})

ALLOWED_MIME_TYPES = frozenset({
    "application/pdf",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
})

# Magic-byte signatures for supported formats
_MAGIC_SIGNATURES: dict[str, tuple[bytes, ...]] = {
    ".pdf": (b"%PDF",),
    ".ppt": (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",),  # OLE compound document
    ".pptx": (b"PK\x03\x04",),  # Office Open XML (ZIP)
}


class PresentationType(str, Enum):
    """Supported presentation categories."""

    PITCH = "pitch"
    INTERVIEW = "interview"
    NETWORKING = "networking"
    GENERAL = "general"


@dataclass(frozen=True)
class ValidatedUpload:
    """Result of a successful file validation."""

    extension: str
    mime_type: str
    original_filename: str
    sanitized_filename: str


def sanitize_filename(filename: str) -> str:
    """Strip path components and unsafe characters from a filename."""
    basename = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    sanitized = re.sub(r"[^\w.\-]", "_", basename.strip())
    return sanitized or "upload"


def _extension(filename: str) -> str:
    """Return the lowercase file extension including the dot."""
    dot = filename.rfind(".")
    if dot == -1:
        return ""
    return filename[dot:].lower()


def _matches_magic(content: bytes, extension: str) -> bool:
    """Verify file content matches expected magic bytes for the extension."""
    signatures = _MAGIC_SIGNATURES.get(extension, ())
    return any(content.startswith(sig) for sig in signatures)


def validate_upload(
    *,
    filename: str | None,
    content_type: str | None,
    content: bytes,
) -> ValidatedUpload:
    """
    Validate an uploaded file's extension, MIME type, size, and magic bytes.

    Raises ValueError with a generic message suitable for client responses.
    """
    if not filename:
        raise ValueError("Upload failed")

    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("Upload failed")

    if len(content) == 0:
        raise ValueError("Upload failed")

    extension = _extension(filename)
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Upload failed")

    mime_type = (content_type or "application/octet-stream").split(";")[0].strip().lower()
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError("Upload failed")

    if not _matches_magic(content, extension):
        raise ValueError("Upload failed")

    sanitized = sanitize_filename(filename)
    if _extension(sanitized) not in ALLOWED_EXTENSIONS:
        sanitized = f"{sanitized}{extension}"

    return ValidatedUpload(
        extension=extension,
        mime_type=mime_type,
        original_filename=filename,
        sanitized_filename=sanitized,
    )


def build_storage_path(user_id: str, sanitized_filename: str, timestamp: int) -> str:
    """Build a unique storage object path under the user's folder."""
    return f"{user_id}/{timestamp}_{sanitized_filename}"


def title_from_filename(filename: str) -> str:
    """Derive a human-readable title from a filename."""
    name = sanitize_filename(filename)
    dot = name.rfind(".")
    if dot > 0:
        name = name[:dot]
    return name.replace("_", " ").strip() or "Untitled"

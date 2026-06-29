"""Stream large uploads with a hard size cap."""

from fastapi import UploadFile

CHUNK_SIZE = 1024 * 1024  # 1 MB


async def read_upload_with_limit(file: UploadFile, max_bytes: int) -> bytes:
    """
    Read an upload in chunks, enforcing a maximum total size.

    Raises ValueError with a generic message when the limit is exceeded.
    """
    chunks: list[bytes] = []
    total = 0

    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise ValueError("Upload failed")
        chunks.append(chunk)

    content = b"".join(chunks)
    if not content:
        raise ValueError("Upload failed")
    return content

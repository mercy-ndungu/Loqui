"""Encrypt and decrypt sensitive text at rest."""

import logging
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def _fernet() -> Fernet:
    """Return a cached Fernet instance using the configured encryption key."""
    return Fernet(get_settings().transcription_encryption_key.encode())


def encrypt_text(plaintext: str) -> str:
    """Encrypt plaintext and return a URL-safe base64 ciphertext string."""
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_text(ciphertext: str) -> str | None:
    """Decrypt a ciphertext string, returning None on failure."""
    try:
        return _fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError) as exc:
        logger.error("Transcription decryption failed: %s", exc)
        return None

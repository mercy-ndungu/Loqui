"""Improv challenge images via Unsplash API with a curated fallback list."""

import logging
import random
from typing import Any

import requests

from app.core.config import get_settings

logger = logging.getLogger(__name__)

UNSPLASH_RANDOM_URL = "https://api.unsplash.com/photos/random"
IMPROV_IMAGE_COUNT = 5

# Fallback when Unsplash is unavailable (22 curated images)
IMPROV_IMAGES: tuple[str, ...] = (
    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=500",
    "https://images.unsplash.com/photo-1495521821757-a1efb6729352?w=500",
    "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?w=500",
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=500",
    "https://images.unsplash.com/photo-1495954484750-af469f1357be?w=500",
    "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=500",
    "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=500",
    "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=500",
    "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=500",
    "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=500",
    "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?w=500",
    "https://images.unsplash.com/photo-1426604966848-d7ad8d697736?w=500",
    "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?w=500",
    "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=500",
    "https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=500",
    "https://images.unsplash.com/photo-1526481280693-3bfa7568e0f3?w=500",
    "https://images.unsplash.com/photo-1532274402911-5a369e4c4ddb?w=500",
    "https://images.unsplash.com/photo-1540979388789-6ceed516a388?w=500",
    "https://images.unsplash.com/photo-1551632811-561732d1e58d?w=500",
    "https://images.unsplash.com/photo-1561214115-f2f134cc4912?w=500",
    "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?w=500",
    "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=500",
)

FALLBACK_ALTS: tuple[str, ...] = (
    "Mountain landscape",
    "Ocean view",
    "City skyline",
    "Forest path",
    "Desert dunes",
    "Nature valley",
    "Foggy hills",
    "Lake and mountains",
    "Snowy peaks",
    "Ocean waves",
    "Green meadow",
    "Forest lake",
    "Woodland trail",
    "Beach sunset",
    "Urban street",
    "Camera on desk",
    "Colorful flowers",
    "Coffee shop",
    "Hot air balloons",
    "Hiking trail",
    "Workshop tools",
    "City at night",
)


def _from_stored_list(count: int = IMPROV_IMAGE_COUNT) -> list[dict[str, str]]:
    """Pick random images from the hard-coded fallback list."""
    picks = random.sample(list(IMPROV_IMAGES), k=min(count, len(IMPROV_IMAGES)))
    logger.info("Using %d stored fallback improv images", len(picks))
    return [
        {"url": url, "alt": FALLBACK_ALTS[i % len(FALLBACK_ALTS)]}
        for i, url in enumerate(picks)
    ]


def _fetch_unsplash_images(count: int = IMPROV_IMAGE_COUNT) -> list[dict[str, str]] | None:
    """
    Fetch random photos from https://api.unsplash.com/photos/random?count=5

    Unsplash requires a Client-ID for API access in production. Set UNSPLASH_ACCESS_KEY
    in the environment. Without it, the request may return 401 and fallback images are used.
    """
    params: dict[str, Any] = {"count": count}
    headers: dict[str, str] = {"Accept-Version": "v1"}
    access_key = get_settings().unsplash_access_key
    if access_key:
        headers["Authorization"] = f"Client-ID {access_key}"
    else:
        logger.warning(
            "UNSPLASH_ACCESS_KEY not set; Unsplash API may reject requests (401). "
            "Register a free key at https://unsplash.com/developers"
        )

    try:
        logger.info("Fetching %d improv images from Unsplash API", count)
        response = requests.get(
            UNSPLASH_RANDOM_URL,
            params=params,
            headers=headers,
            timeout=15,
        )
        if response.status_code == 401:
            logger.error(
                "Unsplash API returned 401 Unauthorized. Set UNSPLASH_ACCESS_KEY in .env"
            )
            return None
        response.raise_for_status()
        payload = response.json()
        items = payload if isinstance(payload, list) else [payload]
        images: list[dict[str, str]] = []
        for photo in items:
            urls = photo.get("urls") or {}
            url = urls.get("regular") or urls.get("small")
            if not url:
                continue
            alt = photo.get("alt_description") or photo.get("description") or "Image"
            images.append({"url": url, "alt": alt})
        if len(images) >= count:
            logger.info("Unsplash returned %d improv images", len(images[:count]))
            return images[:count]
        logger.warning("Unsplash returned only %d/%d images", len(images), count)
    except requests.RequestException as exc:
        logger.error("Unsplash API request failed: %s", exc)
    except Exception as exc:
        logger.error("Unexpected Unsplash error: %s", exc)
    return None


def generate_improv_images() -> list[dict[str, str]]:
    """Return 5 random improv images from Unsplash, or the stored fallback list."""
    unsplash = _fetch_unsplash_images(IMPROV_IMAGE_COUNT)
    if unsplash:
        return unsplash
    return _from_stored_list(IMPROV_IMAGE_COUNT)

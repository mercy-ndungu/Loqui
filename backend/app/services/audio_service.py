"""Extract audio from video files using ffmpeg."""

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def ffmpeg_available() -> bool:
    """Return True when ffmpeg is available on the system PATH."""
    return shutil.which("ffmpeg") is not None


def extract_audio_to_wav(video_bytes: bytes, extension: str) -> Path | None:
    """
    Write video bytes to a temp file and extract mono 16 kHz WAV audio.

    Returns the path to the WAV file (caller must delete the temp directory).
    """
    if not ffmpeg_available():
        logger.error("ffmpeg is not installed or not on PATH")
        return None

    tmp_dir = Path(tempfile.mkdtemp(prefix="loqui_audio_"))
    video_path = tmp_dir / f"input{extension}"
    audio_path = tmp_dir / "audio.wav"

    try:
        video_path.write_bytes(video_bytes)
        result = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(video_path),
                "-vn",
                "-acodec",
                "pcm_s16le",
                "-ar",
                "16000",
                "-ac",
                "1",
                str(audio_path),
                "-y",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            logger.error("ffmpeg audio extraction failed: %s", result.stderr.strip())
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return None
        if not audio_path.exists() or audio_path.stat().st_size == 0:
            logger.error("ffmpeg produced empty audio output")
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return None
        return audio_path
    except Exception as exc:
        logger.exception("Audio extraction error: %s", exc)
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return None


def cleanup_temp_dir(path: Path) -> None:
    """Remove the temporary directory containing a extracted audio file."""
    try:
        shutil.rmtree(path.parent, ignore_errors=True)
    except Exception as exc:
        logger.warning("Failed to clean temp dir: %s", exc)

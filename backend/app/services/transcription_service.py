"""Speech-to-text transcription providers."""

import logging
import os
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)


class TranscriptionProvider(ABC):
    """Abstract transcription backend."""

    @abstractmethod
    def transcribe(self, audio_path: Path) -> str | None:
        """Return transcribed text or None on failure."""


class WhisperTranscriptionProvider(TranscriptionProvider):
    """Local transcription using faster-whisper."""

    def __init__(self, model_size: str = "base") -> None:
        self._model_size = model_size
        self._model = None

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            device = os.getenv("WHISPER_DEVICE", "cpu")
            compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
            self._model = WhisperModel(self._model_size, device=device, compute_type=compute_type)
        return self._model

    def transcribe(self, audio_path: Path) -> str | None:
        try:
            model = self._get_model()
            segments, _info = model.transcribe(str(audio_path), beam_size=5)
            text = " ".join(segment.text.strip() for segment in segments).strip()
            return text or None
        except Exception as exc:
            logger.error("Whisper transcription failed: %s", exc)
            return None


class FfmpegWhisperCliProvider(TranscriptionProvider):
    """Fallback: invoke the openai-whisper CLI if installed."""

    def __init__(self, model_size: str = "base") -> None:
        self._model_size = model_size

    def transcribe(self, audio_path: Path) -> str | None:
        if not shutil.which("whisper"):
            logger.error("whisper CLI not found on PATH")
            return None
        output_dir = audio_path.parent
        try:
            result = subprocess.run(
                [
                    "whisper",
                    str(audio_path),
                    "--model",
                    self._model_size,
                    "--output_format",
                    "txt",
                    "--output_dir",
                    str(output_dir),
                    "--language",
                    "en",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                logger.error("whisper CLI failed: %s", result.stderr.strip())
                return None
            txt_path = output_dir / f"{audio_path.stem}.txt"
            if not txt_path.exists():
                return None
            return txt_path.read_text(encoding="utf-8").strip() or None
        except Exception as exc:
            logger.error("whisper CLI error: %s", exc)
            return None


def get_transcription_provider() -> TranscriptionProvider:
    """Return the configured transcription provider."""
    provider = os.getenv("TRANSCRIPTION_PROVIDER", "whisper").lower()
    model_size = os.getenv("WHISPER_MODEL", "base")

    if provider == "whisper_cli":
        return FfmpegWhisperCliProvider(model_size=model_size)
    return WhisperTranscriptionProvider(model_size=model_size)


def transcribe_audio(audio_path: Path) -> str | None:
    """Transcribe an audio file using the configured provider."""
    return get_transcription_provider().transcribe(audio_path)

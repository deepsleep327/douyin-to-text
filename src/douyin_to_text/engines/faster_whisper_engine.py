"""faster-whisper engine — CTranslate2-based Whisper inference (CPU)."""

from __future__ import annotations

import logging
import time
from typing import Any

from .base import ASREngine, Segment, TranscriptResult

logger = logging.getLogger("douyin_to_text.engines")

VALID_MODEL_SIZES: tuple[str, ...] = (
    "tiny",
    "base",
    "small",
    "medium",
    "large-v3-turbo",
)

DEFAULT_MODEL_SIZE = "base"


class FasterWhisperEngine(ASREngine):
    """Whisper ASR via the ``faster-whisper`` library (CPU, int8)."""

    def __init__(self, model_size: str = DEFAULT_MODEL_SIZE) -> None:
        if model_size not in VALID_MODEL_SIZES:
            raise ValueError(
                f"Invalid model size {model_size!r}. "
                f"Choose from {VALID_MODEL_SIZES}"
            )
        self._model_size = model_size
        self._model: Any | None = None

    # -- ASREngine interface ---------------------------------------------------

    @property
    def name(self) -> str:  # noqa: D401
        return "faster-whisper"

    @property
    def priority(self) -> int:  # noqa: D401
        return 50

    def is_available(self) -> bool:
        """Check that ``faster_whisper`` is importable."""
        try:
            import faster_whisper  # noqa: F401

            return True
        except ImportError:
            return False

    def transcribe(
        self, audio_path: str, language: str = "auto"
    ) -> TranscriptResult:
        """Run faster-whisper on *audio_path* and return the transcript."""
        if not self.is_available():
            raise RuntimeError(
                "faster-whisper engine requires 'faster-whisper'. "
                "Install with: pip install faster-whisper"
            )

        model = self._get_model()
        lang: str | None = None if language == "auto" else language

        logger.info(
            "Transcribing %s with faster-whisper/%s (lang=%s)",
            audio_path,
            self._model_size,
            lang or "auto",
        )
        t0 = time.monotonic()

        raw_segments, info = model.transcribe(
            audio_path,
            language=lang,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=400,
            ),
        )

        segments: list[Segment] = []
        full_texts: list[str] = []

        for seg in raw_segments:
            text = seg.text.strip()
            if text:
                segments.append(
                    Segment(start=seg.start, end=seg.end, text=text)
                )
                full_texts.append(text)

        elapsed = time.monotonic() - t0
        detected_lang = info.language if info.language else "zh"
        full_text = " ".join(full_texts).strip()

        logger.info(
            "faster-whisper done in %.2fs — %d chars, detected=%s",
            elapsed,
            len(full_text),
            detected_lang,
        )

        return TranscriptResult(
            text=full_text,
            segments=segments,
            language=detected_lang,
            engine_name=self.name,
            model_name=f"faster-whisper/{self._model_size}",
            audio_duration=info.duration,
            processing_time=elapsed,
        )

    # -- internal --------------------------------------------------------------

    def _get_model(self) -> Any:
        """Lazy-load the faster-whisper model."""
        if self._model is not None:
            return self._model

        from faster_whisper import WhisperModel  # type: ignore[import-untyped]

        logger.info(
            "Loading faster-whisper model '%s' (CPU, int8) …",
            self._model_size,
        )
        self._model = WhisperModel(
            self._model_size,
            device="cpu",
            compute_type="int8",
        )
        return self._model

"""SenseVoice engine — FunASR + SenseVoiceSmall (ONNX, CPU)."""

from __future__ import annotations

import logging
import time
from typing import Any

from .base import ASREngine, Segment, TranscriptResult

logger = logging.getLogger("douyin_to_text.engines")

_LANG_MAP: dict[str, str] = {
    "auto": "auto",
    "zh": "zh",
    "en": "en",
    "ja": "ja",
    "ko": "ko",
    "yue": "yue",
}

import os
MODEL_ID = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "models", "SenseVoiceSmall")


class SenseVoiceEngine(ASREngine):
    """FunASR SenseVoiceSmall with ONNX Runtime inference."""

    def __init__(self) -> None:
        self._model: Any | None = None

    # -- ASREngine interface ---------------------------------------------------

    @property
    def name(self) -> str:  # noqa: D401
        return "sensevoice"

    @property
    def priority(self) -> int:  # noqa: D401
        return 50

    def is_available(self) -> bool:
        """Check that ``funasr`` and ``onnxruntime`` are importable."""
        try:
            import funasr  # noqa: F401
            import onnxruntime  # noqa: F401

            return True
        except ImportError:
            return False

    def transcribe(
        self, audio_path: str, language: str = "auto"
    ) -> TranscriptResult:
        """Run SenseVoiceSmall on *audio_path* and return the transcript."""
        if not self.is_available():
            raise RuntimeError(
                "SenseVoice engine requires 'funasr' and 'onnxruntime'. "
                "Install with: pip install funasr onnxruntime"
            )

        model = self._get_model()
        lang = _LANG_MAP.get(language, "auto")

        logger.info(
            "Transcribing %s with SenseVoice (lang=%s, chunked)", audio_path, lang
        )
        t0 = time.monotonic()

        try:
            from pydub import AudioSegment
            import tempfile
            audio = AudioSegment.from_file(audio_path)
            chunk_length_ms = 30000  # 30 seconds
            chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
        except Exception as e:
            logger.warning("Could not chunk audio with pydub (%s), falling back to full audio.", e)
            chunks = [None]

        segments: list[Segment] = []
        full_texts: list[str] = []

        for i, chunk in enumerate(chunks):
            if chunk is not None:
                tmp_fd, tmp_path = tempfile.mkstemp(suffix=".wav")
                os.close(tmp_fd)
                chunk.export(tmp_path, format="wav")
                input_path = tmp_path
            else:
                input_path = audio_path
                tmp_path = None

            try:
                results = model.generate(
                    input=input_path,
                    cache={},
                    language=lang,
                    use_itn=True,
                    batch_size_s=60,
                )
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)

            time_offset = i * (30000 / 1000.0) if chunk is not None else 0.0

            for item in results:
                text: str = item.get("text", "")
                full_texts.append(text)

                if "timestamp" in item:
                    for ts_pair, seg_text in zip(
                        item["timestamp"], item.get("text_seg", [text])
                    ):
                        segments.append(
                            Segment(
                                start=(ts_pair[0] / 1000.0) + time_offset,
                                end=(ts_pair[1] / 1000.0) + time_offset,
                                text=seg_text.strip(),
                            )
                        )

        elapsed = time.monotonic() - t0
        full_text = " ".join(full_texts).strip()

        logger.info(
            "SenseVoice done in %.2fs — %d chars", elapsed, len(full_text)
        )

        return TranscriptResult(
            text=full_text,
            segments=segments,
            language=detected_lang,
            engine_name=self.name,
            model_name=MODEL_ID,
            processing_time=elapsed,
        )

    # -- internal --------------------------------------------------------------

    def _get_model(self) -> Any:
        """Lazy-load the SenseVoiceSmall model (downloads on first call)."""
        if self._model is not None:
            return self._model

        from funasr import AutoModel  # type: ignore[import-untyped]

        logger.info(
            "Loading SenseVoice model %s (will download on first run) …",
            MODEL_ID,
        )
        self._model = AutoModel(
            model=MODEL_ID,
            trust_remote_code=True,
            device="cpu",
        )
        return self._model

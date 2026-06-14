"""ASR engine registry with auto-detection.

Usage::

    from douyin_to_text.engines import get_engine

    engine = get_engine()          # auto-select best available
    result = engine.transcribe("audio.wav")
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .base import ASREngine, Segment, TranscriptResult

if TYPE_CHECKING:
    pass

logger = logging.getLogger("douyin_to_text.engines")

__all__ = [
    "ASREngine",
    "Segment",
    "TranscriptResult",
    "get_available_engines",
    "get_engine",
]


def _build_all_engines(model_size: str = "small") -> list[ASREngine]:
    """Instantiate every known engine (whether or not it is available)."""
    from .faster_whisper_engine import FasterWhisperEngine
    from .sensevoice import SenseVoiceEngine

    return [
        SenseVoiceEngine(),
        FasterWhisperEngine(model_size=model_size),
    ]


def get_available_engines(
    model_size: str = "small",
) -> list[ASREngine]:
    """Return engines whose runtime dependencies are importable.

    The list is sorted by :pyattr:`ASREngine.priority` (descending).
    """
    available = [
        e for e in _build_all_engines(model_size) if e.is_available()
    ]
    available.sort(key=lambda e: e.priority, reverse=True)
    if not available:
        logger.warning(
            "No ASR engines available. Install 'funasr onnxruntime' "
            "or 'faster-whisper'."
        )
    return available


def get_engine(
    name: str = "auto",
    model_size: str = "small",
) -> ASREngine:
    """Select an ASR engine by *name*, or auto-pick the best one.

    Parameters
    ----------
    name:
        ``'auto'`` (default) selects the highest-priority available engine.
        Other accepted values: ``'sensevoice'``, ``'faster-whisper'``.
    model_size:
        Model size hint passed to engines that support it
        (e.g. faster-whisper: ``'tiny'``, ``'base'``, ``'small'``, …).

    Raises
    ------
    RuntimeError
        If no matching engine is available.
    """
    if name == "auto":
        engines = get_available_engines(model_size)
        if not engines:
            raise RuntimeError(
                "No ASR engine is available. "
                "Install one of: "
                "pip install funasr onnxruntime  |  "
                "pip install faster-whisper"
            )
        chosen = engines[0]
        logger.info(
            "Auto-selected engine '%s' (priority=%d)",
            chosen.name,
            chosen.priority,
        )
        return chosen

    # Explicit engine selection ------------------------------------------------
    all_engines = _build_all_engines(model_size)
    for engine in all_engines:
        if engine.name == name:
            if not engine.is_available():
                raise RuntimeError(
                    f"Engine '{name}' is not available — "
                    f"its dependencies are not installed."
                )
            logger.info("Using explicitly requested engine '%s'", name)
            return engine

    known = [e.name for e in all_engines]
    raise RuntimeError(
        f"Unknown engine '{name}'. Known engines: {known}"
    )

"""High-level ASR orchestrator for douyin-to-text.

Coordinates the full pipeline:

1. Resolve the Douyin URL.
2. Download audio.
3. Select and run the ASR engine.
4. Format and return the output.
"""

from __future__ import annotations

import logging
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional

from .downloader import DownloadError, DownloadResult, download_audio
from .engines.base import ASREngine, TranscriptResult
from .output import OutputFormat, format_output
from .resolver import Platform, URLResolveError, resolve_url
from .utils import ensure_ffmpeg, get_audio_duration

logger = logging.getLogger("douyin_to_text")


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class TranscribeError(Exception):
    """Raised when the full transcription pipeline fails."""


# ---------------------------------------------------------------------------
# Engine registry helper
# ---------------------------------------------------------------------------


def _get_engine(engine_name: str, model_size: str) -> ASREngine:
    """Instantiate the requested ASR engine.

    If *engine_name* is ``"auto"``, the function tries available engines
    in priority order.

    Raises
    ------
    TranscribeError
        If no engine is available.
    """
    # Import engine implementations lazily to avoid hard deps at module level.
    engines: list[ASREngine] = []

    if engine_name in ("auto", "sensevoice"):
        try:
            from .engines.sensevoice import SenseVoiceEngine  # type: ignore[import-not-found]

            eng = SenseVoiceEngine()
            if eng.is_available():
                engines.append(eng)
        except ImportError:
            logger.debug("SenseVoice engine not importable")

    if engine_name in ("auto", "faster-whisper"):
        try:
            from .engines.faster_whisper import FasterWhisperEngine  # type: ignore[import-not-found]

            eng = FasterWhisperEngine(model_size=model_size)
            if eng.is_available():
                engines.append(eng)
        except ImportError:
            logger.debug("faster-whisper engine not importable")

    if not engines:
        raise TranscribeError(
            f"No ASR engine available (requested: {engine_name!r}). "
            "Install at least one backend – see README for details."
        )

    # Sort by priority (higher is preferred) and pick the best.
    engines.sort(key=lambda e: e.priority, reverse=True)
    selected = engines[0]
    logger.info("Selected ASR engine: %s (priority %d)", selected.name, selected.priority)
    return selected


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def transcribe_url(
    url: str,
    *,
    engine: str = "auto",
    language: str = "auto",
    model_size: str = "large-v3",
    fmt: str = "json",
    keep_audio: bool = False,
    temp_dir: Optional[str] = None,
    cookies_from_browser: Optional[str] = None,
) -> str:
    """Run the full transcription pipeline on a Douyin video URL.

    Parameters
    ----------
    url:
        Douyin URL (short or full).
    engine:
        ASR engine name (``"auto"``, ``"sensevoice"``, ``"faster-whisper"``).
    language:
        Language hint (``"auto"``, ``"zh"``, ``"en"``, etc.).
    model_size:
        Model size for Whisper-family engines (e.g. ``"large-v3"``).
    fmt:
        Output format (``"json"``, ``"markdown"``, ``"text"``).
    keep_audio:
        If ``True``, do not delete the downloaded WAV after transcription.
    temp_dir:
        Directory to store temporary audio files.  A new temp directory
        is created when ``None``.
    cookies_from_browser:
        Browser name for cookie extraction (e.g. ``"chrome"``).

    Returns
    -------
    str
        Formatted transcription output.

    Raises
    ------
    TranscribeError
        On any pipeline failure (wraps underlying exceptions).
    """
    if not ensure_ffmpeg():
        raise TranscribeError(
            "ffmpeg/ffprobe is required but not found on PATH. "
            "Install ffmpeg first."
        )

    work_dir = temp_dir or tempfile.mkdtemp(prefix="douyin_to_text_")
    download_result: Optional[DownloadResult] = None

    try:
        # 1. Resolve URL --------------------------------------------------------
        logger.info("Step 1/4: Resolving URL …")
        try:
            resolved = resolve_url(url)
        except (URLResolveError, ValueError) as exc:
            raise TranscribeError(f"URL resolution failed: {exc}") from exc

        if resolved.platform != Platform.DOUYIN:
            raise TranscribeError(
                f"Platform {resolved.platform.value!r} is not yet supported."
            )

        target_url = resolved.resolved_url
        video_id = resolved.video_id or ""

        # 2. Download audio -----------------------------------------------------
        logger.info("Step 2/4: Downloading audio …")
        try:
            download_result = download_audio(
                target_url,
                video_id=video_id,
                temp_dir=work_dir,
                cookies_from_browser=cookies_from_browser,
            )
        except DownloadError as exc:
            raise TranscribeError(f"Audio download failed: {exc}") from exc

        audio_path = str(download_result.audio_path)
        audio_duration = get_audio_duration(audio_path) or download_result.duration

        # 3. Transcribe ----------------------------------------------------------
        logger.info("Step 3/4: Transcribing audio …")
        asr_engine = _get_engine(engine, model_size)
        t0 = time.monotonic()
        try:
            result: TranscriptResult = asr_engine.transcribe(audio_path, language=language)
        except Exception as exc:
            raise TranscribeError(f"Transcription failed ({asr_engine.name}): {exc}") from exc
        elapsed = time.monotonic() - t0

        # Populate timing metadata
        result.audio_duration = audio_duration
        result.processing_time = round(elapsed, 2)

        logger.info(
            "Transcription complete: %.1fs audio in %.1fs (%.1f× realtime)",
            audio_duration,
            elapsed,
            audio_duration / elapsed if elapsed > 0 else 0,
        )

        # 4. Format output -------------------------------------------------------
        logger.info("Step 4/4: Formatting output …")
        return format_output(
            result,
            download_info=download_result,
            fmt=fmt,
            url=url,
        )

    finally:
        # Cleanup
        if not keep_audio and download_result is not None:
            audio_file = download_result.audio_path
            if audio_file.exists():
                audio_file.unlink()
                logger.debug("Cleaned up audio file: %s", audio_file)
        if not keep_audio and temp_dir is None:
            # We created the temp dir ourselves – try to remove it.
            work_path = Path(work_dir)
            if work_path.exists():
                shutil.rmtree(work_path, ignore_errors=True)
                logger.debug("Cleaned up temp directory: %s", work_path)

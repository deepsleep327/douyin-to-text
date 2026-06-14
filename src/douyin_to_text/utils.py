"""Shared utility functions for douyin-to-text."""

from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("douyin_to_text")


# ---------------------------------------------------------------------------
# Audio helpers
# ---------------------------------------------------------------------------


def get_audio_duration(path: str | Path) -> float:
    """Return the duration of an audio file in seconds using ``ffprobe``.

    Parameters
    ----------
    path:
        Path to the audio file.

    Returns
    -------
    float
        Duration in seconds.  Returns ``0.0`` if ffprobe is unavailable or
        the file cannot be probed.
    """
    path = Path(path)
    if not path.exists():
        logger.warning("Audio file does not exist: %s", path)
        return 0.0

    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        logger.warning("ffprobe not found; cannot determine audio duration")
        return 0.0

    cmd = [
        ffprobe,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        str(path),
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode != 0:
            logger.warning("ffprobe returned %d for %s", proc.returncode, path)
            return 0.0
        info = json.loads(proc.stdout)
        return float(info.get("format", {}).get("duration", 0))
    except (subprocess.TimeoutExpired, json.JSONDecodeError, ValueError) as exc:
        logger.warning("Failed to get audio duration: %s", exc)
        return 0.0


# ---------------------------------------------------------------------------
# Environment checks
# ---------------------------------------------------------------------------


def ensure_ffmpeg() -> bool:
    """Return ``True`` if both ``ffmpeg`` and ``ffprobe`` are on ``$PATH``."""
    ffmpeg_ok = shutil.which("ffmpeg") is not None
    ffprobe_ok = shutil.which("ffprobe") is not None
    if not ffmpeg_ok:
        logger.error("ffmpeg is not installed or not on PATH")
    if not ffprobe_ok:
        logger.error("ffprobe is not installed or not on PATH")
    return ffmpeg_ok and ffprobe_ok


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def setup_logging(verbose: bool = False) -> None:
    """Configure the ``douyin_to_text`` logger to write to *stderr*.

    Parameters
    ----------
    verbose:
        If ``True``, set level to ``DEBUG``; otherwise ``WARNING``.
    """
    level = logging.DEBUG if verbose else logging.WARNING
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    pkg_logger = logging.getLogger("douyin_to_text")
    pkg_logger.setLevel(level)
    # Avoid duplicate handlers on repeated calls
    if not pkg_logger.handlers:
        pkg_logger.addHandler(handler)


# ---------------------------------------------------------------------------
# Filename sanitisation
# ---------------------------------------------------------------------------

_UNSAFE_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_MAX_FILENAME_LEN = 200


def sanitize_filename(name: str) -> str:
    """Clean *name* so it is safe for use as a filename.

    * Strips leading/trailing whitespace.
    * Replaces characters forbidden on Windows/macOS/Linux.
    * Collapses multiple underscores.
    * Truncates to :data:`_MAX_FILENAME_LEN` characters.
    * Returns ``"untitled"`` when the result would be empty.
    """
    name = name.strip()
    name = _UNSAFE_RE.sub("_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    if not name:
        return "untitled"
    return name[:_MAX_FILENAME_LEN]

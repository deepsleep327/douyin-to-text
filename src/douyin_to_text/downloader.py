"""Download audio from Douyin videos using ``yt-dlp``.

Extracts audio-only in 16 kHz mono WAV format (optimal for ASR), along with
video metadata such as title, author, duration, and description.
"""

from __future__ import annotations

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger("douyin_to_text")


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class DownloadResult:
    """Metadata and file path returned after a successful download."""

    audio_path: Path
    title: str
    author: str
    duration: float
    description: str
    video_id: str


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class DownloadError(Exception):
    """Raised when audio download fails."""


# ---------------------------------------------------------------------------
# Progress hook
# ---------------------------------------------------------------------------


def _progress_hook(d: dict) -> None:  # type: ignore[type-arg]
    """Log download progress to stderr via the logger."""
    status = d.get("status")
    if status == "downloading":
        pct = d.get("_percent_str", "?%").strip()
        speed = d.get("_speed_str", "?").strip()
        logger.debug("Downloading: %s at %s", pct, speed)
    elif status == "finished":
        logger.info("Download finished, processing audio …")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def download_audio(
    url: str,
    *,
    video_id: str = "",
    temp_dir: Optional[str] = None,
    cookies_from_browser: Optional[str] = None,
) -> DownloadResult:
    """Download audio from *url* and return a :class:`DownloadResult`.

    Parameters
    ----------
    url:
        Full Douyin video URL (already resolved).
    video_id:
        Pre-extracted video ID.  Used for the output filename; if empty the
        filename is based on the yt-dlp default template.
    temp_dir:
        Directory for the output WAV file.  Defaults to a new temporary
        directory.
    cookies_from_browser:
        Browser name (e.g. ``"chrome"``, ``"firefox"``) from which to
        extract cookies for anti-scraping authentication.

    Returns
    -------
    DownloadResult

    Raises
    ------
    DownloadError
        On network errors, geo-restriction, deleted videos, or any yt-dlp
        failure.
    """
    try:
        import yt_dlp  # type: ignore[import-untyped]
    except ImportError as exc:
        raise DownloadError(
            "yt-dlp is not installed. Install it with: pip install yt-dlp"
        ) from exc

    if temp_dir is None:
        temp_dir = tempfile.mkdtemp(prefix="douyin_to_text_")
    outdir = Path(temp_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    stem = video_id or "%(id)s"
    outtmpl = str(outdir / f"{stem}.%(ext)s")

    ydl_opts: dict = {
        # Audio extraction
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            },
        ],
        "postprocessor_args": [
            "-ar", "16000",   # 16 kHz sample rate
            "-ac", "1",       # mono
        ],
        "outtmpl": outtmpl,
        # Behaviour
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "progress_hooks": [_progress_hook],
        # Network
        "socket_timeout": 30,
        "retries": 3,
    }

    if cookies_from_browser:
        ydl_opts["cookiesfrombrowser"] = (cookies_from_browser,)
        logger.info("Using cookies from browser: %s", cookies_from_browser)

    logger.info("Starting audio download: %s", url)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info: dict = ydl.extract_info(url, download=True)  # type: ignore[assignment]
    except yt_dlp.utils.GeoRestrictedError as exc:
        raise DownloadError(
            "This video is geo-restricted and cannot be accessed from your "
            "current location."
        ) from exc
    except yt_dlp.utils.ExtractorError as exc:
        msg = str(exc).lower()
        if "removed" in msg or "deleted" in msg or "not found" in msg:
            raise DownloadError("Video has been deleted or is unavailable.") from exc
        raise DownloadError(f"Failed to extract video info: {exc}") from exc
    except yt_dlp.utils.DownloadError as exc:
        raise DownloadError(f"Download failed: {exc}") from exc
    except Exception as exc:
        raise DownloadError(f"Unexpected error during download: {exc}") from exc

    if info is None:
        raise DownloadError("yt-dlp returned no info for the URL.")

    # Locate the output WAV file
    actual_id = info.get("id", video_id or "audio")
    audio_path = outdir / f"{actual_id}.wav"
    if not audio_path.exists():
        # Fallback: find any WAV in the output dir
        wavs = list(outdir.glob("*.wav"))
        if not wavs:
            raise DownloadError(
                f"Audio file not found after download. Expected: {audio_path}"
            )
        audio_path = wavs[0]

    result = DownloadResult(
        audio_path=audio_path,
        title=info.get("title", ""),
        author=info.get("uploader", "") or info.get("channel", ""),
        duration=float(info.get("duration", 0) or 0),
        description=info.get("description", "") or "",
        video_id=info.get("id", video_id),
    )

    logger.info(
        "Audio saved: %s (%.1fs, by %s)", result.audio_path, result.duration, result.author
    )
    return result

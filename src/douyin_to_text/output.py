"""Format transcription results for output.

Supports three output formats:

* **json** – full structured output with metadata.
* **markdown** – human-friendly with title, segments table, and full text.
* **text** – bare transcript text, suitable for piping.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from enum import Enum
from typing import Optional

from .downloader import DownloadResult
from .engines.base import TranscriptResult

logger = logging.getLogger("douyin_to_text")


# ---------------------------------------------------------------------------
# Format enum
# ---------------------------------------------------------------------------


class OutputFormat(str, Enum):
    """Supported output formats."""

    JSON = "json"
    MARKDOWN = "markdown"
    TEXT = "text"


# ---------------------------------------------------------------------------
# Internal formatters
# ---------------------------------------------------------------------------


def _format_timestamp(seconds: float) -> str:
    """Convert *seconds* to ``MM:SS.mmm`` for display."""
    mins, secs = divmod(seconds, 60)
    return f"{int(mins):02d}:{secs:06.3f}"


def _format_json(
    result: TranscriptResult,
    download_info: Optional[DownloadResult],
    url: str,
) -> str:
    """Produce a JSON string with full metadata."""
    data: dict = {
        "status": "ok",
        "url": url,
        "title": download_info.title if download_info else "",
        "author": download_info.author if download_info else "",
        "duration_seconds": download_info.duration if download_info else result.audio_duration,
        "engine": result.engine_name,
        "language": result.language,
        "transcript": result.text,
        "full_text": result.text,
        "segments": [asdict(s) for s in result.segments],
        "metadata": {
            "model": result.model_name,
            "processing_time_seconds": result.processing_time,
            "audio_duration_seconds": result.audio_duration,
        }
    }
    if download_info is not None:
        data["metadata"].update({
            "description": download_info.description,
            "video_id": download_info.video_id,
        })
    return json.dumps(data, ensure_ascii=False, indent=2)


def _format_markdown(
    result: TranscriptResult,
    download_info: Optional[DownloadResult],
    url: str,
) -> str:
    """Produce a Markdown document."""
    lines: list[str] = []

    # Title
    title = download_info.title if download_info else "Transcript"
    lines.append(f"# {title}")
    lines.append("")

    # Metadata
    if download_info:
        lines.append(f"- **Author:** {download_info.author}")
        lines.append(f"- **Duration:** {_format_timestamp(download_info.duration)}")
        lines.append(f"- **Video ID:** {download_info.video_id}")
    lines.append(f"- **URL:** {url}")
    lines.append(f"- **Engine:** {result.engine_name} ({result.model_name})")
    lines.append(f"- **Language:** {result.language}")
    lines.append("")

    # Segments table
    if result.segments:
        lines.append("## Segments")
        lines.append("")
        lines.append("| Start | End | Text |")
        lines.append("|-------|-----|------|")
        for seg in result.segments:
            start = _format_timestamp(seg.start)
            end = _format_timestamp(seg.end)
            # Escape pipe characters in text
            text = seg.text.replace("|", "\\|")
            lines.append(f"| {start} | {end} | {text} |")
        lines.append("")

    # Full transcript
    lines.append("## Full Transcript")
    lines.append("")
    lines.append(result.text)
    lines.append("")

    return "\n".join(lines)


def _format_text(result: TranscriptResult) -> str:
    """Produce plain transcript text."""
    return result.text


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def format_output(
    result: TranscriptResult,
    download_info: Optional[DownloadResult] = None,
    fmt: str | OutputFormat = OutputFormat.JSON,
    url: str = "",
) -> str:
    """Format a :class:`TranscriptResult` in the requested format.

    Parameters
    ----------
    result:
        The transcription result.
    download_info:
        Optional download metadata (title, author, etc.).
    fmt:
        Output format – ``"json"``, ``"markdown"``, or ``"text"``.
    url:
        Original URL, included in JSON/Markdown output.

    Returns
    -------
    str
        The formatted output string.
    """
    if isinstance(fmt, str):
        try:
            fmt = OutputFormat(fmt.lower())
        except ValueError:
            logger.warning("Unknown format %r, falling back to JSON", fmt)
            fmt = OutputFormat.JSON

    if fmt is OutputFormat.JSON:
        return _format_json(result, download_info, url)
    if fmt is OutputFormat.MARKDOWN:
        return _format_markdown(result, download_info, url)
    return _format_text(result)

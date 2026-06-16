"""CLI entry point for douyin-to-text.

Design rules
------------
* **stdout** is reserved for machine-readable data (JSON / markdown / plain).
* **stderr** carries human-readable logs and progress via :mod:`logging`.
* Errors are emitted as ``{"status": "error", "message": "…"}`` on stdout so
  that callers (including AI agents) can parse them uniformly.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import TextIO

import click

from douyin_to_text import __version__

# ---------------------------------------------------------------------------
# Logging setup — always to stderr
# ---------------------------------------------------------------------------

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
logger = logging.getLogger("douyin_to_text")


def _configure_logging(*, verbose: bool) -> None:
    """Set up root logger to write to *stderr*."""
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    logging.basicConfig(level=level, handlers=[handler])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _emit_json(data: dict | list, file: TextIO = sys.stdout) -> None:
    """Write *data* as compact UTF-8 JSON to *file*."""
    click.echo(json.dumps(data, ensure_ascii=False, indent=2), file=file)


def _emit_error(message: str, *, exit_code: int = 1) -> None:  # noqa: WPS210
    """Print a structured error to stdout and exit."""
    _emit_json({"status": "error", "message": message})
    sys.exit(exit_code)


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def main() -> None:
    """douyin-to-text — extract speech-to-text from Douyin / TikTok videos."""


# ---------------------------------------------------------------------------
# transcribe
# ---------------------------------------------------------------------------


@main.command()
@click.argument("url")
@click.option(
    "--engine",
    type=click.Choice(["sensevoice", "faster-whisper", "auto"], case_sensitive=False),
    default="auto",
    show_default=True,
    help="ASR engine to use.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "markdown", "plain"], case_sensitive=False),
    default="json",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--language",
    type=click.Choice(["zh", "en", "auto"], case_sensitive=False),
    default="auto",
    show_default=True,
    help="Language hint for the ASR engine.",
)
@click.option(
    "--model-size",
    type=click.Choice(["tiny", "base", "small", "medium", "large-v3-turbo"]),
    default="base",
    help="Whisper model size (only applies to whisper engine).",
)
@click.option(
    "--output-file",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    default=None,
    help="Write output to file instead of stdout.",
)
@click.option(
    "--keep-audio",
    is_flag=True,
    default=False,
    help="Keep downloaded audio file after transcription.",
)
@click.option(
    "--temp-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="Temporary directory for downloaded audio.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Enable verbose (DEBUG) logging to stderr.",
)
def transcribe(  # noqa: WPS211 — many args by design (CLI surface)
    url: str,
    engine: str,
    output_format: str,
    language: str,
    model_size: str,
    output_file: Path | None,
    keep_audio: bool,
    temp_dir: Path | None,
    verbose: bool,
) -> None:
    """Transcribe audio from a Douyin / TikTok video URL."""
    _configure_logging(verbose=verbose)
    logger.debug(
        "transcribe called: url=%s engine=%s format=%s lang=%s model=%s",
        url,
        engine,
        output_format,
        language,
        model_size,
    )

    try:
        # Late imports so the top-level CLI loads fast even when heavy deps
        # (torch, onnxruntime, …) are installed.
        from douyin_to_text.transcriber import transcribe_url  # type: ignore[import-untyped]

        result = transcribe_url(
            url=url,
            engine=engine,
            language=language,
            model_size=model_size,
            fmt=output_format,
            keep_audio=keep_audio,
            temp_dir=temp_dir,
        )
    except ImportError as exc:
        _emit_error(f"Missing dependency for engine '{engine}': {exc}")
    except Exception as exc:  # noqa: BLE001 — top-level catch for structured output
        logger.exception("Transcription failed")
        _emit_error(str(exc))

    # --- format & emit ---------------------------------------------------
    output = result

    if output_file is not None:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(output, encoding="utf-8")
        logger.info("Output written to %s", output_file)
    else:
        click.echo(output)


def _format_result(result: dict, fmt: str) -> str:
    """Serialize *result* dict into the requested format string."""
    if fmt == "json":
        return json.dumps(result, ensure_ascii=False, indent=2)
    if fmt == "markdown":
        parts: list[str] = [f"# {result.get('title', 'Transcription')}", ""]
        for seg in result.get("segments", []):
            start = seg.get("start", "")
            text = seg.get("text", "")
            parts.append(f"**[{start}]** {text}")
        return "\n".join(parts)
    # plain
    return "\n".join(
        seg.get("text", "") for seg in result.get("segments", [])
    )


# ---------------------------------------------------------------------------
# engines
# ---------------------------------------------------------------------------


@main.command()
def engines() -> None:
    """List available ASR engines and their installation status."""
    engine_info: list[dict[str, str | bool]] = []

    for name, pkg in (
        ("sensevoice", "funasr"),
        ("faster-whisper", "faster_whisper"),
    ):
        try:
            __import__(pkg)
            available = True
        except ImportError:
            available = False
        engine_info.append({"name": name, "available": available})

    _emit_json(engine_info)


# ---------------------------------------------------------------------------
# version
# ---------------------------------------------------------------------------


@main.command()
def version() -> None:
    """Show version information."""
    _emit_json({"name": "douyin-to-text", "version": __version__})

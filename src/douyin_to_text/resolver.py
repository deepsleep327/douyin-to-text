"""Resolve Douyin short URLs to full URLs and extract video IDs.

Supports ``v.douyin.com`` short links, direct ``www.douyin.com/video/`` and
``www.douyin.com/note/`` URLs, plus preliminary detection of Bilibili and
YouTube for future extensibility.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger("douyin_to_text")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.0 Mobile/15E148 Safari/604.1"
)

_REDIRECT_TIMEOUT = 15  # seconds

# Regex patterns for video-ID extraction
_DOUYIN_VIDEO_ID_RE = re.compile(r"/(?:video|note)/(\d+)")
_DOUYIN_MODAL_ID_RE = re.compile(r"modal_id=(\d+)")

# Short-link host
_DOUYIN_SHORT_HOST = "v.douyin.com"


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


class Platform(str, Enum):
    """Supported (or detected) video platforms."""

    DOUYIN = "douyin"
    BILIBILI = "bilibili"
    YOUTUBE = "youtube"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ResolvedURL:
    """Result of resolving a Douyin URL."""

    original_url: str
    resolved_url: str
    video_id: Optional[str]
    platform: Platform


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _detect_platform(url: str) -> Platform:
    """Detect which platform a URL belongs to."""
    lower = url.lower()
    if "douyin.com" in lower:
        return Platform.DOUYIN
    if "bilibili.com" in lower or "b23.tv" in lower:
        return Platform.BILIBILI
    if "youtube.com" in lower or "youtu.be" in lower:
        return Platform.YOUTUBE
    return Platform.UNKNOWN


def _is_short_link(url: str) -> bool:
    """Return ``True`` when *url* looks like a ``v.douyin.com`` short link."""
    return _DOUYIN_SHORT_HOST in url.lower()


def _follow_redirects(url: str) -> str:
    """Follow HTTP 3xx redirects and return the final URL.

    Uses :mod:`urllib.request` to avoid adding ``requests`` as a dependency.
    Only the HEAD-like first response is inspected; the response body is
    discarded.
    """
    req = Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urlopen(req, timeout=_REDIRECT_TIMEOUT) as resp:  # noqa: S310
            return resp.url  # type: ignore[return-value]
    except HTTPError as exc:
        # Some 3xx codes raise HTTPError but still carry a useful URL.
        if exc.url:
            return exc.url
        raise URLResolveError(f"HTTP {exc.code} when resolving {url}") from exc
    except URLError as exc:
        raise URLResolveError(f"Network error resolving {url}: {exc.reason}") from exc


def _extract_video_id(url: str) -> Optional[str]:
    """Extract a numeric video ID from a resolved Douyin URL."""
    # /video/1234567890 or /note/1234567890
    match = _DOUYIN_VIDEO_ID_RE.search(url)
    if match:
        return match.group(1)
    # ?modal_id=1234567890
    match = _DOUYIN_MODAL_ID_RE.search(url)
    if match:
        return match.group(1)
    return None


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class URLResolveError(Exception):
    """Raised when a URL cannot be resolved."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def resolve_url(url: str) -> ResolvedURL:
    """Resolve a Douyin URL and extract its video ID.

    Parameters
    ----------
    url:
        A Douyin short link (``v.douyin.com/…``) or full URL.

    Returns
    -------
    ResolvedURL
        Structured result containing the original URL, the fully resolved
        URL, the extracted video ID (if any), and the detected platform.

    Raises
    ------
    URLResolveError
        If the URL cannot be resolved due to network or HTTP errors.
    ValueError
        If the URL does not appear to belong to Douyin.
    """
    url = url.strip()
    platform = _detect_platform(url)

    if platform == Platform.UNKNOWN:
        raise ValueError(
            f"Unsupported URL: {url!r}. "
            "Only Douyin, Bilibili, and YouTube URLs are recognised."
        )

    if platform != Platform.DOUYIN:
        logger.info("Detected platform: %s (not yet fully supported)", platform.value)
        return ResolvedURL(
            original_url=url,
            resolved_url=url,
            video_id=None,
            platform=platform,
        )

    # Resolve short links
    if _is_short_link(url):
        logger.debug("Resolving short link: %s", url)
        resolved = _follow_redirects(url)
        logger.debug("Resolved to: %s", resolved)
    else:
        resolved = url

    video_id = _extract_video_id(resolved)
    if video_id:
        logger.info("Extracted video ID: %s", video_id)
    else:
        logger.warning("Could not extract video ID from: %s", resolved)

    return ResolvedURL(
        original_url=url,
        resolved_url=resolved,
        video_id=video_id,
        platform=Platform.DOUYIN,
    )

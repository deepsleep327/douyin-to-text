from unittest.mock import patch
import pytest

from douyin_to_text.resolver import (
    Platform,
    ResolvedURL,
    URLResolveError,
    _detect_platform,
    _extract_video_id,
    _is_short_link,
    resolve_url,
)


def test_detect_platform():
    assert _detect_platform("https://v.douyin.com/abcde/") == Platform.DOUYIN
    assert _detect_platform("https://www.douyin.com/video/123456") == Platform.DOUYIN
    assert _detect_platform("https://www.bilibili.com/video/BV12345") == Platform.BILIBILI
    assert _detect_platform("https://b23.tv/abcde") == Platform.BILIBILI
    assert _detect_platform("https://www.youtube.com/watch?v=123") == Platform.YOUTUBE
    assert _detect_platform("https://youtu.be/123") == Platform.YOUTUBE
    assert _detect_platform("https://example.com") == Platform.UNKNOWN


def test_is_short_link():
    assert _is_short_link("https://v.douyin.com/abcde/") is True
    assert _is_short_link("https://www.douyin.com/video/123") is False


def test_extract_video_id():
    assert _extract_video_id("https://www.douyin.com/video/7123456789012345678?abc=1") == "7123456789012345678"
    assert _extract_video_id("https://www.douyin.com/note/7123456789012345678") == "7123456789012345678"
    assert _extract_video_id("https://www.douyin.com/discover?modal_id=7123456789012345678") == "7123456789012345678"
    assert _extract_video_id("https://www.douyin.com/user/123") is None


@patch("douyin_to_text.resolver._follow_redirects")
def test_resolve_url_short_link(mock_follow):
    mock_follow.return_value = "https://www.douyin.com/video/7123456789012345678"
    res = resolve_url("https://v.douyin.com/abcde/")
    
    assert res.original_url == "https://v.douyin.com/abcde/"
    assert res.resolved_url == "https://www.douyin.com/video/7123456789012345678"
    assert res.video_id == "7123456789012345678"
    assert res.platform == Platform.DOUYIN
    mock_follow.assert_called_once_with("https://v.douyin.com/abcde/")


def test_resolve_url_full_link():
    res = resolve_url("https://www.douyin.com/video/7123456789012345678")
    assert res.original_url == "https://www.douyin.com/video/7123456789012345678"
    assert res.resolved_url == "https://www.douyin.com/video/7123456789012345678"
    assert res.video_id == "7123456789012345678"
    assert res.platform == Platform.DOUYIN


def test_resolve_url_unsupported_platform():
    res = resolve_url("https://www.youtube.com/watch?v=123")
    assert res.original_url == "https://www.youtube.com/watch?v=123"
    assert res.resolved_url == "https://www.youtube.com/watch?v=123"
    assert res.video_id is None
    assert res.platform == Platform.YOUTUBE


def test_resolve_url_unknown_platform():
    with pytest.raises(ValueError, match="Unsupported URL"):
        resolve_url("https://example.com")

"""Shared pytest fixtures for douyin-to-text tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest


@pytest.fixture()
def tmp_audio_dir(tmp_path: Path) -> Path:
    """Return a temporary directory pre-created for audio downloads."""
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    return audio_dir


@pytest.fixture()
def sample_transcript_result() -> dict[str, Any]:
    """Return a representative transcription result dict for assertions."""
    return {
        "status": "ok",
        "url": "https://www.douyin.com/video/1234567890",
        "title": "测试视频",
        "engine": "sensevoice",
        "language": "zh",
        "duration_seconds": 15.3,
        "segments": [
            {"start": 0.0, "end": 3.2, "text": "你好，欢迎来到我的频道。"},
            {"start": 3.2, "end": 7.8, "text": "今天我们来聊一聊语音识别技术。"},
            {"start": 7.8, "end": 15.3, "text": "这是一个非常有趣的话题，让我们开始吧。"},
        ],
        "full_text": (
            "你好，欢迎来到我的频道。"
            "今天我们来聊一聊语音识别技术。"
            "这是一个非常有趣的话题，让我们开始吧。"
        ),
    }

import json
import pytest
from pathlib import Path

from douyin_to_text.engines.base import TranscriptResult, Segment
from douyin_to_text.downloader import DownloadResult
from douyin_to_text.output import format_output, OutputFormat


@pytest.fixture()
def sample_data():
    result = TranscriptResult(
        text="你好，欢迎。今天天气不错。",
        segments=[
            Segment(start=0.0, end=2.5, text="你好，欢迎。"),
            Segment(start=2.5, end=5.0, text="今天天气不错。")
        ],
        language="zh",
        engine_name="mock-engine",
        model_name="mock-model",
        audio_duration=5.0,
        processing_time=0.5
    )
    download_info = DownloadResult(
        audio_path=Path("/tmp/audio.wav"),
        title="测试视频标题",
        author="测试作者",
        duration=5.0,
        description="这是一个测试视频描述",
        video_id="1234567890"
    )
    return result, download_info


def test_format_output_json(sample_data):
    result, download_info = sample_data
    url = "https://www.douyin.com/video/1234567890"
    
    formatted = format_output(result, download_info, fmt=OutputFormat.JSON, url=url)
    data = json.loads(formatted)
    
    assert data["status"] == "ok"
    assert data["url"] == url
    assert data["title"] == "测试视频标题"
    assert data["author"] == "测试作者"
    assert data["duration_seconds"] == 5.0
    assert data["engine"] == "mock-engine"
    assert data["language"] == "zh"
    assert data["transcript"] == "你好，欢迎。今天天气不错。"
    assert data["full_text"] == "你好，欢迎。今天天气不错。"
    assert len(data["segments"]) == 2
    assert data["segments"][0]["start"] == 0.0
    assert data["segments"][0]["text"] == "你好，欢迎。"
    
    # Metadata
    meta = data["metadata"]
    assert meta["model"] == "mock-model"
    assert meta["processing_time_seconds"] == 0.5
    assert meta["audio_duration_seconds"] == 5.0
    assert meta["video_id"] == "1234567890"
    assert meta["description"] == "这是一个测试视频描述"


def test_format_output_markdown(sample_data):
    result, download_info = sample_data
    url = "https://www.douyin.com/video/1234567890"
    
    formatted = format_output(result, download_info, fmt=OutputFormat.MARKDOWN, url=url)
    
    assert "# 测试视频标题" in formatted
    assert "- **Author:** 测试作者" in formatted
    assert "- **Engine:** mock-engine (mock-model)" in formatted
    assert "| 00:00.000 | 00:02.500 | 你好，欢迎。 |" in formatted
    assert "## Full Transcript" in formatted
    assert "你好，欢迎。今天天气不错。" in formatted


def test_format_output_text(sample_data):
    result, _ = sample_data
    formatted = format_output(result, fmt=OutputFormat.TEXT)
    assert formatted == "你好，欢迎。今天天气不错。"

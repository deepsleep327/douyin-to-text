from unittest.mock import patch
from click.testing import CliRunner
import pytest
import json

from douyin_to_text.cli import main


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(main, ["version"])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["name"] == "douyin-to-text"
    assert "version" in data


def test_cli_engines():
    runner = CliRunner()
    result = runner.invoke(main, ["engines"])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert any(eng["name"] == "faster-whisper" for eng in data)


@patch("douyin_to_text.transcriber.transcribe_url")
def test_cli_transcribe_success(mock_transcribe):
    mock_transcribe.return_value = "{\"status\": \"ok\", \"transcript\": \"hello\"}"
    runner = CliRunner()
    result = runner.invoke(main, ["transcribe", "https://v.douyin.com/abcde/"])
    
    assert result.exit_code == 0
    assert "hello" in result.output
    mock_transcribe.assert_called_once_with(
        url="https://v.douyin.com/abcde/",
        engine="auto",
        language="auto",
        model_size="base",
        fmt="json",
        keep_audio=False,
        temp_dir=None,
        cookies_from_browser=None,
    )


@patch("douyin_to_text.transcriber.transcribe_url")
def test_cli_transcribe_failure(mock_transcribe):
    mock_transcribe.side_effect = Exception("Download error")
    runner = CliRunner()
    result = runner.invoke(main, ["transcribe", "https://v.douyin.com/abcde/"])
    
    # Even if transcription fails, errors are output on stdout in JSON and exit_code is 1
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["status"] == "error"
    assert "Download error" in data["message"]

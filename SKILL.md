---
name: douyin-to-text
description: |
  从抖音/TikTok视频链接提取语音文字内容，输出结构化JSON。
  纯CLI工具，Agent通过bash调用。支持SenseVoice和faster-whisper双引擎。
  Skill只负责提取原始文本，润色/整理由调用方Agent负责。
---

# douyin-to-text

将抖音视频的语音内容转录为文字，输出结构化 JSON。

## 安装

```bash
# 最小安装 (需要手动选择 ASR 引擎)
pip install douyin-to-text

# 推荐：SenseVoice 引擎 (中文最快)
pip install "douyin-to-text[sensevoice]"

# 备选：faster-whisper 引擎 (多语言)
pip install "douyin-to-text[whisper]"
```

## 前置依赖

- `ffmpeg` 必须已安装并在 PATH 中
- `yt-dlp` 会自动安装

## 核心命令

### 转录视频

```bash
# 基本用法 - 输出 JSON 到 stdout
douyin-to-text transcribe "https://v.douyin.com/xxx"

# 指定引擎和输出格式
douyin-to-text transcribe "https://v.douyin.com/xxx" --engine sensevoice --format markdown

# 输出到文件
douyin-to-text transcribe "https://v.douyin.com/xxx" --output-file transcript.json

# 保留音频文件
douyin-to-text transcribe "https://v.douyin.com/xxx" --keep-audio --temp-dir ./audio
```

### 查看可用引擎

```bash
douyin-to-text engines
```

### 查看版本

```bash
douyin-to-text version
```

## JSON 输出格式

```json
{
  "status": "success",
  "url": "https://www.douyin.com/video/xxx",
  "title": "视频标题",
  "author": "作者名",
  "duration_seconds": 120.5,
  "engine": "sensevoice",
  "language": "zh",
  "transcript": "完整的转录文本...",
  "segments": [
    {"start": 0.0, "end": 2.5, "text": "大家好"},
    {"start": 2.5, "end": 5.0, "text": "今天我们来聊一下..."}
  ],
  "metadata": {
    "model": "sensevoice-small",
    "processing_time_seconds": 3.2,
    "audio_duration_seconds": 120.5
  }
}
```

## 错误输出格式

```json
{
  "status": "error",
  "message": "错误描述",
  "url": "原始URL"
}
```

## Agent 工作流推荐

1. 调用 `douyin-to-text transcribe <URL>` 获取 JSON 输出
2. 解析 JSON，提取 `transcript` 字段获得原始文本
3. 对文本进行润色、摘要、分段等后处理
4. 将处理后的内容写入目标笔记系统 (Obsidian, Notion 等)

## 选项参考

| 选项 | 值 | 默认值 | 说明 |
|:---|:---|:---|:---|
| `--engine` | sensevoice, faster-whisper, auto | auto | ASR引擎，auto自动选最快可用引擎 |
| `--format` | json, markdown, plain | json | 输出格式 |
| `--language` | zh, en, auto | auto | 语言 |
| `--model-size` | small, base, large | small | 模型大小 |
| `--output-file` | PATH | - | 输出到文件 |
| `--keep-audio` | - | false | 保留下载的音频 |
| `--temp-dir` | PATH | 系统临时目录 | 临时文件目录 |
| `--verbose` | - | false | 详细日志到stderr |

# 🎙️ douyin-to-text

> 从抖音/TikTok 视频提取语音文字 — Agent-Native CLI 工具

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)

**douyin-to-text** 是一个专为 AI Agent 设计的命令行工具，从抖音视频链接中提取语音内容并转为结构化文字。

## ✨ 特性

- 🚀 **极速转录** — SenseVoice 引擎，10秒音频处理仅需百毫秒级
- 🤖 **Agent-Native** — 标准 JSON 输出，可被任何 AI Agent 框架直接解析
- 🔌 **可插拔引擎** — 支持 SenseVoice (中文极速) 和 faster-whisper (多语言)
- 💻 **纯 CPU 推理** — 无需 GPU，4核 CPU + 8GB RAM 即可运行
- 📦 **零 LLM 依赖** — Skill 只做转录，润色交给 Agent
- 🛡️ **生产级质量** — 完整错误处理、结构化日志、类型注解

## 📥 安装

### 推荐安装 (SenseVoice 引擎，中文最快)

```bash
pip install "douyin-to-text[sensevoice]"
```

### 备选安装 (faster-whisper 引擎，多语言)

```bash
pip install "douyin-to-text[whisper]"
```

### 全部安装

```bash
pip install "douyin-to-text[all]"
```

### 前置依赖

- **Python** >= 3.10
- **FFmpeg** — 必须已安装 ([安装指南](https://ffmpeg.org/download.html))

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

## 🚀 快速开始

### 基本用法

```bash
# 转录抖音视频 (输出 JSON)
douyin-to-text transcribe "https://v.douyin.com/xxxxxxx"

# 输出 Markdown 格式
douyin-to-text transcribe "https://v.douyin.com/xxxxxxx" --format markdown

# 输出纯文本
douyin-to-text transcribe "https://v.douyin.com/xxxxxxx" --format plain

# 指定引擎
douyin-to-text transcribe "https://v.douyin.com/xxxxxxx" --engine sensevoice

# 保存到文件
douyin-to-text transcribe "https://v.douyin.com/xxxxxxx" -o transcript.json
```

### 查看可用引擎

```bash
douyin-to-text engines
```

### 输出示例

```json
{
  "status": "success",
  "url": "https://www.douyin.com/video/7380000000000000000",
  "title": "AI 编程效率提升 10 倍的秘密",
  "author": "科技博主",
  "duration_seconds": 65.3,
  "engine": "sensevoice",
  "language": "zh",
  "transcript": "大家好，今天来聊一下如何用 AI 提升编程效率...",
  "segments": [
    {"start": 0.0, "end": 2.1, "text": "大家好"},
    {"start": 2.1, "end": 5.8, "text": "今天来聊一下如何用 AI 提升编程效率"}
  ],
  "metadata": {
    "model": "sensevoice-small",
    "processing_time_seconds": 1.8,
    "audio_duration_seconds": 65.3
  }
}
```

## 🤖 Agent 集成

### 推荐工作流

```
Agent 收到抖音链接
  → douyin-to-text transcribe <URL> --format json
  → Agent 解析 JSON，提取 transcript
  → Agent 润色、摘要、格式化
  → Agent 写入 Obsidian / Notion / 笔记
```

### Agent Skill 文件

项目根目录的 `SKILL.md` 文件包含了 Agent 所需的完整使用说明。将此项目路径添加到 Agent 的 skill 搜索路径即可自动发现。

### Python API 调用

```python
from douyin_to_text.transcriber import transcribe_url

result = transcribe_url(
    url="https://v.douyin.com/xxxxxxx",
    engine="auto",
    language="auto",
    output_format="json"
)
print(result)
```

## ⚡ 性能基准

在 Intel i5-4210U (4核 1.7GHz, 12GB RAM, 纯 CPU) 上的实测性能：

| 视频时长 | SenseVoice-Small | faster-whisper (base) |
|:---|:---|:---|
| 10s 短视频 | ~0.5s | ~3s |
| 60s 中视频 | ~2s | ~15s |
| 5min 长视频 | ~10s | ~60s |

## 🏗️ 架构

```
douyin-to-text transcribe <URL>
       │
       ├── resolver      解析抖音短链接
       ├── downloader     yt-dlp 提取音频 (WAV 16kHz)
       ├── engines/       可插拔 ASR 引擎
       │   ├── sensevoice     SenseVoice ONNX (优先)
       │   └── faster_whisper CTranslate2 (备选)
       └── output         格式化输出 (JSON/MD/Plain)
```

## 🧑‍💻 开发

```bash
# 克隆项目
git clone https://github.com/y3275969734-arch/douyin-to-text.git
cd douyin-to-text

# 安装开发依赖
pip install -e ".[all,dev]"

# 运行测试
pytest tests/ -v
```

## 📄 License

[MIT](LICENSE) — 自由使用、修改、分发。

## 🙏 致谢

- [SenseVoice](https://github.com/FunAudioLLM/SenseVoice) — 阿里开源的高性能语音识别模型
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — CTranslate2 加速的 Whisper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — 强大的视频/音频下载工具

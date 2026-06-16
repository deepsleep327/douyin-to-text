# Douyin-to-Text 🚀

> ⚡ **Agent-Native CLI 工具**：一键提取抖音 (Douyin/TikTok) 视频文案，自动转写为结构化 Markdown/JSON，专为 AI Agent、RAG 知识库与本地工作流设计。

## 🌟 特性 (Features)

- **一键提取**：丢入任意抖音分享链接（如 `v.douyin.com/xxx` 或网页版链接），自动解析、下载音频、剥离提取。
- **纯本地推理 (Local First)**：无需调用任何外部大模型 API，保护隐私，拒绝网络超量收费。
- **专为低配优化**：深度适配普通 CPU，无需昂贵的独立显卡。
- **结构化输出**：自动排版为带有元数据（标题、时长、作者）的 Markdown 或 JSON，无缝对接 Obsidian 和 Agent。
- **双擎驱动 (Dual Engines)**：
  - `faster-whisper` (默认)：内置 VAD（静音过滤算法），超长视频**绝不吞字**，`base` 模型兼顾极速与高精度（低配 CPU 推荐）。
  - `sensevoice` (进阶)：阿里强大的多模态语音模型，支持识别情感标签、BGM、多语种。

## 📦 安装 (Installation)

由于现代 Linux 环境引入了 PEP 668（externally-managed-environment），推荐使用 `pipx` 或在虚拟环境中安装本项目，以保持系统环境干净。

### 先决条件
请确保系统已安装 `ffmpeg`：
```bash
sudo apt update
sudo apt install ffmpeg
```

### 安装步骤
```bash
git clone https://github.com/lemon/douyin-to-text.git
cd douyin-to-text
pipx install -e .[all]
```
*(注意：`[all]` 会同时安装 whisper 和 sensevoice 依赖。如果只需轻量使用，可改为 `.[whisper]`。)*

## 🛠 使用教程 (Usage)

直接在终端输入指令提取视频文案：

```bash
# 最简用法（默认使用 faster-whisper 的 base 模型，兼顾极速与精度）
douyin-to-text transcribe "https://v.douyin.com/xxxxxx/"

# 输出为 JSON 格式（适合 Agent 与代码调用）
douyin-to-text transcribe "https://v.douyin.com/xxxxxx/" --format json

# 指定使用 SenseVoice 引擎提取多模态情绪标签（首次运行会自动下载模型）
douyin-to-text transcribe "https://v.douyin.com/xxxxxx/" --engine sensevoice
```

### 参数选项
- `--engine`: 指定推理引擎，可选 `faster-whisper` 或 `sensevoice`（默认：`faster-whisper`）。
- `--model-size`: Whisper 引擎的模型大小，可选 `tiny`, `base`, `small`, `medium`, `large-v3-turbo`（默认：`base`）。
- `--format`: 输出格式，可选 `markdown`, `json`, `plain`（默认：`markdown`）。
- `--output-file`: 将结果直接写入指定文件。

## 🧠 引擎选型指南

| 引擎 | 适用场景 | CPU 速度 | 准确度 | 是否掉字 | 特殊功能 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **faster-whisper** (默认) | 所有长短视频，笔记整理 | ⚡极快 | ⭐⭐⭐⭐⭐ | 绝对不会 | 极简环境依赖 |
| **sensevoice** (进阶) | 短视频或需情绪分析 | 🐌一般 | ⭐⭐⭐⭐ | 很少（已内置分段算法） | 情绪、BGM识别 |

## 🤝 贡献与感谢
本项目受 `yt-dlp`、`faster-whisper` 以及 `FunASR` 驱动，欢迎提交 Issue 与 PR 共同完善这个 Agent 小工具！

## 📄 许可证
MIT License

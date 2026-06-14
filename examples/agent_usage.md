# Agent 集成示例

## 1. Antigravity / Gemini Agent

Agent 的 SKILL.md 自动发现机制可以直接读取本项目的 `SKILL.md` 文件。

### 安装为 Agent Skill

将 `douyin-to-text` 目录路径添加到 Agent 的 skill 搜索路径：

```
~/.gemini/config/plugins/user-skills-plugin/skills/douyin-to-text -> /path/to/douyin-to-text
```

### Agent 自动调用示例

当用户发送抖音链接时，Agent 会自动：

1. 识别链接类型
2. 调用 `douyin-to-text transcribe`
3. 对原始文本进行润色
4. 输出整理后的内容

```bash
# Agent 执行的命令
douyin-to-text transcribe "https://v.douyin.com/xxx" --format json

# Agent 解析 JSON 输出中的 transcript 字段
# Agent 使用自身的 LLM 能力进行润色：
#   - 去除口语化表达
#   - 添加标点符号
#   - 分段整理
#   - 生成摘要
```

## 2. 通用 Agent 框架

### Shell 命令调用

```bash
# 获取 JSON 输出并用 jq 提取文本
TRANSCRIPT=$(douyin-to-text transcribe "$URL" | jq -r '.transcript')

# 检查是否成功
STATUS=$(douyin-to-text transcribe "$URL" | jq -r '.status')
if [ "$STATUS" = "error" ]; then
    echo "转录失败"
fi
```

### Python API

```python
import json
import subprocess

def get_transcript(url: str) -> dict:
    """调用 douyin-to-text CLI 获取转录结果"""
    result = subprocess.run(
        ["douyin-to-text", "transcribe", url, "--format", "json"],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

# 使用
data = get_transcript("https://v.douyin.com/xxx")
if data["status"] == "success":
    raw_text = data["transcript"]
    # 传递给 LLM 润色...
```

## 3. 批量处理

```bash
# 从文件读取 URL 列表，逐个处理
while IFS= read -r url; do
    douyin-to-text transcribe "$url" --format json >> results.jsonl
    sleep 2  # 避免被限流
done < urls.txt
```

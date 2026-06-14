# Obsidian 工作流集成

## 概述

通过 `douyin-to-text` + Agent 的组合，实现"一键抖音链接 → Obsidian 笔记"的自动化工作流。

## 工作流程

```
用户发送抖音链接给 Agent
    ↓
Agent 调用 douyin-to-text 提取文字
    ↓
Agent 润色、整理文本
    ↓
Agent 写入 Obsidian vault 的指定目录
```

## 输出 Markdown 模板

Agent 润色后可以生成如下格式的 Obsidian 笔记：

```markdown
---
title: "{{title}}"
author: "{{author}}"
source: "{{url}}"
duration: {{duration_seconds}}s
created: {{date}}
tags: [douyin, transcript]
---

# {{title}}

> 来源: [抖音视频]({{url}}) | 作者: {{author}} | 时长: {{duration}}

## 摘要

{{agent 生成的摘要}}

## 完整文本

{{agent 润色后的文本}}

## 关键要点

{{agent 提取的要点列表}}

## 原始转录

<details>
<summary>点击展开原始转录文本</summary>

{{raw transcript}}

</details>
```

## 配置 Obsidian Vault 路径

在 Agent 的配置中设置 Obsidian vault 路径：

```bash
# 示例：将转录笔记保存到 Obsidian vault
douyin-to-text transcribe "$URL" --format json | \
  jq -r '.transcript' > \
  "$HOME/Obsidian/MyVault/Transcripts/$(date +%Y%m%d)_douyin.md"
```

## 与 Obsidian 插件配合

### Templater 插件

可以创建 Templater 模板，Agent 填充后保存：

```markdown
<%*
const data = JSON.parse(tp.frontmatter.raw_data);
-%>
# <% data.title %>

**作者**: <% data.author %>
**时长**: <% Math.round(data.duration_seconds / 60) %> 分钟

## 内容

<% data.transcript %>
```

### Dataview 插件

使用 Dataview 查询所有转录笔记：

```dataview
TABLE author, duration, created
FROM #douyin AND #transcript
SORT created DESC
```

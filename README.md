# OpenClaw WeChat Publishing Kit

给 OpenClaw 用的公众号发布技能包。

这个包安装后提供 3 个 skill：
- `wechat-publish-from-materials`（主入口：材料 → 文章）
- `wechat-draft-publisher`（发布入口：Markdown → 草稿箱）
- `wechat-illustrated-publisher`（插图链 + 发布链统一入口）

---

## 先说最重要的一步：先选你的配图模式

安装后第一件事，不是先看一堆参数，而是先选下面 3 种模式之一：

1. **纯文字发布（最快）**
   - 不配图，只把内容整理好后推进草稿箱。
2. **我自己提供图片**
   - 你给封面/正文图，系统负责插入和发布检查。
3. **AI 自动配图**
   - 系统先做插图规划，再走生图链（默认 MiniMax，可切换 provider）。

> 建议：第一次先走「纯文字发布」，跑通后再开配图。

---

## 第一次接入（5 分钟）

### 1) 克隆并安装

```bash
git clone https://gitee.com/woipanda/openclaw-wechat-publishing-kit.git
cd openclaw-wechat-publishing-kit
bash install.sh
```

### 2) 填你的 persona

安装后编辑：

```bash
~/.openclaw/skills/wechat-publish-from-materials/user-templates/persona.md
```

最少写清：你是谁、写什么、语气风格、你希望结尾怎么引导读者。

### 3) 填公众号配置

安装脚本会自动在首次安装时创建以下文件（若不存在）：
- `~/.openclaw/skills/wechat-draft-publisher/config/credentials.json`
- `~/.openclaw/skills/wechat-draft-publisher/config/settings.json`

你只需要补：
- `appid`
- `secret`
- `author`

### 4) 连通性检查

```bash
python3 ~/.openclaw/skills/wechat-draft-publisher/scripts/check_wechat_connection.py
```

### 5) 直接用一句话开始

#### A. 纯文字发布
```text
请按我的 persona，把这份材料整理成公众号文章，先不要配图，检查后推到草稿箱。
```

#### B. 我自己提供图片
```text
请按我的 persona，把这份材料整理成公众号文章；封面和正文配图我自己提供，你帮我一起处理后推到草稿箱。
```

#### C. AI 自动配图
```text
请按我的 persona，把这份材料整理成公众号文章，并为合适段落生成插图方案与 AI 配图，检查后推到草稿箱。
```

---

## 你会得到什么

按模式不同，这套能力会帮你完成：
- 材料整理成公众号正文
- （可选）插图规划 + 图位 + prompt
- （可选）真实生图并回填正文
- 发布前检查（封面策略 / 配图状态 / next action）
- 推送到微信公众号草稿箱

---

## 最常见问题

### Q1：我必须先学插图链吗？
不用。第一次建议先跑「纯文字发布」。

### Q2：我已经有 Markdown，能直接发吗？
可以，直接用 `wechat-draft-publisher`。

### Q3：AI 配图默认走什么？
默认 MiniMax；可切换到即梦 / Seedream / Ark 兼容链。

---

## 进阶文档

- 主入口 skill 说明：`skills/wechat-publish-from-materials/README.md`
- 插图统一入口：`skills/wechat-illustrated-publisher/README.md`
- 发布链细节：`skills/wechat-draft-publisher/SKILL.md`

---

## 安全说明

- 不要把真实 `credentials.json` 提交到 git。
- 不要把真实 `settings.json` 提交到 git。
- 不要在 README / SKILL / 示例里暴露 API key 或 AppSecret。

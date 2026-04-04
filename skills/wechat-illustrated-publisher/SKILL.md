---
name: wechat-illustrated-publisher
description: 当用户已经有 Markdown 文章，想把“插图规划、prompt 包、可选真实生图、发布前检查、推进微信公众号草稿箱”收成一个统一入口时使用。尤其适用于“帮我把这篇文章带图发到公众号”“我已经有 generated plan，直接检查/发布”“把原本分散的插图链和发布链做成一个可安装、可复用、可交付 skill 产品”这类场景。它是一个组合型 skill：统一调用 `wechat-publish-from-materials` 和 `wechat-draft-publisher`，对第一次接入者优先暴露最短成功路径。不要用于：从零写正文、资料搜集、选题讨论、脱离公众号发布场景的单纯生图实验。
---

# WeChat Illustrated Publisher

这是一个把**带插图的公众号发布链**收成单独产品入口的 skill。

它的目标不是替代底层能力，而是让用户第一次接入时，不需要自己理解两套 skill 之间怎么拼。

底层依赖仍然是：
- `wechat-publish-from-materials`
- `wechat-draft-publisher`

但对外入口收口成一个：
- `scripts/publish_with_illustrations.py`

## 它解决什么问题

用户原本常见的痛点是：
- 文章已经有了，但不知道哪些段落该配图
- 已经做了图位规划，但不知道怎么接到 publisher
- 已经生好图了，但不知道怎么统一检查 / 发布
- 不想在“插图 skill”和“发布 skill”之间手工来回切换

这个 skill 解决的是：

> **把 Markdown 文章稳定推进到“带插图、可检查、可进草稿箱”的状态。**

## 第一次成功路径

### 用户最少要准备什么
1. 一篇 Markdown 文章
2. 微信公众号发布配置（给 `wechat-draft-publisher` 用）
3. 二选一：
   - 已有 `illustration-plan.generated.json`
   - 或准备好真实生图所需配置（当前走 MiniMax 官方生图）

### 用户第一轮最推荐怎么开始
先不要直接发布，先跑检查：

```bash
python3 scripts/publish_with_illustrations.py \
  --article /path/to/article.md \
  --existing-generated-plan /path/to/illustration-plan.generated.json \
  --publisher-config ~/.openclaw/skills/wechat-draft-publisher/config/settings.json \
  --check
```

### 第一次成功的判断标准
至少同时满足：
- 成功产出 / 读取插图计划
- publisher `--check` 返回 `ok: true`
- 返回结果里有：
  - `cover_strategy`
  - `illustration_report`
  - `image_state`
  - `next_action = null`（或为空）

## 典型使用场景

### 场景 1：我已经有生图结果
最适合这个 skill。

你只需要给：
- 文章 Markdown
- `illustration-plan.generated.json`
- publisher 配置

它会直接完成：
- 计划读取
- publisher 检查
- 可选正式推草稿箱

### 场景 2：我只有文章，还没有最终图
它会先帮你完成：
- illustration plan
- slots / prompts
- 若显式加 `--generate`，再继续真实生图
- 然后再 check / publish

### 场景 3：我只想先看插图规划，不想真发
不传 `--existing-generated-plan`，也不加 `--generate`，默认会停在 dry-run：
- 产出 plan
- 产出 slots
- 产出 prompts
- 不真实生图
- 不正式发布

## 主入口脚本

```bash
python3 scripts/publish_with_illustrations.py
```

## 最常用命令

### 1. 复用已有 generated plan，先检查

```bash
python3 scripts/publish_with_illustrations.py \
  --article /path/to/article.md \
  --existing-generated-plan /path/to/illustration-plan.generated.json \
  --publisher-config ~/.openclaw/skills/wechat-draft-publisher/config/settings.json \
  --check
```

### 2. 复用已有 generated plan，直接推草稿箱

```bash
python3 scripts/publish_with_illustrations.py \
  --article /path/to/article.md \
  --existing-generated-plan /path/to/illustration-plan.generated.json \
  --publisher-config ~/.openclaw/skills/wechat-draft-publisher/config/settings.json \
  --publish
```

### 3. 只有文章，先产出 plan / slots / prompts

```bash
python3 scripts/publish_with_illustrations.py \
  --article /path/to/article.md \
  --publisher-config ~/.openclaw/skills/wechat-draft-publisher/config/settings.json
```

### 4. 只有文章，继续真实生图后再检查

```bash
python3 scripts/publish_with_illustrations.py \
  --article /path/to/article.md \
  --generate \
  --publisher-config ~/.openclaw/skills/wechat-draft-publisher/config/settings.json \
  --check
```

## 当前生图后端说明

当前真实生图路径默认按 **MiniMax 官方接口** 接：
- 默认接口：`https://api.minimaxi.com/v1/image_generation`
- 默认模型：`image-01`
- 默认按以下顺序取 key：
  - `--api-key`
  - `MINIMAX_API_KEY`
  - `ABAB_API_KEY`
  - `~/.openclaw/openclaw.json` 中 `models.providers.minimax.apiKey`

如果你不想真实生图，就不要加 `--generate`。
默认 dry-run 不会调用外部图片接口。

## 输出约定

统一输出 JSON，便于上层系统继续接。

至少应关注这些字段：
- `ok`
- `flow`
- `publish_result`
- `next_action`

如果跑了 `--check`，重点看：
- `flow.publisher_check.cover_strategy`
- `flow.publisher_check.image_state`
- `flow.publisher_check.illustration_report`
- `flow.publisher_check.next_action`

## 边界

这个 skill：
- 负责把“已有文章 + 插图链 + 发布链”收成统一入口
- 负责第一次接入时的最短成功路径
- 负责检查和推进到公众号草稿箱

这个 skill 不负责：
- 从零写正文
- 选题与资料搜集
- 承诺每篇文章都能自动配出高质量专属图
- 替用户做最终正式群发决策

## 对使用者的默认建议

第一次接入时，默认顺序应是：
1. 先 `--check`
2. 再看 `illustration_report / image_state / next_action`
3. 最后再决定要不要 `--publish`

一句话：

> 先把它当成“带插图的公众号预检与推进器”，而不是“无人值守自动群发器”。

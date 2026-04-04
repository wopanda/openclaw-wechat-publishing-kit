# wechat-illustrated-publisher

这是一个按 **skill-productizer** 思路收口过的 skill 产品入口。

它不是单纯多加一个脚本，而是把：
- 插图规划
- prompt 包
- 可选真实生图
- 发布前检查
- 推进微信公众号草稿箱

整理成一个第一次接入就能理解的统一入口。

底层依赖仍然是：
- `wechat-publish-from-materials`
- `wechat-draft-publisher`

但用户不需要先理解这两个 skill 的边界，再决定怎么拼。

---

## 这是什么

`wechat-illustrated-publisher` 是一个**带插图的公众号发布 skill**。

适合这样的人：
- 你已经有一篇 Markdown 文章
- 你想先配合适的插图，再推进公众号草稿箱
- 你不想自己手工串“插图 planning → prompts → 生图 → publisher check → 发布”

它最适合解决的是：

> **把一篇现成文章，推进到“带插图、可检查、可发草稿箱”的状态。**

---

## 你最少要准备什么

第一次接入时，最少准备：

1. 一篇 Markdown 文章
2. 微信公众号配置（给 `wechat-draft-publisher` 用）
3. 二选一：
   - 已有 `illustration-plan.generated.json`
   - 或准备好真实生图配置（当前默认走 MiniMax 官方生图）

---

## 你会得到什么

这条 skill 会统一帮你产出或推进：
- `illustration-plan.json`
- `illustration-slots.json`
- `illustration-prompts.md`
- `illustration-plan.generated.json`（如已有或真实生图成功）
- publisher `--check` 结果
- 可选正式推送到微信公众号草稿箱

---

## 第一次成功：最短路径

### 如果你已经有 generated plan
最推荐先跑检查：

```bash
python3 scripts/publish_with_illustrations.py \
  --article /path/to/article.md \
  --existing-generated-plan /path/to/illustration-plan.generated.json \
  --publisher-config ~/.openclaw/skills/wechat-draft-publisher/config/settings.json \
  --check
```

第一次成功的判断标准：
- 返回 `ok: true`
- 返回 `flow.publisher_check.ok: true`
- 有 `cover_strategy`
- 有 `illustration_report`
- `next_action` 为空或为 null

### 如果你还没有最终图
先跑 dry-run：

```bash
python3 scripts/publish_with_illustrations.py \
  --article /path/to/article.md \
  --publisher-config ~/.openclaw/skills/wechat-draft-publisher/config/settings.json
```

它会先停在：
- 插图计划
- slots
- prompts

不会真实生图，也不会正式发布。

---

## 常用命令

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

---

## 当前生图后端

当前真实生图默认按 **MiniMax 官方接口** 接入：

- 默认接口：`https://api.minimaxi.com/v1/image_generation`
- 默认模型：`image-01`

默认会按这个顺序取 key：
- `--api-key`（如果桥接脚本显式传入）
- `MINIMAX_API_KEY`
- `ABAB_API_KEY`
- `~/.openclaw/openclaw.json` 中的 `models.providers.minimax.apiKey`

如果你不加 `--generate`，就不会真实调用生图接口。

---

## 输出怎么看

脚本统一输出 JSON。

最值得看的字段：
- `ok`
- `flow`
- `publish_result`
- `next_action`

如果你跑的是 `--check`，重点看：
- `flow.publisher_check.cover_strategy`
- `flow.publisher_check.image_state`
- `flow.publisher_check.illustration_report`
- `flow.publisher_check.next_action`

---

## 它不负责什么

这个 skill 不负责：
- 从零写正文
- 帮你搜集资料
- 选题讨论
- 保证每篇都自动生出高质量专属图
- 替你做正式群发拍板

它负责的是：

> **把“已有文章 + 插图链 + 发布链”收成一个用户第一次就能用的统一入口。**

---

## 默认建议怎么用

第一次接入时，建议固定顺序：

1. 先 `--check`
2. 看 `illustration_report / image_state / next_action`
3. 再决定要不要 `--publish`

不要第一次就把它当“无人值守自动群发器”。

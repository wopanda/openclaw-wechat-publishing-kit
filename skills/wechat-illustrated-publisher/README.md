# wechat-illustrated-publisher

这是一个把“插图规划 + 可选生图衔接 + 微信公众号草稿箱发布”收成统一入口的新 skill。

它本身不重新实现底层能力，而是组合调用：
- `wechat-publish-from-materials`
- `wechat-draft-publisher`

## 适合什么情况

- 你已经有一篇 Markdown 文章
- 你想先做插图计划 / prompt 包
- 你已经有 `illustration-plan.generated.json`，想直接检查或发布
- 你希望这条链路不再拆成两个 skill 分开调用

## 主入口脚本

```bash
python3 scripts/publish_with_illustrations.py
```

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

### 3. 只先生成计划 / slots / prompts

```bash
python3 scripts/publish_with_illustrations.py \
  --article /path/to/article.md \
  --publisher-config ~/.openclaw/skills/wechat-draft-publisher/config/settings.json
```

## 输出

统一输出 JSON，便于上层继续接：
- `ok`
- `flow`
- `publish_result`
- `next_action`

## 说明

- 若你没有传 `--existing-generated-plan`，也没有加 `--generate`，脚本会默认走 dry-run，只产出计划 / slots / prompts。
- 若要真正 `--publish`，必须满足以下至少一项：
  - 提供 `--existing-generated-plan`
  - 或加 `--generate` 让它生成真正可发布的 merged plan

# wechat-publish-from-materials

这是第一次接入用户的默认入口，也是这个交付包里的主 skill。

## 第一次先选模式（避免卡在引导）

先选你这篇文章的配图方式：

1. **纯文字发布（最快）**
2. **你自己提供图片**
3. **AI 自动配图**
   - **MiniMax**（默认）
   - **Jimeng / 即梦**（提供 API key 后可切换）

> 建议第一次先走「纯文字发布」，先把主链跑通。

## 你只需要提供什么

1. `persona.md`
2. 一篇参考内容或一组材料
3. 公众号 `appid / secret`

## 它会帮你做什么

- 读取 persona + 材料
- 生成公众号正文
- （可选）插图规划 / 生图 / 回填
- 发布前检查
- 推送到公众号草稿箱

## 一句话入口

### 纯文字发布
> 请按我的 persona，把这份材料整理成公众号文章，先不要配图，检查后推到草稿箱。

### 我自己提供图片
> 请按我的 persona，把这份材料整理成公众号文章；封面和正文配图我自己提供，你帮我一起处理后推到草稿箱。

### AI 自动配图（MiniMax）
> 请按我的 persona，把这份材料整理成公众号文章，并使用 MiniMax 为合适段落生成插图方案与 AI 配图，检查后推到草稿箱。

### AI 自动配图（Jimeng / 即梦）
> 请按我的 persona，把这份材料整理成公众号文章，并使用 Jimeng / 即梦为合适段落生成插图方案与 AI 配图；如果需要 Jimeng key，我会补给你。

## 可选：给文章配插图

如果你希望文章不是只发纯正文，而是给段落配合适插图，可以多走一层。

> 标题建议用标准 Markdown 二级标题 `## 标题`。
> 现在也兼容把单独一行 `**加粗文本**` 当作章节标题做图位规划，但推荐优先用 `##` 以保证稳定。


```bash
python3 scripts/build_illustration_plan.py \
  --article /path/to/article.md \
  --output /tmp/illustration-plan.json

python3 scripts/build_illustration_slots.py \
  --article /path/to/article.md \
  --slots-output /tmp/illustration-slots.json \
  --prompts-output /tmp/illustration-prompts.md

python3 scripts/generate_article_illustrations.py \
  --plan /tmp/illustration-plan.json \
  --output-dir /tmp/article-images \
  --dry-run

python3 scripts/merge_illustrations_into_article.py \
  --article /path/to/article.md \
  --illustration-plan /tmp/article-images/illustration-plan.generated.json \
  --output /tmp/article.merged.md \
  --prepend-title
```

有真实生图条件时，再去掉 `--dry-run`。

如果想切换生图 provider：

```bash
# 默认 MiniMax（不填 provider 也会走 minimax）
python3 scripts/generate_article_illustrations.py \
  --plan /tmp/illustration-plan.json \
  --output-dir /tmp/article-images \
  --provider minimax \
  --minimax-api-key "$MINIMAX_API_KEY"

# 切到即梦 / Seedream 兼容链
python3 scripts/generate_article_illustrations.py \
  --plan /tmp/illustration-plan.json \
  --output-dir /tmp/article-images \
  --provider jimeng \
  --jimeng-api-key "$JIMENG_API_KEY"
```

参数规则：
- 不填 provider 时默认 `minimax`
- `--minimax-api-key` / `--jimeng-api-key` 优先级高于通用 `--api-key`
- 参数别名兼容：
  - `--provider` 等价 `--image-provider`
  - `--api-key` 等价 `--image-api-key`
  - `--base-url` 等价 `--image-base-url`
  - `--model` 等价 `--image-model`

如有需要，也可以继续覆盖：
- `--base-url`（或 `--image-base-url`）
- `--model`（或 `--image-model`）

如果要用“用户上传图片”替代/补充生图，可在统一流程里加：

```bash
python3 scripts/run_illustrated_publish_flow.py \
  --article /path/to/article.md \
  --generate \
  --provider minimax \
  --minimax-api-key "$MINIMAX_API_KEY" \
  --custom-images /tmp/custom-images.json \
  --custom-image-mode assist \
  --image-analysis-file /tmp/custom-images.analysis.json
```

其中 `/tmp/custom-images.json` 示例：

```json
{
  "custom_images": [
    {
      "image_id": "img_cover",
      "image_path": "/tmp/openclaw/uploads/cover.jpg",
      "slot_id": "cover_01",
      "mode": "manual",
      "note": "封面图"
    },
    {
      "image_id": "img_cmp",
      "image_path": "/tmp/openclaw/uploads/compare.png",
      "note": "上下文差异对照图",
      "mode": "assist",
      "auto_match": true
    }
  ]
}
```

`--image-analysis-file` 是可选增强层：
- 你有 MiniMax 识图机制时，先产出图片理解 JSON，再喂给绑定器
- 没有识图机制时，也可以只靠 `slot_id/heading/note` 先跑起来

也可以直接使用内置识图脚本先产出分析结果：

```bash
python3 scripts/analyze_uploaded_images.py \
  --custom-images /tmp/custom-images.json \
  --output /tmp/custom-images.analysis.json
```

或者在统一流程里自动触发识图：

```bash
python3 scripts/run_illustrated_publish_flow.py \
  --article /path/to/article.md \
  --custom-images /tmp/custom-images.json \
  --analyze-custom-images \
  --image-understanding-provider minimax \
  --image-understanding-model MiniMax-VL-01
```

说明：
- 这一步现在会真实调用 MiniMax 识图，再把结果喂给绑定器
- 识图和生图是两层能力，参数彼此分离
- 如果识图结果不足以高置信命中图位，系统会保留 `recommendations / unmatched`，而不是强行乱插

生成后的 `illustration-plan.generated.json` 或 `illustration-plan.bound.json` 既可以直接交给 publisher，也可以先回填成一份新的 Markdown 再交给 publisher：

```bash
python3 ../wechat-draft-publisher/scripts/publish_markdown.py \
  --file /path/to/article.md \
  --illustration-plan /tmp/article-images/illustration-plan.generated.json \
  --check

# 或者发布回填后的稿件
python3 ../wechat-draft-publisher/scripts/publish_markdown.py \
  --file /tmp/article.merged.md \
  --cover-image /path/to/cover.png \
  --check

# 如果想一条命令串起来
python3 scripts/run_illustrated_publish_flow.py \
  --article /path/to/article.md \
  --existing-generated-plan /tmp/article-images/illustration-plan.generated.json \
  --publisher-check \
  --publisher-config ../wechat-draft-publisher/config/settings.json
```


## 插图层说明

如果你不只是想“把文发出去”，还想让文章带上更合适的专属插图，当前版本会先帮你做：
- 图位规划
- 每张图的用途定义
- prompt 包整理
- 生图完成后把插图回填进正文 Markdown

也就是先把“该配什么图、为什么配、提示词怎么写”定下来。
后续你可以继续接生图、回填、再推进草稿箱。

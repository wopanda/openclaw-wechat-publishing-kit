# wechat-publish-from-materials

这是第一次接入用户的默认入口，也是这个交付包里的主 skill。

## 你只需要提供什么

1. `persona.md`
2. 一篇参考内容或一组材料
3. 公众号 `appid / secret`
4. 如果想改观感：`style_theme` / `accent_color`

## 它会帮你做什么

- 读取你的 persona
- 吸收参考内容
- 生成一篇适合你口吻的公众号正文
- 可选生成文章插图规划、图位与 prompt 包
- 可选调用 MiniMax 官方生图桥生成插图
- 可选把已生成插图回填进正文 Markdown
- 做发布前检查
- 推送到公众号草稿箱

## 一句话怎么用

> 请读取我的 persona 和这篇参考内容，整理成公众号稿，并推送到公众号草稿箱。


## 可选：给文章配插图

如果你希望文章不是只发纯正文，而是给段落配合适插图，可以多走一层：

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
生成后的 `illustration-plan.generated.json` 既可以直接交给 publisher，也可以先回填成一份新的 Markdown 再交给 publisher：

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

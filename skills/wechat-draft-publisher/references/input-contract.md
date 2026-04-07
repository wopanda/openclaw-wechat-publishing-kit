# 输入契约（Input Contract）

## 支持的输入方式

### 1. 文件路径

优先使用本地 Markdown 文件路径：

- `.md`
- Obsidian 笔记路径
- 绝对路径或相对路径

### 2. 内联内容

如果用户直接提供正文内容，也可以通过 `--content` 传入。

---

## 标题提取规则

按以下优先级提取标题：

1. 用户显式传入 `--title`
2. 清洗正文后的第一行 `# 一级标题`
3. 清洗正文后的第一行非空文本截断到 64 字
4. 最终回退：`无标题`

---

## 作者规则

按以下优先级确定作者：

1. 用户显式传入 `--author`
2. 元信息区块中的 `- 作者: xxx`
3. 配置项 `default_author`
4. 最终回退：`日新`

---

## 封面规则

按以下优先级确定最终封面：

1. 用户显式传入 `--thumb-media-id`
2. 用户显式传入 `--cover-image`
3. 插图计划中的封面图
4. 配置项 `default_thumb_media_id`
5. 配置项 `default_cover_image_path`
6. 正文中第一张本地可访问图片（自动取首图）

如果以上都没有，微信大概率会因缺少有效封面而拒绝发布。

说明：
- `default_thumb_media_id` 适合已经上传到微信素材库的固定封面
- `default_cover_image_path` 适合用户自己在本地保留一张兜底封面图，但不想把模板写死成所有人共用同一张图

---

## 正文图片规则

当前版本支持三种正文插图路径：

1. 在 Markdown 里直接写图片（原有路径）
2. 在发布参数里显式新增插图（新增路径）
   - `--body-image` / `--illustration`（可重复）
   - `--body-image-placement` / `--illustration-placement`
     - 推荐：`after-intro` / `before-ending`
     - 兼容旧值：`after-first-h2` / `before-signature`
   - `--max-body-images <N>`
   - `--strict-illustration`（需要“有图才发”时启用）
3. 通过 `--illustration-plan` 让 publisher 在发布前自动把结构化插图计划合并进正文

当前版本会尝试上传正文中的本地图片，并替换为微信可访问 URL。已实测支持：

- 普通 Markdown 图片：`![alt](path/to/image.jpg)`
- Obsidian 图片：`![[path/to/image.jpg]]`

说明：
- 飞书导出的 `<image url="..." />` 会先转换为发布链可识别的 `<img src="..." />`
- 默认会尝试下载并上传公网/飞书远程图片到微信素材库；下载/上传失败时会回退保留原远程 URL，并在结果中的 `image_report.failed_uploads` / `passthrough_remote_sources` 体现
- 本地图片路径解析失败时，会在结果中的 `image_report.unresolved_sources` 体现
- 发布前可先用 `--check-images` 查看图片分类、解析结果和未解析项

---

## 配图状态回报（新增）

`publish_markdown.py` 会回报 `image_state`，约定值：
- `article-specific`
- `fallback-approved`
- `text-only`
- `blocked-by-image`

你也可以显式传入：
- `--image-state` / `--illustration-state` = `article-specific|fallback-approved|text-only|blocked-by-image`

约束：
- 当状态为 `blocked-by-image` 时，脚本会停止并返回错误，不继续推草稿箱。
- 当状态为 `fallback-approved` 时，前台应明确告知“本轮使用兜底图，不是本文专属生图”。

默认图片数量上限（来自现有公众号工作流抽取）：
- 1 张封面图
- 0~1 张正文图

---

## 推荐使用姿势

### 最稳发布方式

- 先 `--check`
- 再正式发布
- 尽量显式提供 `--cover-image`

### 最稳插图方式

- 先跑：
  `python3 scripts/publish_markdown.py --check --file /path/to/article.md --body-image /path/to/body.jpg --image-state article-specific`
- 看清当前 `image_state`、`inserted_body_images`、`image_analysis`
- 再决定是否正式发布

### 自动首图封面适用场景

- 文章正文里已经有本地图片
- 不想额外单独准备封面

---

## 当前版本的边界

1. 不负责自动生成正文
2. 不负责自动起标题
3. 核心发布器 `publish_markdown.py` 仍然不是写作器
4. 插图能力只做“插入已有图片 + 状态显式化”，不负责自动生图
5. 默认目标是“草稿箱”，不是正式发布


## 插图计划（新增）

如果上游已经生成了结构化插图计划，可通过：

- `--illustration-plan /path/to/illustration-plan.generated.json`

让发布链在发布前自动把多张正文插图合并进文章正文。

要求：
- JSON 中必须有 `slots` 数组
- 正文插图应带 `local_path` / `image_path` / `image_url` 之一
- 封面图可通过 `cover_01` 的本地路径自动作为封面候选
- publisher 只负责“合并与上传”，不负责判断该不该生图、也不负责自动写 prompt

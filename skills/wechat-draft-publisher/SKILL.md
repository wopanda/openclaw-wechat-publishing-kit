---
name: wechat-draft-publisher
description: 把已经写好的 Markdown、Obsidian 笔记、飞书预览稿或草稿池记录，推进到微信公众号草稿箱的发布 Skill。适用于：公众号发布前的格式整理、图片处理、封面策略、预检、草稿箱投递、飞书预览稿转发布稿。不要用于：选题、搜集资料、生成正文、起标题、自动配图。特别适合第 5.2 这类“发布链 / 排版 / 草稿箱”场景。
---

# WeChat Draft Publisher

只做发布侧，不做内容生成侧。

## 执行原则

- 先把输入视为“已成型内容”，不要把本 Skill 当成写作器。
- 先跑预检，再正式发布。
- 优先保留成功 / 失败的结构化结果，便于上层流程回写状态。
- 允许把“去 AI 味 / 润色 / 审稿”作为发布前上游步骤，但不要把它们并入本 Skill 的核心边界。
- 发布阶段默认要补齐“作者字段 + 作者人格表达”两层：后台 `author` 与正文里的作者介绍不是一回事。

## 推荐输入形态

优先级从稳到弱：

1. 已确认的本地 Markdown 文件
2. Obsidian 笔记导出的 Markdown
3. 飞书预览文档导出的 Markdown
4. 草稿池标准化记录 JSON + 预览文档 Markdown

## 核心链路

### 1. 现成 Markdown → 草稿箱

- 需要最少信息时，直接调用 `scripts/publish_markdown.py`
- 如有独立封面，显式传 `--cover-image`
- 如需先检查，先加 `--check`
- 如需先做去 AI 味 / 润色，再用 `scripts/polish_and_publish.py`

### 2. 飞书预览稿 → 发布稿 → 草稿箱

- 先用 `scripts/prepare_feishu_doc_for_wechat.py` 去掉 callout、状态区、元信息前缀
- 再用 `scripts/publish_markdown.py` 发布

### 3. 草稿池记录 → 发布稿 → 草稿箱

- 用 `scripts/feishu_record_to_draft.py` 读取标准化记录 JSON + 预览文档 Markdown
- 该脚本会先生成可发布稿，再给出或直接执行发布命令

## 必读参考

- 输入与封面策略：`references/input-contract.md`
- 故障排查：`references/troubleshooting.md`
- 与 5.1 的边界、与“去 AI 味”模块的连接方式：`references/integration-boundary.md`
- 去 AI 味模块的标准接法：`references/polish-integration.md`
- 去 AI 味规则包：`references/polish-rules.md`

## 发布前最小检查顺序

1. 运行 `scripts/check_wechat_connection.py` 检查 AppID / AppSecret / 网络连通性
2. 运行 `scripts/publish_markdown.py --check ...`
3. 看 `cover_strategy`、`body_image_count`、`next_action`
4. 在上层前台显式说明：
   - 当前模式：快速草稿模式 / 正式成品模式
   - 当前配图状态：article-specific / fallback-approved / text-only / blocked-by-image
   - 若为兜底图，必须直接说明“本轮使用兜底图，不是本文专属生图”
5. 确认后再正式发布

## 输出要求

回复或上层系统至少保留这些字段：

- `ok`
- `title`
- `author`
- `cover_strategy`
- `media_id` / `draft_id`
- `image_report`
- `next_action`（如失败）

## 禁止混写

- 不把“搜集资料、生成正文、标题候选、自动配图”写进本 Skill 的能力口径。
- 可以接润色模块，但润色模块属于发布前上游步骤，不属于 5.2 本体扩边。
- 不把“草稿箱”写成“正式群发”。
- 不把 5.1 的上游内容生产链，当成 5.2 的本体。

---
name: wechat-publish-from-materials
description: 当用户想把“个人资料 + 参考内容”整理成一篇适合自己口吻的公众号文章，并在检查后送进微信公众号草稿箱时使用。第一次接入时，只需要用户准备 3 样东西：persona 文件、参考内容、公众号 appid/secret。默认主链 5 步：读取资料 → 生成正文 → 可选插图与配图状态 → 发布前检查 → 推送草稿箱。这个交付版不再包含飞书预览和复杂 workflow。
---

# WeChat Publish From Materials

这是给第一次接入用户的**主入口 skill**。

## 用户只需要准备什么

### 1. persona 文件
至少包含：
- 你是谁
- 你主要写什么
- 你的表达风格
- 你的真实经历 / 判断
- 你的文末引导方式

### 2. 参考内容
可以是：
- 一篇参考文章
- 一组笔记
- 一份主题材料
- 一段你想展开的判断

### 3. 公众号配置
- `appid`
- `secret`

如果想改公众号样式，也可以一起改：
- `style_theme`
- `accent_color`

当前内置主题：
- `wechat-pro`（默认绿色系）
- `cyan-clean`
- `slate-blue`

## 这个 skill 会做什么

它默认只做最稳的 5 步：
1. 读取你的 persona 和参考内容
2. 整理出一篇适合你口吻的公众号正文
3. 可选生成插图规划 / prompt 包 / 已生图回填，而不是只补固定 0~1 张图
4. 做一次发布前检查
5. 推送到微信公众号草稿箱

## 用户怎么调用

一句话就够：

> 请读取我的 persona 和这篇参考内容，整理成公众号稿，并推送到公众号草稿箱。

或者：

> 请根据我的 persona，把这组材料整理成一篇适合发布到微信公众号的文章，然后送进草稿箱。

## 最常见的 3 种用法

### 1. 我有一篇参考文章
读 persona → 吸收参考内容 → 生成你的版本 → 推草稿箱

### 2. 我有一组材料 / 笔记
整理观点 → 生成正文 → 推草稿箱

### 3. 我已经有 Markdown
可以直接交给 `wechat-draft-publisher`


## 插图能力（可选上游）

如果用户明确要“给文章配合适的插图”，建议走这条可选链：

1. `build_illustration_plan.py` 先生成结构化插图计划
2. `build_illustration_slots.py` 产出图位 + prompt 包
3. `generate_article_illustrations.py` 再把计划送入生图桥（默认 MiniMax；也可切到即梦 / Seedream 兼容链，或先 dry-run 导出 slots）
4. `bind_custom_images.py`（新增）可把用户上传的图片绑定到指定 slot / heading，或做自动匹配推荐
5. `merge_illustrations_into_article.py` 可先回填为一份新的 Markdown（可选）
6. 或者把生成后的 `illustration-plan.generated.json`（或 `illustration-plan.bound.json`）直接交给 `wechat-draft-publisher --illustration-plan`
7. 如果想一条命令串起来，可直接跑 `run_illustrated_publish_flow.py`

这条能力的目标不是承诺“每篇自动专属配图必成功”，而是把插图从临场发挥，升级成可验证、可回填、可发布的结构化步骤。

### 生图 provider 说明

当前生图桥已经按 provider 做成可切换：
- 默认：`MiniMax`
- 可选：`即梦 / Seedream / Ark 兼容链`

也就是说：
- 用户**不填生图 API key** 时，默认走 MiniMax
- 用户**填了即梦对应 key + provider** 时，可以切到即梦链路
- 如果后续即梦的实际模型名 / base URL 有变化，也可以通过参数覆盖，而不用重写整条 skill

当前参数约定（两组写法都支持）：
- `--provider` / `--image-provider`：`minimax|jimeng|seedream|ark`
- `--api-key` / `--image-api-key`：通用 key
- `--minimax-api-key`：MiniMax 专用 key（优先于通用 key）
- `--jimeng-api-key`：即梦专用 key（优先于通用 key）
- `--base-url` / `--image-base-url`（可选）
- `--model` / `--image-model`（可选）

默认原则：
- 先保证“能切 provider”
- 再按不同 provider 调 prompt / 出图风格
- 不把 provider 选型写死在正文链路里

### 用户上传图片插图（新增）

新增了“用户自定义图片绑定”能力，支持 3 种模式：
- `manual`：用户显式指定 `slot_id` 或 `insert_after_heading`
- `assist`：系统做候选推荐（低分不强插）
- `auto`：系统自动匹配高置信 slot

核心脚本：`bind_custom_images.py`

输入可用字段（JSON）：
- `image_path` / `image_url`
- `slot_id`（可选）
- `insert_after_heading`（可选）
- `note`（可选，用于匹配）
- `mode`（`manual|assist|auto`）
- `auto_match`（可选，优先于 mode）

如果你已有 MiniMax 识图链路，可以把识图结果先产出成 JSON，再通过 `--analysis-file` 接入绑定脚本：
- `image_id`
- `image_path`
- `caption`
- `visual_type`
- `tags`
- `contains_text`

运行 `run_illustrated_publish_flow.py` 时，可直接开启这层能力：
- `--custom-images /path/to/custom-images.json`
- `--custom-image-mode assist|auto|manual`
- `--image-analysis-file /path/to/analysis.json`（可选）
- `--analyze-custom-images`（可选，自动调用 MiniMax 识图）
- `--image-understanding-provider minimax`
- `--image-understanding-model MiniMax-VL-01`（可覆盖）
- `--image-understanding-api-key`（可选）
- `--bind-min-score 0.18`
- `--allow-cover-auto`（可选）
- `--no-replace-existing-images`（可选）

也可以单独跑识图脚本先产出分析文件：
- `python3 scripts/analyze_uploaded_images.py --custom-images /path/to/custom-images.json --output /path/to/analysis.json`

这样做的目的是：
- 没有识图能力时，也能稳定“手动绑定插图”
- 有 MiniMax 识图时，再叠加自动推荐/自动匹配
- 生图 provider 与识图 provider 解耦，不互相绑死


## 插图能力边界

这里说的“插图”，不是简单识别正文里已有图片。

它要做的是：
- 判断文章哪些段落值得配图
- 为每张图定义图位角色
- 生成可复用的 prompt 包
- 让后续生图与回填有稳定契约

当前建议的图位类型包括：
- 封面图
- 对比图
- 结构图
- 流程图
- 证据图
- 案例场景图
- 收口图

默认原则：
- 不是先定“一篇几张图”，而是先定“哪些段落需要图位”
- 每张图都要服务一个表达任务
- prompt 先来自文章结构与段落任务，不来自随手堆风格词

如果当前只是要快速发文，也可以跳过插图层，直接进入发布前检查。

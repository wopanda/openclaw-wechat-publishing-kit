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
3. `generate_article_illustrations.py` 再把计划送入生图桥（或先 dry-run 导出 slots）
4. `merge_illustrations_into_article.py` 可先回填为一份新的 Markdown（可选）
5. 或者把生成后的 `illustration-plan.generated.json` 直接交给 `wechat-draft-publisher --illustration-plan`
6. 如果想一条命令串起来，可直接跑 `run_illustrated_publish_flow.py`

这条能力的目标不是承诺“每篇自动专属配图必成功”，而是把插图从临场发挥，升级成可验证、可回填、可发布的结构化步骤。


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

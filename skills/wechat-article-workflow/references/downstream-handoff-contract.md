# Downstream Handoff Contract

## 交给 material-to-graphic-report 之前
必须至少具备：
- 已确认的选题卡
- 已确认的观点方向
- 干净正文或至少稳定的正文骨架
- 真实经历已调用
- 已明确这次是：纯原型 / 半闭环 / 闭环生图

如果进入生图：
- 优先按 `material-to-graphic-report` 的图片位协议组织 `slot_id`
- 当前环境可优先接 `nano-banana-pro` 做真实生图
- 调用时显式使用图片模型：`gemini-3-pro-image-preview`
- 不要沿用环境里默认的 `gemini-3.1-pro-preview` 去做图片生成

## 交给 wechat-draft-publisher 之前
必须至少具备：
- 已确认的预览稿 / Markdown 正文
- 已过内容质量门
- 已明确是否需要封面图 / 正文图
- 已完成飞书预览稿到微信发布稿的清洗（如适用）

## 禁止
- 不要把选题阶段结果直接交给发布 skill
- 不要把工作流说明、图像提示词、交付备注混进正文再交给发布 skill

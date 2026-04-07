# Illustration Planning Contract

## 目标
把“给文章配合适插图”从一句模糊需求，变成稳定的中间层产物。

这里的重点不是立刻生图，而是先把：
- 哪些段落该配图
- 每张图承担什么表达任务
- 每张图的 prompt 依据是什么
- 后续如何进入生图 / 回填 / 发布

统一写清。

## 第一性原则

1. 插图不是装饰，是文章表达的一部分。
2. 不先定张数，先定图位（slot）。
3. 每张图只解决一个主问题，不一图多义。
4. prompt 先来自文章结构与段落任务，再来自风格要求。
5. 当前没有生图也没关系，先把图位与 prompt 包做出来。

## 章节识别约束（重要）

推荐使用标准 Markdown 标题（`## 标题`）。
当前也兼容把单独一行 `**加粗文本**` 识别为章节标题（容错兜底），但长期仍建议用 `##`，稳定性更高。

## 图位类型

默认从下面 7 类里选：
- 封面图
- 对比图
- 结构图
- 流程图
- 证据图
- 案例场景图
- 收口图

## 每个图位的最小字段

```json
{
  "slot_id": "sec2_compare_01",
  "section": "第二部分",
  "anchor": "核心论点之后",
  "visual_type": "对比图",
  "purpose": "展示旧流程与新流程的差异",
  "source_paragraph": "对应的正文段落或段落摘要",
  "scene_description": "左侧碎片化手工流程，右侧结构化 workflow",
  "prompt_basis": {
    "article_claim": "这段想成立的判断",
    "why_image_here": "为什么这段需要图",
    "hero_scene": "主画面是什么",
    "supporting_elements": ["1-3 个辅助元素"],
    "style_goal": "希望更像什么，不像什么"
  },
  "prompt": {
    "zh_brief": "中文设计说明",
    "main_zh": "中文主 prompt（默认优先）",
    "main_en": "英文 fallback prompt（可选）",
    "negative_en": "英文 negative prompt（可选）"
  },
  "aspect_ratio": "4:3",
  "style": "business-tech editorial infographic",
  "caption": "放在图下方的一句话说明",
  "image_state": "article-specific"
}
```

## prompt_basis 的来源

`prompt_basis` 不靠拍脑袋，默认来自：
1. 文章主张
2. 当前段落任务
3. 图位类型
4. 主画面收敛结果
5. 平台约束（公众号 / 飞书 / 图文报告）

## prompt 写法顺序

固定顺序：

**表达任务 > 主画面 > 画面关系 > 风格 > 构图 > 输出约束 > negative prompt**

而不是一上来堆：高级感、科技感、未来感。

## image_state 约定

当前图位状态只允许用这 4 种：
- `article-specific`：这张图是为本文专门规划 / 生成的
- `fallback-approved`：这张图是旧图 / 兜底图，但已明确接受
- `text-only`：当前这个位置决定不配图
- `blocked-by-image`：这段明显需要图，但当前卡在图

## 推荐产物

当一篇文章进入“可选插图层”时，推荐产出：

1. `article-with-illustration-plan.md`
   - 文章正文
   - 附图位摘要
2. `illustration-slots.json`
   - 所有图位的结构化定义
3. `illustration-prompts.md`
   - 给人看的 prompt 包

## 当前真实生图桥

默认真实生图桥现在走：
- `scripts/generate_with_minimax.py`
- 底层接口：MiniMax 官方文生图接口 `POST https://api.minimaxi.com/v1/image_generation`
- 默认模型：`image-01`

说明：
- 不再默认依赖火山方舟 Ark / Seedream
- 优先读取环境变量：`MINIMAX_API_KEY`
- 兼容读取：`ABAB_API_KEY`
- 若环境变量未提供，会回退读取 `~/.openclaw/openclaw.json` 中的 `models.providers.minimax.apiKey`
- `--dry-run` 时不会真正调生图 API

## 与发布链的边界

这里不负责：
- 保证每张图一定生成成功
- 自动把复杂工作流一步发完
- 替代 `wechat-draft-publisher`

这里负责：
- 让“文章插图”先有稳定 schema
- 让后续生图 / 回填 / 发布有共同语言

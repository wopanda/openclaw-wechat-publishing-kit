# Illustration Prompt Contract

当文章需要“合适的插图”时，不直接从空白开始生图，而是先组织成结构化插图计划。

## 核心原则

1. 先判断这张图在文章里承担什么表达任务，再写 prompt。
2. 张数不是先验约束；是否需要更多图片，取决于段落推进、抽象程度、对比需求、证据密度。
3. 一张图只解决一个主问题，不在一张图里塞五个意思。
4. Prompt 的依据不是“风格词堆砌”，而是：表达任务 > 主画面 > 画面关系 > 风格 > 构图 > 约束 > negative prompt。

## 单图最小结构

```json
{
  "slot_id": "sec2_compare_01",
  "title": "旧流程 vs 新流程",
  "insert_after_heading": "第二节标题",
  "purpose": "展示旧流程与新流程的差异",
  "visual_type": "对比图",
  "scene_description": "左边是手工链路，右边是系统先整理后人判断的新链路",
  "prompt_cn": "前后对比、手工流程 vs 系统流程、信息整理、判断提速、结构清晰",
  "prompt": {
    "main_zh": "围绕旧流程与新流程做左右对比，突出结构化处理后的判断提速，编辑型信息图风格",
    "main_en": "side-by-side comparison of a fragmented manual workflow and a structured AI-assisted workflow, clear contrast in effort and clarity, business-tech editorial infographic style, 4:3",
    "negative_en": "watermark, random text, blurry, messy composition, cluttered background, overdone sci-fi"
  },
  "negative_prompt": "不要水印，不要中英文文字，不要模糊，不要杂乱背景",
  "aspect_ratio": "4:3",
  "style": "结构对比图 / 信息图",
  "caption": "差别不在信息量，而在是否还要自己先跑那一轮重复动作"
}
```

## 推荐图位类型

- 封面图：建立主题
- 对比图：旧 vs 新 / 前 vs 后
- 结构图：解释组成关系
- 流程图：讲步骤链路
- 证据图：承接数据、截图、事实
- 案例场景图：把抽象内容具象化
- 收口图：结尾固化判断

## Prompt 设计 8 字段

1. subject
2. action
3. setting
4. supporting_elements
5. message
6. style
7. composition
8. output_constraints

## 输出格式建议

整篇文章的插图计划建议使用：

```json
{
  "article_title": "文章标题",
  "visual_density": "medium",
  "slot_strategy": "rhetorical-role-first-v4",
  "slots": [ ... ]
}
```

## V4 新增约束

1. `main_zh` 作为默认主 prompt；`main_en` 仅做 fallback，不再要求英文优先。
2. 图位不是按 section 顺序机械截断，而是先给每个候选图位打优先级，再按密度筛选。
3. 默认保留封面图；正文图按 `light / medium / heavy` 做优先级截断。
4. prompt 包里应显式展示：为什么这里需要图、主画面、辅助元素、风格目标、优先级。

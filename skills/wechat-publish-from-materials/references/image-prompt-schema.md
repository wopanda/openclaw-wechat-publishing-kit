# Image Prompt Schema

## 目标
说明“文章插图 prompt 应该怎么写，以及依据是什么”。

## 一句话原则
prompt 不是为了写得华丽，而是为了让模型稳定生成**服务正文推进**的图片。

## prompt 依据
每张图的 prompt 默认来自 5 层：
1. 文章主张
2. 当前段落在推进什么
3. 这张图的图位类型
4. 主画面是什么
5. 这张图不该长成什么样

## 标准字段

### 1. zh_brief
给人看的中文设计说明，至少回答：
- 这张图为什么存在
- 主画面是什么
- 辅助元素是什么
- 想传达什么判断

### 2. main_en
英文主 prompt，默认骨架：

```text
[subject], [action], [setting], [1-3 supporting elements], conveying [message], [visual style], [composition], [lighting/palette], [output constraints]
```

### 3. negative_en
英文 negative prompt，默认至少压：
- watermark
- random text
- blurry
- low resolution
- messy composition
- cluttered background
- unrelated people
- cheap commercial advertising style
- overdone sci-fi
- too many visual elements

## 推荐拆解字段

在真正写 `main_en` 前，先内部拆成：
- `subject`
- `action`
- `setting`
- `supporting_elements`
- `message`
- `style`
- `composition`
- `output_constraints`

## 示例

### 中文设计说明
- 图位类型：对比图
- 用途：展示旧流程 vs 新流程
- 主画面：左边是碎片化手工处理，右边是结构化 agent workflow
- 辅助元素：笔记卡片、发布草稿、流程箭头
- 判断：差别不在信息量，而在是否先被重组

### main_en
```text
side-by-side comparison of a fragmented manual content workflow and a structured AI-assisted publishing workflow, left side showing scattered notes, browser tabs, copy-paste steps and confusion, right side showing a clean orchestrated pipeline with organized content blocks, article draft, image slots and publishing flow, conveying transformation from chaos to structured execution, business-tech editorial infographic style, clear visual hierarchy, clean layout, restrained blue-gray palette, premium professional illustration, 4:3
```

### negative_en
```text
watermark, random text, garbled labels, blurry, low resolution, messy composition, crowded layout, unrelated characters, cheap advertising style, overdone sci-fi, neon cyberpunk, too many visual elements
```

## 中文直接进图
如果用户明确要求图片里直接带中文，再额外补：
- 正确简体中文
- 指定文字内容
- 指定层级与位置
- 在 negative 中压乱码 / 假字 / 锯齿

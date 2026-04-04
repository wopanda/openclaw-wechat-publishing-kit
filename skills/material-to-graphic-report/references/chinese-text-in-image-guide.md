# 中文直接进图指南

这个文件定义：当图文报告需要**直接由模型生成清晰、正常、可读的中文文字**时，应该如何组织需求、提示词和验收标准。

这不是默认降级方案，而是基于当前已验证路线整理出的正式规范。

## 目标

让模型直接在图片里生成：
- 正确简体中文
- 清晰无锯齿的中文标题 / 副标题 / 标签 / 图注
- 适合飞书图文报告的成品感

## 第一性原则

1. 中文在这里不是装饰，而是信息层的一部分。
2. 既然要直接进图，就必须把“文字内容”当作主设计约束，而不是附带说明。
3. 不要默认让模型自由发挥中文内容；应明确给出文字、位置、层级和风格要求。
4. 不是所有图都适合直接写中文。优先用于：封面图、对比图、结论图、标签较少的信息图。
5. 正文中超多字、复杂表格、密集说明，不应强行让模型全部写进图里。

## 哪些图适合直接写中文

### 适合
- 封面图
- 对比图
- 收口图
- 少量标签式结构图
- 结论卡片图

### 谨慎使用
- 流程非常复杂的图
- 有很多步骤说明的图
- 需要精确小字排版的图
- 类似 PPT 一页信息墙的图

原则：
**文字越短、层级越清楚，模型内直接出中文越稳。**

## 文字层级建议

默认只使用 3 层：

1. **主标题**
   - 6-18 字为宜
   - 必须是一句话主命题

2. **副标题 / 标签**
   - 4-16 字
   - 用来辅助解释主标题

3. **图注 / 短句**
   - 8-28 字
   - 用来收口或点明图意

不要在一张图里同时塞：
- 超长标题
- 多段正文
- 多个小字说明块

## 中文直接进图的 Prompt 规则

### 1. 显式告诉模型必须输出正确简体中文
必须写清：
- correct Simplified Chinese
- no fake Chinese
- no garbled text
- no distorted characters
- clean sans-serif Chinese typography
- sharp, legible, smooth edges

### 2. 显式给出文字内容
不要写：
- add a Chinese title

要写：
- Main title in Chinese: 把分散素材压成一份可读报告
- Subtitle in Chinese: 内容重组 × 视觉脚本 × 飞书装配

### 3. 显式给出文字层级
例如：
- title should be prominent and elegant
- subtitle should be smaller and supportive
- labels should be concise and readable

### 4. 显式给出版式要求
例如：
- reserved negative space for Chinese headline
- clean left-aligned title block
- clear top-bottom hierarchy
- avoid overcrowded text layout

### 5. negative prompt 里要单独压文字风险
建议默认加入：
- fake Chinese characters
- garbled text
- typo-like characters
- blurry text
- jagged text edges
- unreadable labels

## 推荐 Prompt 模板

### 模板 A：封面图

```text
Generate a premium Chinese business-tech cover image for a Feishu visual report.
Main visual: [主画面]
Style: [风格]
Layout: horizontal 16:9 cover, clean hierarchy, reserved negative space for Chinese title.

Chinese text requirements:
- The image must contain natural, correct, sharp Simplified Chinese text.
- Use clean sans-serif Chinese typography, high legibility, smooth edges, no jagged text, no distorted characters.
- Main title in Chinese: [主标题]
- Subtitle in Chinese: [副标题]
- Title should be prominent and elegant.
- Subtitle should be smaller and supportive.
- Do not generate garbled text, fake Chinese, typo-like characters, or random letters.
```

### 模板 B：对比图

```text
Generate a premium Chinese comparison infographic image for a Feishu visual report.
Main visual idea: [左旧右新 / 前后对比]
Style: business-tech editorial infographic, clean, premium, minimal clutter.
Layout: horizontal 4:3, clear left-right split, highly readable Chinese typography integrated naturally.

Chinese text requirements:
- Main title in Chinese: [对比标题]
- Left label in Chinese: [左侧标签]
- Right label in Chinese: [右侧标签]
- Optional bottom caption in Chinese: [底部图注]
- Use correct, clean, sharp Simplified Chinese.
- No fake Chinese, no garbled text, no distorted characters.
```

### 模板 C：收口图

```text
Generate a premium Chinese ending visual for a Feishu visual report.
Main visual: [结论画面]
Style: restrained editorial visual, calm and strong, premium finish.
Layout: [比例], enough space for one short Chinese conclusion line.

Chinese text requirements:
- Main conclusion in Chinese: [一句话结论]
- Text should be elegant, sharp, easy to read, and naturally integrated.
```

## 验收标准

中文直接进图后，至少检查：

1. 是否是**正确简体中文**，不是乱码或假字
2. 是否**边缘清晰**，没有明显锯齿感
3. 是否**层级明确**，能一眼看出标题 / 副标题 / 标签关系
4. 是否**像中文图文成品**，而不是英文海报硬换中文
5. 是否**没有过多小字**导致难读

## 失败判定

以下任一情况，都判为这张图不通过：
- 中文乱码
- 中文像伪字
- 字边发糊或严重锯齿
- 文字排布拥挤
- 文本很多但不可读
- 标题与画面主焦点互相打架

## 失败后的处理

### 轻微问题
例如：
- 文字略不够稳
- 个别字边略糊

处理：
- 继续同路线重生一版
- 收紧文字量
- 加强“sharp, legible, smooth edges”约束

### 严重问题
例如：
- 乱码明显
- 多行中文完全崩掉

处理：
- 缩减图片内文字层级
- 把长句改成短标题 + 短标签
- 必要时把复杂说明移回飞书正文，而不是强塞进图里

## 对我们当前链路的具体要求

在 `material-to-graphic-report` 中：
- 如果用户明确要求中文直接进图，就把这条能力视为主路线，不要默认降级到后期叠字。
- 但同时保持判断：**复杂信息图仍然要克制文字量。**
- 优先把中文直接进图用于：
  - `cover_01`
  - `sec2_compare_01`
  - `sec4_close_01`

## 一句话原则

**中文直接进图不是“顺便写几个字”，而是把文字当成图的一部分一起设计。文字越短、层级越清楚、主任务越单一，结果越稳。**

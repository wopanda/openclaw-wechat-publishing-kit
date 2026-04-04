# 生图提示词设计指南

这个文件吸收了我刚在 ClawHub 上看的几类 skill 思路，并改造成适合我们当前这条链的版本：
- 不是做通用海报比赛 prompt
- 不是做随机艺术图
- 而是服务 **中文图文报告 / 飞书图文稿 / 文章内容重组** 的视觉生成

参考来源主要包括：
- `grok-image-prompt-optimizer`：把需求拆成结构字段、收敛成一个主画面、补 negative prompt
- `image-prompt`：用风格 / 光线 / 构图 / 质量词做增强，但不搞随机化主导
- `nano-banana-skill`：提醒我们保留分辨率、比例、参考图、一致性等模型能力接口

## 第一性原则

1. Prompt 不是为了“描述得多”，而是为了让模型更稳定地产出正确画面。
2. 对图文报告来说，最重要的是 **表达任务清楚**，不是画风花哨。
3. 先有图片位，再有 Prompt；不能反过来。
4. 每张图只解决一个主问题，不要一张图塞五个意思。
5. 如果文档场景是飞书图文，默认优先：清晰、克制、可读、可留白。

## 我们的默认设计流程

### 第一步：先定义这张图要完成什么
先回答：
- 这张图是在建立主题？
- 讲清对比？
- 解释结构？
- 展示流程？
- 承接证据？
- 做结尾收口？

如果这一步说不清，先别写 prompt。

### 第二步：把需求拆成 8 个字段
借鉴 `grok-image-prompt-optimizer` 的拆法，但改成更适合图文报告的版本：

1. `subject`：主对象是什么
2. `action`：它在做什么
3. `setting`：画面发生在什么环境里
4. `supporting_elements`：1-3 个辅助元素
5. `message`：这张图要传达什么判断
6. `style`：要什么视觉风格
7. `composition`：画面怎么构图
8. `output_constraints`：比例、清晰度、留白、是否适合飞书等

### 第三步：收敛成一个主画面
如果需求里同时想讲：
- 流程
- 对比
- 结果
- 情绪
- 案例

那通常已经过载了。

默认做法：
- 选一个 **hero scene**（主画面）
- 其他东西降级成辅助元素或图注语义

### 第四步：再写 Prompt
Prompt 默认结构：

```text
[subject], [action], [setting], [1-3 supporting elements], [message], [visual style], [composition], [lighting / palette], [output constraints]
```

### 第五步：补 negative prompt
对图文报告默认补：
- 水印
- 杂乱小字
- 低清晰度
- 过度商业广告感
- 无关人物
- 过度赛博朋克
- 画面过满
- 错误图表或错误界面元素

## 适合我们这条链的 Prompt 结构

### 1. 封面图 Prompt
适用于：建立主题感

公式：

```text
[核心主题对象], [核心变化], [简洁环境], conveying [主题判断], clean business-tech illustration, premium editorial visual, strong focal point, negative space for title, [palette], [aspect ratio]
```

示例：

```text
scattered information streams converging into a highlighted report card, from chaos to clarity, minimal digital workspace background, conveying structured content recomposition, clean business-tech illustration, premium editorial visual, strong focal point, negative space for title, blue-white-gray palette, 16:9
```

### 2. 对比图 Prompt
适用于：旧流程 vs 新流程

公式：

```text
side-by-side comparison of [old state] and [new state], clear contrast in workflow and information clarity, structured infographic style, clean layout, strong visual hierarchy, minimal clutter, [aspect ratio]
```

示例：

```text
side-by-side comparison of manual information scanning workflow and system-organized briefing workflow, clear contrast in effort and clarity, structured infographic style, clean layout, strong visual hierarchy, minimal clutter, 4:3
```

### 3. 结构图 Prompt
适用于：解释组成关系

公式：

```text
[input] flowing into [processing structure] and producing [output], modular diagram feeling, clean information architecture, simplified labels feel without actual text rendering, minimal business infographic, [aspect ratio]
```

### 4. 流程图 Prompt
适用于：讲步骤链路

注意：
如果能用 Mermaid，优先用 Mermaid；
只有在需要更有视觉感的成品图时，才生图。

### 5. 证据图 Prompt
适用于：承接数据 / 截图 / 结论卡

公式：

```text
report-style evidence cards, key facts highlighted, clean data card layout, premium professional visual, minimal clutter, readable hierarchy, [aspect ratio]
```

### 6. 收口图 Prompt
适用于：结尾固化判断

公式：

```text
[main conclusion visualized], restrained editorial style, calm strong ending image, clean composition, symbolic but not abstract to the point of confusion, premium finish, [aspect ratio]
```

## 中文图文报告场景下的特殊规则

### 1. 默认不走“海报口号风”
除非用户明确要“宣传海报”，否则：
- 不要大字报感
- 不要比赛海报感
- 不要过度主旋律宣发感

### 2. 默认不走“电商广告风”
避免：
- 夸张商品展示
- 强烈销售气息
- 过亮配色
- 促销海报式构图

### 3. 默认更像“编辑型配图 / 商务信息图”
优先：
- 编辑感
- 信息感
- 商务科技感
- 卡片化
- 留白

### 4. 中文语义可先中文思考，最终 prompt 以英文为主
对大多数图像模型，最终可调用 prompt 默认建议：
- 中文：作为内部设计说明
- 英文：作为主 prompt
- negative prompt：英文

## 一张图的标准输出

当设计一张图时，默认输出：

1. **图片位判断**
   - slot_id
   - visual_type
   - purpose

2. **Prompt 设计说明（中文）**
   - 这张图为什么这样设计
   - 主画面是什么
   - 辅助元素是什么

3. **Main prompt（EN）**
4. **Negative prompt（EN）**
5. **可调旋钮**
   - 更官方
   - 更克制
   - 更有结构感
   - 更像信息图

## 可调旋钮（推荐保留）

### 更官方
加入：
- professional
- trustworthy
- orderly
- official communication visual
- restrained design

### 更有图文报告感
加入：
- editorial visual
- business infographic
- report-style visual
- clear focal hierarchy
- structured composition

### 更克制
加入：
- minimal clutter
- restrained palette
- clean background
- limited supporting elements

### 更像中国内容平台常见爆款配图
慎用，只在用户明确想要时加：
- strong contrast
- emotional visual hook
- bold poster framing

## 默认 negative prompt 起手式

```text
watermark, random text, logo errors, blurry, low resolution, messy composition, cluttered background, unrelated people, overdone sci-fi, cheap commercial advertising style, garish colors, too many visual elements, unreadable interface details
```

## 对我们当前需求的核心判断

我们这条链里，生图 prompt 最重要的不是“艺术性最大化”，而是：

**让图片稳定服务文章内容的结构表达。**

所以 prompt 设计顺序固定为：

**表达任务 > 主画面 > 画面关系 > 风格 > 构图 > 约束 > negative prompt**

而不是先想一句“好像很厉害的话”。

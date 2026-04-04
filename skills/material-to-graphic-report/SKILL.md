---
name: material-to-graphic-report
description: 把一份或多份现有素材，重组成可在飞书中阅读的图文报告原型：先提炼结构与证据，再压入用户观点，生成正文、结构化图片位、图片提示词和飞书装配稿。适用于把素材重组成图文稿、把多份材料融合成一篇新稿、按用户观点重写现有素材、制作飞书可发的视觉化报告、先用占位图后续再补生图。不适用于普通摘要、同义改写、纯文字随手稿、或默认自动发布。
---

# Material to Graphic Report

把已有素材重组成一份“可在飞书里点开阅读”的图文报告原型。
默认交付不是一段文字，而是一个完整中间态：**内容重组 + 视觉脚本 + 飞书装配 + 后续可补图闭环**。

## 核心原则

1. 先定义最终成品，再写正文。
2. 图不是装饰，每一张图都必须服务一个表达任务。
3. 先把图片位、提示词、图注和位置写死，再进入生图与替换。
4. 优先服务飞书阅读体验，而不是普通长文排版。
5. 不要在 skill 文件、reference 文件、示例文档、飞书预览稿或对用户回复中暴露真实 API Key。

## 参考文件导航

按需要读取，不要一上来全读。

### 做视觉脚本时读
- `references/visual-slot-types.md`：先判断这张图属于封面图、对比图、结构图、流程图、证据图、案例场景图还是收口图
- `references/image-slot-format.md`：结构化图片位格式

### 做飞书装配时读
- `references/feishu-visual-layout.md`：飞书图文版式骨架
- `references/feishu-delivery-strategy.md`：该回消息还是该建飞书文档，以及后续怎么补图替换

### 做生图与替换时读
- `references/image-generation-input-contract.md`：生图输入 / 返回契约
- `references/image-runtime-config.md`：运行配置参考（不含密钥）
- `references/image-prompt-design-guide.md`：Prompt 设计顺序与约束
- `references/chinese-text-in-image-guide.md`：用户明确要求中文直接进图时使用
- `references/image-replacement-protocol.md`：按 `slot_id` 推进替换闭环
- `references/nano-banana-integration.md`：当前环境默认接入的真实生图执行桥
- `references/slot-replacement-bridge.md`：真实图片回填到原型稿的最后一段桥接

### 做成品校准时读
- `references/output-template.md`：固定五层交付格式
- `references/example-feishu-visual-report.md`：最小真实案例
- `references/example-image-replacement.md`：替换前 → 替换后演示
- `references/end-to-end-execution-checklist.md`：整条链的阶段清单

## Workflow

1. **收集输入**
   - 收集一份或多份源素材。
   - 确认用户目标、受众、核心观点、交付场景、是否需要飞书落地。

2. **拆解素材**
   - 提取可复用的结构逻辑、证据、案例、强段落。
   - 区分哪些内容可借，哪些内容不应直接沿用。

3. **注入用户观点**
   - 明确用户真正想成立的判断、主命题和不可退让点。
   - 如果用户观点与源素材 framing 冲突，优先以用户观点为准。

4. **重组内容**
   - 重新生成主题、标题候选、提纲、段落顺序和论证路径。
   - 必要时融合多份素材，形成新的表达结构。

5. **设计视觉脚本**
   - 判断哪些段落需要图，哪些只需文字。
   - 先用 `visual-slot-types.md` 判定图位类型。
   - 再按 `image-slot-format.md` 输出结构化图片位：用途、位置、画面描述、提示词、比例、风格、图注。
   - 如果用户明确要求中文直接进图，再按 `chinese-text-in-image-guide.md` 把中文作为主设计约束。

6. **装配飞书稿**
   - 生成适合飞书打开阅读的 Markdown / 文档结构。
   - 插入结构化图片位，而不是只写“这里配图”。
   - 让封面、节奏、段落层级、图文切换都服务飞书阅读。

7. **交付与后续闭环**
   - 默认返回 Markdown。
   - 如用户要求，进一步创建飞书文档原型。
   - 无生图能力时，保留图片位占位。
   - 有生图能力时，按 `image-generation-input-contract.md` 组织请求。
   - 当前环境默认优先接 `nano-banana-pro` 执行真实生图，再按 `image-replacement-protocol.md` 逐位替换。

## Input Contract

### 必填输入
- **materials**：一份或多份源素材
- **goal**：这份输出拿来做什么

### 强烈建议提供
- **my_points**：用户自己的核心观点、判断或主命题
- **target_audience**：给谁看
- **mode**：`quick` / `deep`
- **output_style**：`feishu-visual-report` / `article-draft` / `book-material`
- **length**：`short` / `medium` / `long`
- **visual_density**：`light` / `medium` / `heavy`
- **image_mode**：`placeholder-now-generate-later` / `source-only` / `generate-if-available`
- **deliver_to_feishu**：`yes` / `no`

## Output Contract

结果优先按五层返回：

1. **素材拆解**
   - 这份素材为什么可用
   - 可借结构
   - 可借证据 / 案例
   - 不应直接沿用的部分

2. **重组方案**
   - 新角度
   - 新标题候选
   - 新提纲
   - 新论证顺序

3. **视觉脚本**
   - 全文需要几张图
   - 每张图服务什么作用
   - 每张图对应的结构化图片位

4. **飞书图文稿**
   - Markdown 草稿
   - 已插入结构化图片位
   - 已具备飞书阅读节奏

5. **交付层**
   - Markdown ready
   - Feishu doc prototype created（可选）
   - image slots pending generation / replacement
   - later replacement plan

## Guardrails

1. 不要把任务降级成普通摘要。
2. 不要把自己当成同义改写器或表面润色器。
3. 始终优先用户观点，而不是源素材原本的 framing。
4. 多份素材冲突时，先显式指出冲突，再决定是否融合。
5. 优先做结构级重组，而不是词句级替换。
6. 不要把图片当装饰；每张图都必须承担封面、解释、对比、证据、转折或收口中的一种作用。
7. 不要只写“这里配图”；必须输出结构化图片位。
8. 当前没有生图能力时，不要假装图片已经存在；应明确标注为占位待生成。
9. 如果用户明确要求中文直接进图，不要默认降级到后期叠字；先按中文直接进图路线设计和验证。
10. 不要默认公开发布、自动发文或自动投稿。
11. 明确说明借用了什么：结构、证据、角度，还是案例。
12. 如果素材不足以支撑图文重组，先指出缺口，不要硬写。

## Interaction Rules

- 如果输入已经清楚，先给一版简短重组方案，再出草稿。
- 如果用户明确要求快，可先内部拆解，再直接出图文稿。
- 如果用户观点不清楚，先追问观点，再做深度重组。
- 如果素材质量太弱、太散、太同质，要先提醒用户。
- 如果目标是飞书图文报告，默认把“飞书可阅读的成品感”当成输出要求的一部分，而不是附属项。
- 如果用户要求“逐步进行”，按阶段推进；默认内部验证，不必把每张测试图都发给用户拍板，除非用户明确要求看中间图。

# 生图输入契约

当 `material-to-graphic-report` 进入“可补生图”阶段时，生图输入必须按本契约组织，避免图片生成结果与文档坑位脱节。

## 目标

确保每一张图都不是孤立生成，而是：
- 有明确 `slot_id`
- 有明确表达任务
- 有明确返回格式
- 生成后可直接进入替换协议

## 第一性原则

1. 生图不是“顺手画几张图”，而是为已有视觉位补齐正式图片。
2. 生图输入必须围绕 `slot_id` 组织，而不是围绕“第几张图”组织。
3. 生成结果必须可回填到飞书文档，不接受只有图片、没有映射关系的结果。
4. 如果某张图的表达任务没定义清楚，先补图片位，不要急着生成。

## 单张图的最小输入字段

每个图片位最少应提供：

```json
{
  "slot_id": "sec2_compare_01",
  "title": "旧流程 vs 新流程",
  "purpose": "展示旧流程与新流程的差异",
  "position": "第二节核心论点之后",
  "visual_type": "对比图",
  "scene_description": "左边是手工链路，右边是系统先整理后人判断的新链路",
  "prompt": "前后对比、手工流程 vs 系统流程、信息整理、判断提速、结构清晰、4:3",
  "aspect_ratio": "4:3",
  "style": "结构对比图 / 信息图",
  "caption": "差别不在信息量，而在是否还要自己先跑那一轮重复动作"
}
```

## 推荐扩展字段

如果生图模型支持，建议补：

```json
{
  "negative_prompt": "杂乱文字、水印、低清晰度、无关人物、错误图表",
  "color_palette": "蓝灰 + 白色 + 轻科技感",
  "quality": "standard",
  "count": 1,
  "seed": null,
  "source_mode": "generate-if-available"
}
```

## 多图输入格式

如果一篇文档有多张图，统一使用数组：

```json
{
  "doc_id": "IpWHd1juyok9cDx0sKjci3kwnRg",
  "output_style": "feishu-visual-report",
  "image_mode": "placeholder-now-generate-later",
  "slots": [
    {
      "slot_id": "cover_01",
      "title": "封面头图",
      "purpose": "建立主题感",
      "visual_type": "封面图",
      "scene_description": "分散信息流汇聚成一份被高亮的报告",
      "prompt": "科技感、信息汇聚、报告高亮、简洁高级、16:9",
      "aspect_ratio": "16:9",
      "style": "商务科技感 / 简洁高级",
      "caption": "把分散素材压成一份可读报告"
    },
    {
      "slot_id": "sec2_compare_01",
      "title": "旧流程 vs 新流程",
      "purpose": "展示旧结构与新结构的差异",
      "visual_type": "对比图",
      "scene_description": "左侧碎片化内容，右侧清晰模块化图文结构",
      "prompt": "前后对比、信息重组、模块化、结构优化、简洁信息图风格、4:3",
      "aspect_ratio": "4:3",
      "style": "结构对比图 / 信息图",
      "caption": "不是换词，而是重组表达结构"
    }
  ]
}
```

## 生成结果的返回契约

生成器返回时，不要只返回 URL 列表。
必须保留 `slot_id`，推荐格式：

```json
{
  "results": [
    {
      "slot_id": "cover_01",
      "status": "generated",
      "image_url": "https://example.com/cover_01.png",
      "local_path": null,
      "width": 1600,
      "height": 900
    },
    {
      "slot_id": "sec2_compare_01",
      "status": "generated",
      "image_url": "https://example.com/sec2_compare_01.png",
      "local_path": null,
      "width": 1200,
      "height": 900
    }
  ]
}
```

## 三种来源模式

### 1. `generate-if-available`
- 有生图模型或 API 时生成
- 结果返回 URL / 本地路径 + `slot_id`

### 2. `source-only`
- 不生成新图
- 只使用用户已有图片
- 也必须绑定 `slot_id`

### 3. `placeholder-now-generate-later`
- 当前只整理生图输入
- 暂不真正生成
- 输出重点是未来可调用的 `slots` 数组

## 失败处理

如果某张图生成失败，返回：

```json
{
  "slot_id": "sec3_structure_01",
  "status": "failed",
  "reason": "prompt too vague"
}
```

不要吞掉失败，也不要默默跳过某个 `slot_id`。

## 与替换协议的衔接

拿到生成结果后：
1. 按 `slot_id` 找到对应图片位
2. 进入 `references/image-replacement-protocol.md`
3. 将该图位从 `待生成` 推进到 `已生成待替换` 再到 `已替换`

## 输出检查清单

在调用生图或整理生图输入前，至少检查：
1. 每个 `slot_id` 是否唯一
2. 每张图的 `purpose` 是否清楚
3. `visual_type` 是否已经判定
4. `prompt` 是否足以支持生成
5. 返回结果是否保留了 `slot_id`

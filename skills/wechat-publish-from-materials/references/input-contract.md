# Input Contract

## 最小输入
- `persona_file`
- `references`

## 推荐补充
- `topic`
- `publish_intent`
- `target_audience`
- `need_feishu_preview`
- `style_override`
- `need_illustrations`
- `illustration_density`（light / medium / heavy）
- `image_style_hint`
- `allow_chinese_text_in_image`

## persona_file 最少应包含
1. 身份定位
2. 真实经历
3. 失败教训
4. 表达偏好
5. 行动召唤 / CTA（如有）

## references 可接受形态
- 文章正文
- Markdown 笔记
- 多条材料摘录
- 飞书文档导出内容

## 注意
- 参考内容默认只借结构与论证线索
- 不默认接受“直接仿写某作者风格”


## need_illustrations 为 yes 时
- 先生成结构化插图计划，不直接从空白 prompt 临场发挥
- 图片数量由文章结构决定，不预设固定 0~1 张
- 每张图都应绑定一个明确图位与表达任务
- 可选继续走：`build_illustration_slots.py` → `generate_article_illustrations.py` → `merge_illustrations_into_article.py` / `publish_markdown.py --illustration-plan`
- 如果想一条命令串起来，可直接跑 `scripts/run_illustrated_publish_flow.py`
- 参考 `references/illustration-prompt-contract.md`

### 结构化标题建议
- 最稳方式：使用标准 Markdown 二级标题 `## 标题`
- 当前也兼容把单独一行 `**加粗文本**` 识别为章节标题
- 但如果要稳定生成图位、稳定插回正文，仍建议优先用 `## 标题`

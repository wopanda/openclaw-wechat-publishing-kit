# Publish Handoff Contract

交给 `wechat-draft-publisher` 的输入应是：
- 干净 Markdown 正文
- 可选封面图路径
- 可选作者名
- 可选已回填完成的正文插图（此时图片已在正文中，不再附带图位说明）
- 可选插图计划（已带生成结果）

## 不应带入的内容
- persona-summary
- reference-extract
- article-brief
- draft-handoff 说明文字
- 飞书图位占位说明

## 默认发布顺序
1. 连接检查
2. `--check` 预检
3. 查看 cover_strategy / next_action
4. 再正式推草稿箱


如果有多张正文插图，不要直接把“图位说明”塞进正文；应优先生成 `illustration-plan.generated.json`，再由 publisher 合并。

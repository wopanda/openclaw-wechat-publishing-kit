# Publish Handoff Contract

交给 `wechat-draft-publisher` 的输入应是：
- 干净 Markdown 正文
- 可选封面图路径
- 可选作者名

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

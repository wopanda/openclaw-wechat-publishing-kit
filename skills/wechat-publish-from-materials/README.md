# wechat-publish-from-materials

面向用户的主入口 skill。

它适合这种场景：

> 我给你一个人的 persona 文件，再给你一篇参考内容或一批材料，你帮我整理成适合这个人口吻的公众号正文，检查后推进到公众号草稿箱。

## 它解决什么问题

把原本分散的几步收口成一个稳定主入口：
- 读取个人信息文件
- 吸收参考内容
- 形成文章 brief
- 生成干净正文
- 按需进入飞书预览
- 最后交给发布器推草稿箱

## 最稳的使用方式

### 输入
- 一个 `persona.md` 或等价个人信息文件
- 一份或多份参考内容
- 可选主题 / 发布意图

### 输出
- `persona-summary`
- `reference-extract`
- `article-brief`
- `draft-handoff`
- 干净正文 Markdown

## 默认边界

### 能做
- 根据 persona 收口写作边界
- 参考外部内容，但不照搬口吻
- 对接现有发布链，推进到草稿箱

### 不承诺
- 自动正式群发
- 自动稳定专属生图
- 自动事实核验
- 自动全网找题

## 下游依赖
- `wechat-article-workflow`：内容前链
- `material-to-graphic-report`：飞书预览（可选）
- `wechat-draft-publisher`：草稿箱发布

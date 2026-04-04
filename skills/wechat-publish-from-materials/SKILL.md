---
name: wechat-publish-from-materials
description: 当用户想把“个人信息文件 + 参考内容 + 可选主题/发布意图”推进成微信公众号可发布正文，并在检查后送入公众号草稿箱时使用。这个 skill 是统一主入口：先提炼 persona 约束，再吸收参考内容，生成干净正文，按需走飞书预览，最后交给 wechat-draft-publisher 做预检与草稿箱投递。它不承诺自动正式群发，不承诺稳定自动专属生图，也不负责替用户完成事实核验与合规审核。
---

# WeChat Publish From Materials

这是一个**主入口 skill**。

它负责把用户给的：
- 个人信息文件
- 参考文章 / 笔记 / 材料
- 可选主题 / 发布意图

收口成一条稳定主链：

```text
persona + references + optional topic
    ↓
提炼人设约束
    ↓
抽取参考结构与论证线索
    ↓
生成干净正文
    ↓
(可选) 飞书图文预览
    ↓
发布前预检
    ↓
微信公众号草稿箱
```

## 它负责什么

1. 读取个人信息文件，提炼：
   - 身份定位
   - 真实经历
   - 失败教训
   - 表达偏好
   - 不可偏离主张
2. 吸收参考内容，只借：
   - 结构
   - 信息
   - 论证顺序
   - 问题 framing
3. 组织出一份适合公众号发布的干净 Markdown 正文
4. 如用户明确需要，再交给 `material-to-graphic-report` 生成飞书图文预览原型
5. 最后交给 `wechat-draft-publisher` 做：
   - 预检
   - 清洗
   - 草稿箱投递

## 它不负责什么

- 不承诺自动找题 / 自动抓全网资料
- 不承诺自动生成稳定可用的专属配图
- 不承诺直接正式群发
- 不替用户完成事实核验、观点正确性与合规审核
- 不把参考内容直接写成仿写内容

## 默认输入

### 必填
- `persona_file`：个人信息文件
- `references`：参考内容（1 份或多份）

### 可选
- `topic`：本次主题
- `publish_intent`：为什么要发
- `need_feishu_preview`：是否需要飞书图文预览
- `style_override`：本次临时风格要求

## 默认输出

至少保留 4 类中间产物：
1. `persona-summary`
2. `reference-extract`
3. `article-brief`
4. `draft-handoff`

最终对发布链只交付：
- **干净正文 Markdown**

## 必读参考

- `references/product-boundary.md`
- `references/input-contract.md`
- `references/persona-loading-contract.md`
- `references/draft-output-contract.md`
- `references/publish-handoff-contract.md`

## 模板

- `templates/persona-summary.md`
- `templates/reference-extract.md`
- `templates/article-brief.md`
- `templates/draft-handoff.md`

## 执行规则

1. **先抽 persona，再读参考内容**
   - 不要让参考内容压过用户自己的人设。

2. **参考内容只借结构，不借人格**
   - 不直接复刻外部作者口吻。

3. **工作流文件与发布正文分开**
   - brief / extract / handoff 不可混进最终正文。

4. **飞书预览是可选分支，不是硬门槛**
   - 用户没要求时，可以直接走正文 → 预检 → 草稿箱。

5. **首版优先成功率，不追求全自动闭环炫技**
   - 能 text-only 就别强绑专属生图。

## 与其他 skill 的边界

### `wechat-article-workflow`
负责内容前链调度，不负责真正草稿箱投递。

### `material-to-graphic-report`
负责飞书图文预览 / 视觉原型，只在用户明确需要时调用。

### `wechat-draft-publisher`
负责发布前清洗、预检、草稿箱投递，不负责写正文。

## 最稳的对外口径

> 给我你的个人信息文件和参考内容，我会先收口你的表达边界，再整理出一版适合你口吻的公众号正文；如有需要再做飞书预览，最后检查后推到公众号草稿箱。

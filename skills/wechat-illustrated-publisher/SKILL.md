---
name: wechat-illustrated-publisher
description: 把“文章 + 插图规划/生图结果 + 微信公众号发布”收成一个统一入口的 Skill。适用于：已经有 Markdown 文章，想自动完成插图计划、prompt 包、可选生图衔接、发布前检查，并最终送进微信公众号草稿箱。它是一个组合 Skill，会调用 `wechat-publish-from-materials` 与 `wechat-draft-publisher` 的现有能力。不要用于：从零写正文、资料搜集、选题讨论、完全脱离公众号发布场景的生图实验。
---

# WeChat Illustrated Publisher

这是一个**新的组合型 skill**。

它不替代底层两个 skill：
- `wechat-publish-from-materials`
- `wechat-draft-publisher`

而是把它们之间原本分开的插图链 + 发布链，收成一个统一入口。

## 它解决什么问题

以前如果你要做“带插图的公众号发布”，通常要自己串这些步骤：
1. 生成插图计划
2. 生成 slots / prompts
3. dry-run 或真实生图
4. 把 generated plan 交给 publisher
5. publisher 再做 `--check` 或正式发布

这个 skill 做的事情，就是把这条链变成一个更像单独产品入口的能力。

## 典型场景

### 1. 你已经有 Markdown 文章
直接用这个 skill 跑：
- 插图计划
- slots / prompts
- 可选复用已有 generated plan
- 发布前检查
- 正式推草稿箱

### 2. 你已经有生图结果
直接给：
- `--existing-generated-plan`

它会跳过重新生图，直接进入 publisher 检查 / 发布。

## 核心脚本

```bash
python3 scripts/publish_with_illustrations.py
```

## 最常用命令

### 只跑到检查
```bash
python3 scripts/publish_with_illustrations.py \
  --article /path/to/article.md \
  --existing-generated-plan /path/to/illustration-plan.generated.json \
  --publisher-config ~/.openclaw/skills/wechat-draft-publisher/config/settings.json \
  --check
```

### 直接发布到草稿箱
```bash
python3 scripts/publish_with_illustrations.py \
  --article /path/to/article.md \
  --existing-generated-plan /path/to/illustration-plan.generated.json \
  --publisher-config ~/.openclaw/skills/wechat-draft-publisher/config/settings.json \
  --publish
```

### 先生成计划 / slots，再 dry-run
```bash
python3 scripts/publish_with_illustrations.py \
  --article /path/to/article.md \
  --publisher-config ~/.openclaw/skills/wechat-draft-publisher/config/settings.json
```

## 输出

脚本会统一输出 JSON，至少包含：
- `ok`
- `flow`（插图链执行结果）
- `publish_result`（如启用正式发布）
- `next_action`（如失败）

## 依赖关系

这个 skill 依赖同仓库中的：
- `wechat-publish-from-materials`
- `wechat-draft-publisher`

安装脚本会一并安装它们。

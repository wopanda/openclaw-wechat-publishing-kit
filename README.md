# OpenClaw WeChat Publishing Kit

把你的**个人资料 + 参考内容 + 公众号配置**，整理成一篇适合你口吻的公众号文章，并送进**微信公众号草稿箱**。

如果你是第一次接这个 skill，先别想 workflow、预览链、图片桥这些事。  
**你只需要关心 3 件事：你要提供什么、怎么发到草稿箱、什么时候算成功。**

## 你只需要准备什么

第一次接入，只准备这 3 项：

### 1. 你的个人资料 / 口吻说明
也就是 `persona.md`。

至少写清：
- 你是谁
- 你主要写什么
- 你的表达风格
- 你的真实经历 / 判断
- 你希望文末怎么引导读者

### 2. 一篇参考内容，或者一组材料
可以是：
- 一篇参考文章
- 一组笔记
- 一份主题素材
- 一段你想展开的判断

### 3. 公众号发布配置
你需要准备：
- 微信公众号 `appid`
- 微信公众号 `secret`

---

## 你会得到什么

这套东西会帮你完成 3 件事：

1. 先整理出一篇适合你口吻的公众号正文
2. 做一次发布前检查
3. 把文章送进微信公众号草稿箱

也就是说，你最终看到的结果应该是：
- 已读取资料
- 已生成正文
- 已进入草稿箱

---

## 第一次接入：最短路径

### 第 1 步：克隆仓库

```bash
git clone https://gitee.com/woipanda/openclaw-wechat-publishing-kit.git
cd openclaw-wechat-publishing-kit
```

### 第 2 步：安装

```bash
bash install.sh
```

默认会安装最稳的发布链：
- `wechat-publish-from-materials`
- `wechat-draft-publisher`

### 第 3 步：改你的 persona

安装后，去这里改：

```bash
~/.openclaw/skills/wechat-publish-from-materials/user-templates/persona.md
```

### 第 4 步：填公众号配置

```bash
cd ~/.openclaw/skills/wechat-draft-publisher/config
cp credentials.example.json credentials.json
cp settings.example.json settings.json
```

然后填入：
- `appid`
- `secret`
- 作者名
- 输出目录

### 第 5 步：先做一次连通性检查

```bash
cd ~/.openclaw/skills/wechat-draft-publisher
python3 scripts/check_wechat_connection.py
```

如果这里能过，说明你的发布入口基本通了。

---

## 一句话怎么用

你可以直接对 OpenClaw 说：

```text
请读取我的 persona 和这篇参考内容，整理成公众号稿，并推送到公众号草稿箱。
```

或者：

```text
请根据我的 persona，把这组材料整理成一篇适合发布到微信公众号的文章，然后送进草稿箱。
```

---

## 最常见的 3 种使用方式

### 1. 我有一篇参考文章
直接让它：
- 读你的 persona
- 吸收参考内容
- 生成你的版本
- 推到草稿箱

### 2. 我有一组材料 / 笔记
直接让它：
- 先整理观点
- 再生成正文
- 再推草稿箱

### 3. 我已经有 Markdown
那你可以跳过前面的整理，直接用：
- `wechat-draft-publisher`

---

## 第一次成功前，你暂时不用关心什么

这些都不是第一次接入必须要开的：
- 飞书预览
- 图文原型
- 图片桥
- 复杂 workflow
- 扩展编排链

先把**“资料 → 正文 → 草稿箱”**跑通，再考虑进阶能力。

---

## 常见问题

### 1. 我到底要提供哪些信息？
最少就是：
- `persona.md`
- 一篇参考内容或一组材料
- 公众号 `appid / secret`

### 2. 怎么知道有没有连上公众号？
先跑：

```bash
python3 scripts/check_wechat_connection.py
```

### 3. 我已经有 Markdown，还要走前面那套吗？
不用。  
你可以直接把 Markdown 交给 `wechat-draft-publisher` 推草稿箱。

---

## 进阶能力（先不用）

如果你后面要更复杂的链路，仓库里还保留了扩展能力，比如：
- 更复杂的内容编排
- 更多中间产物
- 可选扩展模块

但这不是第一次接入必须理解的内容。

---

## 安全说明

- 不要把真实 `credentials.json` 提交到 git
- 不要把真实 `settings.json` 提交到 git
- 不要在 README、SKILL、示例里暴露 API Key / AppSecret

---

## 验收与演示文档

如果你需要看更完整的验收记录，再看：
- `docs/fresh-clone-validation.md`
- `docs/demo-walkthrough.md`
- `docs/hardening-notes.md`

# OpenClaw WeChat Publishing Kit

把**个人信息文件 + 参考内容 + 可选主题**，推进成**微信公众号可发布正文**，并送入**公众号草稿箱**的一套 OpenClaw skill bundle。

这不是“一键黑箱全自动发文器”。
它更像一套**可控、分阶段、可替换人设、可检查**的发布工作台：
- 前链收口内容
- 按需做飞书预览
- 发布前清洗与预检
- 推送到微信公众号草稿箱

## 这套仓库包含什么

### 主入口
- `skills/wechat-publish-from-materials/`
  - 面向用户的主 skill
  - 负责把“个人信息文件 + 参考内容 + 发布意图”收口成可发布链路

### 下游能力
- `skills/wechat-article-workflow/`
  - 内容前链调度
- `skills/material-to-graphic-report/`
  - 飞书图文预览 / 视觉原型（可选）
- `skills/wechat-draft-publisher/`
  - 发布前清洗 / 预检 / 推送公众号草稿箱

### 可替换模板
- `templates/persona.md`
- `templates/writing-guide.md`
- `templates/title-formulas.md`
- `templates/abstract-transfer.md`

## 适合谁
- 想给别人交付一套“可替换人设”的公众号发布能力
- 想把“参考文章 / 材料 / 主题”推进成公众号稿件
- 想保留人工判断，但把发布链做稳

## 不适合谁
- 想要无人值守的一键全自动正式群发
- 想承诺稳定自动专属生图
- 想把它当成事实核验器、选题判断器或合规审核器

## 你能用它做什么
1. 读取个人信息文件，抽取身份、经历、表达偏好与不可偏离主张
2. 吸收参考内容，只借结构、信息与论证线索
3. 生成干净的公众号 Markdown 正文
4. 视需要生成飞书图文预览稿
5. 做一次发布前清洗 / 预检
6. 推送到微信公众号草稿箱

## 不能承诺什么
- 不承诺从选题到正式群发的全自动闭环
- 不承诺自动写出高质量终稿
- 不承诺稳定可用的专属配图
- 不承诺直接正式群发
- 不承诺自动完成事实核验、观点正确性与合规审核

## 默认主链

```text
个人信息文件 + 参考内容 + 可选主题
    ↓
wechat-publish-from-materials
    ↓
wechat-article-workflow
    ↓
(可选) material-to-graphic-report
    ↓
wechat-draft-publisher
    ↓
微信公众号草稿箱
```

## 快速开始

### 1) 克隆仓库

```bash
git clone <your-gitee-repo-url>
cd openclaw-wechat-publishing-kit
```

### 2) 安装到 OpenClaw skills 目录

```bash
bash install.sh
```

默认会把这些目录复制到：
- `~/.openclaw/skills/wechat-publish-from-materials`
- `~/.openclaw/skills/wechat-article-workflow`
- `~/.openclaw/skills/material-to-graphic-report`
- `~/.openclaw/skills/wechat-draft-publisher`

### 3) 替换你的模板

至少先改：
- `templates/persona.md`

推荐再改：
- `templates/writing-guide.md`
- `templates/title-formulas.md`

### 4) 填微信发布配置

先复制模板：

```bash
cd ~/.openclaw/skills/wechat-draft-publisher/config
cp credentials.example.json credentials.json
cp settings.example.json settings.json
```

然后填入你自己的：
- 微信公众号 `appid`
- 微信公众号 `secret`
- 作者名
- 输出目录

### 5) 做最小连通性检查

```bash
cd ~/.openclaw/skills/wechat-draft-publisher
python3 scripts/check_wechat_connection.py
```

### 6) 开始用

你可以直接对 OpenClaw 说：

```text
请用 wechat-publish-from-materials：
读取我的 persona 文件，参考这篇内容，写成适合我口吻的公众号稿，检查后推到草稿箱。
```

## 最常见的 3 条用法

### A. 只有主题，想推进成公众号稿
- 用 `wechat-publish-from-materials`
- 它会先收口个人信息和主题，再推进内容前链

### B. 有一篇参考内容，想改成“我的版本”
- 用 `wechat-publish-from-materials`
- 明确要求“只借结构 / 论证线索，不照搬口吻”

### C. 已经有 Markdown，只想推草稿箱
- 直接用 `wechat-draft-publisher`

## 仓库结构

```text
openclaw-wechat-publishing-kit/
├── README.md
├── install.sh
├── LICENSE
├── templates/
├── skills/
│   ├── wechat-publish-from-materials/
│   ├── wechat-article-workflow/
│   ├── material-to-graphic-report/
│   └── wechat-draft-publisher/
└── docs/
```

## 能力边界建议

### 首版建议承诺
- 材料 + 人设 + 参考内容 → 成稿 Markdown → 草稿箱
- 飞书预览为可选，不做硬依赖
- 专属生图为可选，不做首版承诺

### 首版不建议承诺
- 自动选题
- 自动抓全网资料
- 自动专属配图并保证可用
- 正式群发
- 复杂多轮审稿工作台

## 故障排查

### 1. 公众号连接失败
先跑：

```bash
python3 scripts/check_wechat_connection.py
```

### 2. 推草稿箱时报封面/图片问题
先跑：

```bash
python3 scripts/publish_markdown.py --check --input <your-article.md>
```

### 3. 飞书预览与发布稿不一致
请确保交给发布器的是**干净正文**，不要把观点卡、brief、图片位、工作流备注混进正文。

## 安全说明
- 不要把真实 `credentials.json` 提交到 git
- 不要把真实 `settings.json` 提交到 git
- 不要在 README、SKILL、示例里暴露 API Key / AppSecret

## 当前最稳妥的对外口径

这是一套**面向微信公众号创作者的发布工作台**：
把“主题 / 材料 / 参考内容 / 已有预览稿”推进成**可检查、可预览、可进入公众号草稿箱**的内容。

它强调：
- 模板可替换
- 人设可定制
- 阶段可检查
- 发布链可复用

但**不承诺一键黑箱全自动正式发布**。

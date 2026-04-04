# Demo Walkthrough

这份 walkthrough 对应当前仓库的 **fresh clone 验收版**。

目标不是伪造“真实公众号已成功发出”，而是验证：
- fresh clone 后能否安装
- core / full 两条路径是否可跑
- demo 产物是否能生成
- 发布链配置入口是否清楚

## 一、fresh clone

```bash
git clone https://gitee.com/woipanda/openclaw-wechat-publishing-kit.git
cd openclaw-wechat-publishing-kit
```

## 二、core 安装

```bash
bash install.sh --core
```

预期结果：
- 安装 `wechat-publish-from-materials`
- 安装 `wechat-draft-publisher`
- 自动同步 `user-templates/`

## 三、full 安装

```bash
bash install.sh --full
```

预期结果：
- 在 core 基础上，再安装：
  - `wechat-article-workflow`
  - `material-to-graphic-report`

## 四、core 演示链

### 1. 生成人设摘要

```bash
python3 skills/wechat-publish-from-materials/scripts/prepare_persona_context.py \
  --input templates/persona.md \
  --output /tmp/owpk-persona-summary.md
```

### 2. 生成 article brief

```bash
python3 skills/wechat-publish-from-materials/scripts/build_article_brief.py \
  --persona /tmp/owpk-persona-summary.md \
  --reference examples/demo-reference.md \
  --topic "为什么企业 agent 开始卡在上下文接入" \
  --output /tmp/owpk-article-brief.md
```

### 3. 生成发布 handoff 命令

```bash
python3 skills/wechat-publish-from-materials/scripts/handoff_to_publisher.py \
  --draft /tmp/owpk-article-brief.md
```

预期结果：
- 得到一个可交给发布链的命令骨架
- 说明 core 链的最小产物可生成

## 五、full 演示链

### 1. 生成 workflow context

```bash
python3 skills/wechat-article-workflow/scripts/prepare_context.py \
  --input-mode topic \
  --topic "为什么企业 agent 开始卡在上下文接入" \
  --input-text "为什么重要：企业 agent 一进现场，瓶颈就从模型切到上下文和权限。你该怎么用：以后判断企业 agent，优先看上下文如何接入。" \
  --project-root ./skills/wechat-article-workflow/project-template \
  --output-dir /tmp/owpk-workflow-output
```

### 2. 生成选题卡与观点菜单

```bash
python3 skills/wechat-article-workflow/scripts/prepare_briefs.py \
  --manifest /tmp/owpk-workflow-output/<workflow_manifest.json>
```

### 3. 选定观点后生成 draft handoff

> 当前 demo 默认手动把 manifest 里的 `selected_angle_id` 设为 `A`，再执行：

```bash
python3 skills/wechat-article-workflow/scripts/generate_draft.py \
  --manifest /tmp/owpk-workflow-output/<workflow_manifest.json> \
  --project-root ./skills/wechat-article-workflow/project-template \
  --output-dir /tmp/owpk-workflow-output
```

预期结果：
- 得到：
  - workflow_context
  - topic_pick
  - angle_menu
  - draft_handoff

## 六、发布链配置验证

### 1. 复制配置模板

```bash
cd ~/.openclaw/skills/wechat-draft-publisher/config
cp credentials.example.json credentials.json
cp settings.example.json settings.json
```

### 2. 连通性检查

```bash
cd ~/.openclaw/skills/wechat-draft-publisher
python3 scripts/check_wechat_connection.py --config ./config
```

说明：
- 如果配置是假的 demo appid / secret，脚本应明确返回微信鉴权错误
- 这说明：
  - 配置加载通了
  - 请求链路通了
  - 错误是业务凭据问题，不是仓库结构问题

## 七、本轮验收结论

当前仓库已经达到：
- fresh clone 可装
- core / full 路径清晰
- demo 产物可生成
- README 可跟着走

但仍然要区分：
- **可开箱交付**
- **真实公众号生产可用**

真实生产可用仍取决于：
- 你的公众号 appid / secret
- 你自己的 persona / reference 内容
- 是否补齐图片桥与完整项目上下文

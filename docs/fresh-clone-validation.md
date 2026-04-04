# Fresh Clone Validation

验收对象：
- `https://gitee.com/woipanda/openclaw-wechat-publishing-kit`

验收目标：
- 仓库公开可 clone
- fresh clone 后可按 README 安装
- core / full 两种安装路径可落盘
- demo 脚本可生成核心中间产物

## 1. Clone 验证

已验证：
```bash
git clone --depth 1 https://gitee.com/woipanda/openclaw-wechat-publishing-kit.git /tmp/owpk-public
```

结果：
- clone 成功
- HEAD = `d013a5b`

## 2. Core 安装验证

已验证：
```bash
HOME=/tmp/owpk-accept-home bash ./install.sh --core
```

结果：
- 安装成功
- 已安装：
  - `wechat-publish-from-materials`
  - `wechat-draft-publisher`
- 已同步：
  - `wechat-publish-from-materials/user-templates/`

## 3. Full 安装验证

已验证：
```bash
HOME=/tmp/owpk-accept-home-full bash ./install.sh --full
```

结果：
- 安装成功
- 在 core 基础上追加：
  - `wechat-article-workflow`
  - `material-to-graphic-report`
- 已验证 `project-template/` 落盘

## 4. Core Demo 产物验证

已验证：
- `prepare_persona_context.py`
- `build_article_brief.py`
- `handoff_to_publisher.py`

结果：
- 成功生成：
  - `/tmp/owpk-persona-summary.md`
  - `/tmp/owpk-article-brief.md`
- 成功输出发布命令骨架：
  - `python3 scripts/publish_markdown.py --input "/tmp/owpk-article-brief.md"`

## 5. Full Demo 产物验证

已验证：
- `prepare_context.py`
- `prepare_briefs.py`
- `generate_draft.py`

输入：
- 主题：`为什么企业 agent 开始卡在上下文接入`
- `project-root`：仓库内置 `project-template/`

结果：
- 成功生成：
  - `workflow_context.md`
  - `workflow_manifest.json`
  - `topic_pick.md`
  - `angle_menu.md`
  - `draft_handoff.md`

## 6. 发布链配置验证

已验证：
- `check_wechat_connection.py --config ./config`

结果：
- 在 demo 假配置下，脚本明确返回：
  - `invalid appid`
- 说明：
  - 配置目录加载成功
  - 请求已真正打到微信接口
  - 错误落点是凭据错误，而不是仓库结构错误

## 7. 本轮发现并修掉的问题

### 已修
1. README “最常见的 3 条用法”里 A 段标题缺失
2. 安装路径说明还不够 reader-facing
3. full 链的项目根目录说明不够明确

### 仍保留的边界
1. 没有真实公众号配置时，不能伪造发布成功
2. 没有真实图片桥时，不能伪造真实生图成功
3. full 链仍然是扩展能力，不建议作为第一次上手默认入口

## 8. 结论

当前仓库已通过本轮“fresh clone + install + demo 产物”验收。

可以对外使用的最稳口径是：
- 默认走 `--core`
- `--full` 作为扩展链
- 真实生产发布依赖用户自己补公众号凭据与图片桥

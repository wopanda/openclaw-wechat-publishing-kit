# 开箱交付版改造记录

这一版的目标是：
- 去掉对作者本机固定目录的强依赖
- 让别人 clone 后能理解如何配置
- 让核心链可以先跑起来

## 已完成

### 1. 安装脚本分层
- `install.sh --core`
- `install.sh --full`

### 2. 主入口模板自动同步
安装时会把：
- `templates/*`
复制到：
- `wechat-publish-from-materials/user-templates/`

### 3. wechat-article-workflow 去硬编码
不再要求固定项目目录。
现在支持：
- `--project-root /your/project/path`
- 环境变量 `WECHAT_ARTICLE_PROJECT_ROOT`
- 默认回退到 skill 内置 `project-template/`

### 4. 新增 project-template
提供最小可理解目录骨架：
- `00-主线与流程/`
- `02-个人上下文库/`
- `03-样板库/`
- `04-运行记录/`

### 5. material-to-graphic-report 去硬编码
不再写死某个本地图片 skill 路径。
现在通过环境变量提供：
- `MATERIAL_TO_GRAPHIC_IMAGE_SCRIPT`

## 还建议继续做

### A. wechat-article-workflow 的 README 补独立说明
### B. 为完整链加一个 demo walkthrough
### C. 对 publish 链再做一次 fresh-clone 验收
### D. 如果要给更多人交付，建议补 releases / tags

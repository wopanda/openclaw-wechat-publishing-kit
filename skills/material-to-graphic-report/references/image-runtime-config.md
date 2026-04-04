# 生图运行配置（不含密钥）

这个文件只记录**可公开的运行参数**与接入方式，不记录真实 API Key。

## 当前已验证可用的运行形态

### A. material-to-graphic-report 默认生图配置
- 提供商形态：兼容 OpenAI / Gemini 双接口风格的聚合服务
- Base URL：`https://api.huandutech.com`
- 当前参考模型：`gemini-3.1-flash-image-preview-c`

### B. 当前环境已实测可用的 nano 生图 skill
- Skill：`nano-banana-pro`（目录：`/root/.openclaw/skills/nano-banana-pro-2`）
- 运行方式：本地脚本 `scripts/generate_image.py`
- 当前实测可用模型：`gemini-3-pro-image-preview`
- 当前实测可用 Base URL：`https://api.huandutech.com`
- 备注：当前环境变量里已经有 `GEMINI_API_KEY`，但默认 `GEMINI_MODEL=gemini-3.1-pro-preview` 不适合该脚本的多模态图片输出；接入时应显式覆盖成图片模型。

## 密钥管理原则

1. **不要把真实 API Key 写进 SKILL.md、reference 文件、示例文档或飞书文档。**
2. **不要把真实 API Key 写进测试截图、对外分享文档或 prompt 示例。**
3. 运行时只通过：
   - 环境变量
   - per-skill 配置
   - 受控凭据存储
   注入密钥。

## 推荐配置方式

### 方式 A：per-skill 配置（推荐）
在 OpenClaw 配置里为这个 skill 提供：

```json5
{
  skills: {
    entries: {
      "material-to-graphic-report": {
        env: {
          IMAGE_API_BASE_URL: "https://api.huandutech.com",
          IMAGE_API_MODEL: "gemini-3.1-flash-image-preview-c",
          IMAGE_API_KEY: "[运行时注入，不写入仓库示例]"
        }
      }
    }
  }
}
```

### 方式 B：环境变量

```bash
export IMAGE_API_BASE_URL="https://api.huandutech.com"
export IMAGE_API_MODEL="gemini-3.1-flash-image-preview-c"
export IMAGE_API_KEY="[运行时注入，不写入仓库示例]"
```

## Skill 内部默认读取顺序

运行时优先读取：
1. `IMAGE_API_KEY`
2. `IMAGE_API_BASE_URL`
3. `IMAGE_API_MODEL`

如果缺少 key：
- 可以继续做图文原型、图片位、prompt、飞书预览
- 但不要真正发起生图

## 对外展示时允许保留的内容

可以公开写：
- Base URL
- 模型名
- 能力边界
- 调用方式
- 输入输出契约

不要公开写：
- API Key
- 完整 Authorization header
- 带真实 key 的 curl 命令
- 含真实 key 的日志片段

## 文档里的示例写法

### 安全示例

安全原则不是“把真实 key 写进命令示例”，而是：
- 文档里只说明**通过运行时注入鉴权**
- 具体执行命令由本地脚本、受控环境变量或配置层完成
- 截图、日志、仓库文本都不展示真实鉴权参数

### 不安全示例

不要在任何文档里出现：
- 带真实 key 的完整 URL
- 带真实 key 的 curl 命令
- 能直接复制出去使用的真实鉴权串

## 当前阶段的使用建议

对于 `material-to-graphic-report`：
- 先把 skill 设计、飞书预览、图片位、替换协议做完整
- 再用密钥做运行时调用
- 产物里只保留模型名与接口信息，不保留密钥

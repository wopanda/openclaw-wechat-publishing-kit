# 生图运行配置（不含密钥）

这个文件只记录**可公开的运行参数**与接入方式，不记录真实 API Key。

## 当前可开箱版本的默认口径

`material-to-graphic-report` 不再硬编码依赖某个固定本地 skill 目录。

它现在通过环境变量指定真实图片桥脚本：

- `MATERIAL_TO_GRAPHIC_IMAGE_SCRIPT`：指向本地 `generate_image.py`
- `GEMINI_API_KEY`：运行时注入
- `GOOGLE_GEMINI_BASE_URL`：可选，默认 `https://api.huandutech.com`

## 当前参考模型
- 默认图片模型：`gemini-3-pro-image-preview`

## 推荐配置方式

### 方式 A：per-skill 环境变量（推荐）

```json5
{
  skills: {
    entries: {
      "material-to-graphic-report": {
        env: {
          MATERIAL_TO_GRAPHIC_IMAGE_SCRIPT: "/path/to/generate_image.py",
          GOOGLE_GEMINI_BASE_URL: "https://api.huandutech.com",
          GEMINI_API_KEY: "[运行时注入，不写入仓库]"
        }
      }
    }
  }
}
```

### 方式 B：shell 环境变量

```bash
export MATERIAL_TO_GRAPHIC_IMAGE_SCRIPT="/path/to/generate_image.py"
export GOOGLE_GEMINI_BASE_URL="https://api.huandutech.com"
export GEMINI_API_KEY="[运行时注入]"
```

## 缺少图片桥时的行为

如果没有提供 `MATERIAL_TO_GRAPHIC_IMAGE_SCRIPT`：
- 可以继续做图文原型、图片位、prompt、飞书预览
- 但不要真正发起生图

## 安全原则
- 不公开 API Key
- 不公开 Authorization header
- 不公开带真实 key 的 curl 命令

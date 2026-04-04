# External Image Bridge Integration

## 目标
把 `material-to-graphic-report` 的真实生图执行接到**用户自己提供的图片桥脚本**，而不是写死某个本地 skill 路径。

## 当前默认接法
当流程进入 `generate-if-available` 时：
1. 先按 `image-generation-input-contract.md` 组织 `slots`
2. 再调用：
   - `scripts/generate_with_nano.py`
3. 该脚本内部会转调：
   - 环境变量 `MATERIAL_TO_GRAPHIC_IMAGE_SCRIPT` 指向的本地脚本

## 固定模型
- 默认图片模型：`gemini-3-pro-image-preview`
- 默认 Base URL：`https://api.huandutech.com`

## 为什么这样改
因为“可交付版”不能假设每个用户机器上都有固定的本地图片 skill 安装目录。

所以现在改成：
- 仓库不绑定具体图片 skill 安装路径
- 用户自己在运行环境里提供图片桥

## 最小调用示例
```bash
export MATERIAL_TO_GRAPHIC_IMAGE_SCRIPT="/path/to/generate_image.py"
export GEMINI_API_KEY="your-key"

python3 scripts/generate_with_nano.py \
  --slots-file /path/to/slots.json \
  --output-dir /tmp/material_to_graphic_images
```

## 返回结果
返回 JSON：
- `slot_id`
- `status`
- `local_path` / `reason`
- `model`
- `base_url`

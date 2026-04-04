# Nano Banana Integration

## 目标
把 `material-to-graphic-report` 的真实生图执行默认接到当前环境里已实测可用的 `nano-banana-pro`。

## 当前默认接法
当流程进入 `generate-if-available` 时：
1. 先按 `image-generation-input-contract.md` 组织 `slots`
2. 再调用：
   - `scripts/generate_with_nano.py`
3. 该脚本内部会转调：
   - `/root/.openclaw/skills/nano-banana-pro-2/scripts/generate_image.py`

## 固定模型
- 默认图片模型：`gemini-3-pro-image-preview`
- 默认 Base URL：`https://api.huandutech.com`

## 为什么显式锁这个模型
当前环境变量里的默认：
- `GEMINI_MODEL=gemini-3.1-pro-preview`

它不适合这条图片输出链，容易报：
- `Multi-modal output is not supported.`

所以接入时必须显式覆盖成图片模型。

## 最小调用示例
```bash
python3 scripts/generate_with_nano.py \
  --slots-file /path/to/slots.json \
  --output-dir /tmp/openclaw/material_to_graphic_images
```

## 返回结果
返回 JSON：
- `slot_id`
- `status`
- `local_path` / `reason`
- `model`
- `base_url`

后续再按 `image-replacement-protocol.md` 回填到飞书文档。

# Slot Replacement Bridge

## 目标
把 `generate_with_nano.py` 产出的真实图片，按 `slot_id` 回填到图文原型里。

## 当前默认接法
1. 原型稿里先有稳定的图片位块：
   - `### 图片位｜slot_id｜标题`
2. 真实生图完成后，得到：
   - `results.json`
3. 再调用：
   - `scripts/replace_images_by_slot.py`
4. 输出一版已替换图片的 Markdown 成品稿

## 最小调用示例
```bash
python3 scripts/replace_images_by_slot.py \
  --prototype-file /path/to/prototype.md \
  --results-file /path/to/results.json \
  --slots-file /path/to/slots.json \
  --output-file /path/to/final_with_images.md
```

## 返回结果
- `output_file`
- `replaced_slot_ids`
- `missing_slot_ids`

## 注意
- 只按 `slot_id` 替换，不凭肉眼找图位
- 替换后保留标题和图注，移除占位字段
- 如某个 `slot_id` 没找到，显式报出，不要默默跳过

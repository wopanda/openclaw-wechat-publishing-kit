# 样式主题说明

本仓库当前内置 3 套主题预设：

## 1. `wechat-pro`（默认）
- 参考吸收：
  - `doocs/md` 的“简洁、优雅、少额外调整”方向
  - `aximof/wechat_artical_publisher_skill` 的绿色系正文 / 移动端兼容思路
- 适合：通用公众号正文、知识分享、案例拆解

## 2. `cyan-clean`
- 参考吸收：
  - `wechat-mdnice` 的青蓝单色系风格
- 适合：科技感、教程感更强的内容

## 3. `slate-blue`
- 参考吸收：
  - `doocs/md` 的简洁排版 + 更稳重的蓝灰色系
- 适合：商业、报告、偏正式内容

## 配置方式

在 `config/settings.json` 中设置：

```json
{
  "style_theme": "wechat-pro",
  "accent_color": "#1f9d55"
}
```

### 可选值
- `wechat-pro`
- `cyan-clean`
- `slate-blue`

### `accent_color`
- 可选
- 不填则使用主题默认色
- 填了会覆盖主题主强调色

## 当前这层解决什么问题

- 不再只是“能发进去”
- 开始有稳定默认观感
- 标题、正文、引用、代码、表格、链接、图片都有统一视觉规则
- 兼顾微信移动端列表和正文可读性

## 当前还没做到的

- 可视化主题编辑器
- 大量样式模板市场
- 飞书预览和微信成品双端完全同构
- 真正的高级设计感封面系统

# 去 AI 味 / 润色模块接入说明

## 目标

在不破坏 5.2 边界的前提下，把“去 AI 味 / 润色”作为**发布前上游一步**接入：

`原稿 -> polish_markdown.py -> publish_markdown.py -> 微信草稿箱`

## 当前接入方式

本仓库不内置具体润色模型，而是提供一个**可插拔命令接口**：

- `scripts/polish_markdown.py`
- `scripts/polish_and_publish.py`

你只需要在配置里填一个命令模板：

```json
{
  "polish": {
    "enabled": true,
    "command": "python3 /path/to/your-polish-script.py --input {input} --output {output}",
    "timeout_seconds": 180,
    "keep_intermediate": true
  }
}
```

其中：
- `{input}` 会被替换成原始 Markdown 路径
- `{output}` 会被替换成润色后 Markdown 路径

## 推荐接法

### 方式 A：先润色，再预检发布

```bash
python3 scripts/polish_and_publish.py   --file /path/to/article.md   --cover-image /path/to/cover.jpg   --check
```

### 方式 B：先单独润色，再单独发布

```bash
python3 scripts/polish_markdown.py   --input /path/to/article.md   --output /path/to/article.polished.md

python3 scripts/publish_markdown.py   --file /path/to/article.polished.md   --cover-image /path/to/cover.jpg
```

## 为什么这样接最稳

1. 不把 5.2 重新做回大而全写作系统
2. 不绑定某一个润色模型或脚本实现
3. 后续你换 prompt、换模型、换供应商，都不用重写发布链
4. 写书时也能清楚表达：
   - 润色是发布前上游步骤
   - 草稿箱发布是后段确定性步骤

## 书里最稳口径

可以写：

> 在正式推草稿箱之前，这条链路还可以再串一个“去 AI 味 / 润色”模块，先把稿子修顺、收住机器味，再进入发布预检和草稿箱投递。

不要写：

> 5.2 本身负责从零生成、润色、配图、排版、发布整条链。

## 内置模式（本仓库已带）

如果你还没有独立的润色脚本，可以先用仓库内置的低风险版本：

```json
{
  "polish": {
    "enabled": true,
    "command": "python3 scripts/polish_builtin.py --input {input} --output {output}",
    "timeout_seconds": 180,
    "keep_intermediate": true
  }
}
```

配套规则见：
- `references/polish-rules.md`

### 说明
- 这是一个 **v1 低风险内置模式**，主打收掉明显模板腔、填充转场和部分抽象框架词。
- 它不是完整写作器，也不是重写器。
- 如果你后续有更强的模型化润色模块，仍建议继续替换成自定义 `polish.command`。

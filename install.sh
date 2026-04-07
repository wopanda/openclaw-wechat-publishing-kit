#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="${OPENCLAW_SKILLS_DIR:-$HOME/.openclaw/skills}"

mkdir -p "$TARGET_DIR"

install_skill() {
  local skill="$1"
  local src="$REPO_DIR/skills/$skill"
  local dst="$TARGET_DIR/$skill"
  if [ ! -d "$src" ]; then
    echo "skip missing $src"
    return
  fi
  rm -rf "$dst"
  cp -a "$src" "$dst"
  echo "installed: $skill"
}

install_skill "wechat-publish-from-materials"
install_skill "wechat-draft-publisher"
install_skill "wechat-illustrated-publisher"

USER_TPL_DIR="$TARGET_DIR/wechat-publish-from-materials/user-templates"
mkdir -p "$USER_TPL_DIR"
cp -a "$REPO_DIR/templates/." "$USER_TPL_DIR/"
echo "installed: user-templates"

DRAFT_CFG_DIR="$TARGET_DIR/wechat-draft-publisher/config"
mkdir -p "$DRAFT_CFG_DIR"

if [ ! -f "$DRAFT_CFG_DIR/credentials.json" ] && [ -f "$DRAFT_CFG_DIR/credentials.example.json" ]; then
  cp "$DRAFT_CFG_DIR/credentials.example.json" "$DRAFT_CFG_DIR/credentials.json"
  echo "created: $DRAFT_CFG_DIR/credentials.json"
fi

if [ ! -f "$DRAFT_CFG_DIR/settings.json" ] && [ -f "$DRAFT_CFG_DIR/settings.example.json" ]; then
  cp "$DRAFT_CFG_DIR/settings.example.json" "$DRAFT_CFG_DIR/settings.json"
  echo "created: $DRAFT_CFG_DIR/settings.json"
fi

CURRENT_AUTHOR=""
if [ -f "$DRAFT_CFG_DIR/settings.json" ]; then
  CURRENT_AUTHOR=$(python3 - <<'PY' "$DRAFT_CFG_DIR/settings.json"
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
try:
    data = json.loads(path.read_text(encoding='utf-8'))
    print((data.get('author') or '').strip())
except Exception:
    print('')
PY
)
fi

echo
echo "安装完成 ✅"
echo
echo "请先做 4 件事："
echo "1) 编辑 persona: $USER_TPL_DIR/persona.md"
echo "2) 填公众号配置: $DRAFT_CFG_DIR/credentials.json (appid/secret)"
echo "3) 确认作者名: $DRAFT_CFG_DIR/settings.json"
if [ -n "$CURRENT_AUTHOR" ]; then
  echo "   当前作者名：$CURRENT_AUTHOR"
else
  echo "   当前作者名：未设置（建议先填 author）"
fi
echo "4) 连通性检查: python3 $TARGET_DIR/wechat-draft-publisher/scripts/check_wechat_connection.py"
echo
echo "然后先选配图模式（非常关键）："
echo "A. 纯文字发布（最快）"
echo "B. 你自己提供图片"
echo "C. AI 自动配图："
echo "   - C1 MiniMax（默认）"
echo "   - C2 Jimeng / 即梦（提供 API key 后可切换）"
echo
echo "给 OpenClaw 的一句话示例："
echo "- 纯文字：请按我的 persona，把材料整理成公众号文章，先不要配图，检查后推到草稿箱。"
echo "- 自带图：请按我的 persona 整理成文，封面和正文配图我自己提供，检查后推到草稿箱。"
echo "- AI图（MiniMax）：请按我的 persona 整理成文，并使用 MiniMax 为合适段落生成插图方案与 AI 配图，检查后推到草稿箱。"
echo "- AI图（Jimeng）：请按我的 persona 整理成文，并使用 Jimeng / 即梦为合适段落生成插图方案与 AI 配图；如果需要 Jimeng key，我会补给你。"

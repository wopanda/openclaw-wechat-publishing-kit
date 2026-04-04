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

echo
echo "安装完成。下一步："
echo "1) 编辑 $USER_TPL_DIR/persona.md"
echo "2) 配置 $TARGET_DIR/wechat-draft-publisher/config/credentials.json"
echo "3) 配置 $TARGET_DIR/wechat-draft-publisher/config/settings.json"
echo "4) 运行公众号连通性检查"

#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="${OPENCLAW_SKILLS_DIR:-$HOME/.openclaw/skills}"
PROFILE="core"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<EOF
Usage:
  bash install.sh [--core|--full]

默认安装 --core。
- --core: 只安装最稳的“整理正文 → 推草稿箱”链路
- --full: 额外安装扩展模块（给进阶用户）
EOF
  exit 0
fi

if [[ "${1:-}" == "--full" ]]; then
  PROFILE="full"
elif [[ "${1:-}" == "--core" || -z "${1:-}" ]]; then
  PROFILE="core"
else
  echo "Unknown option: $1"
  exit 1
fi

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

if [[ "$PROFILE" == "full" ]]; then
  install_skill "wechat-article-workflow"
  install_skill "material-to-graphic-report"
fi

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

if [[ "$PROFILE" == "full" ]]; then
  echo
  echo "提示：你还安装了扩展模块，但第一次接入可以先不用它们。"
fi

#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="${OPENCLAW_SKILLS_DIR:-$HOME/.openclaw/skills}"
PROFILE="core"

usage() {
  cat <<EOF
Usage:
  bash install.sh [--core|--full]

Profiles:
  --core (default)
    Install only the stable publish path:
      - wechat-publish-from-materials
      - wechat-draft-publisher

  --full
    Install core + optional orchestration/preview skills:
      - wechat-article-workflow
      - material-to-graphic-report
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

if [[ "${1:-}" == "--full" ]]; then
  PROFILE="full"
elif [[ "${1:-}" == "--core" || -z "${1:-}" ]]; then
  PROFILE="core"
else
  echo "Unknown option: $1"
  usage
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
  echo "installed: $skill -> $dst"
}

# stable path first
install_skill "wechat-publish-from-materials"
install_skill "wechat-draft-publisher"

# optional path
if [[ "$PROFILE" == "full" ]]; then
  install_skill "wechat-article-workflow"
  install_skill "material-to-graphic-report"
fi

# copy user-editable templates into main skill for convenience
USER_TPL_DIR="$TARGET_DIR/wechat-publish-from-materials/user-templates"
mkdir -p "$USER_TPL_DIR"
cp -a "$REPO_DIR/templates/." "$USER_TPL_DIR/"
echo "installed: templates -> $USER_TPL_DIR"

echo
echo "Done (profile=$PROFILE). Next:"
echo "1) cd $TARGET_DIR/wechat-draft-publisher/config"
echo "2) cp credentials.example.json credentials.json"
echo "3) cp settings.example.json settings.json"
echo "4) edit credentials.json / settings.json"
echo "5) edit $USER_TPL_DIR/persona.md"
if [[ "$PROFILE" == "core" ]]; then
  echo
  echo "Tip: use '--full' only if you also want optional preview/orchestration skills."
fi

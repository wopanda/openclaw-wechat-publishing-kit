#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="${OPENCLAW_SKILLS_DIR:-$HOME/.openclaw/skills}"

mkdir -p "$TARGET_DIR"

for skill in \
  wechat-publish-from-materials \
  wechat-article-workflow \
  material-to-graphic-report \
  wechat-draft-publisher
  do
  src="$REPO_DIR/skills/$skill"
  dst="$TARGET_DIR/$skill"
  if [ ! -d "$src" ]; then
    echo "skip missing $src"
    continue
  fi
  rm -rf "$dst"
  mkdir -p "$(dirname "$dst")"
  cp -a "$src" "$dst"
  echo "installed: $skill -> $dst"
done

echo
echo "Done. Next:"
echo "1) edit $TARGET_DIR/wechat-draft-publisher/config/credentials.json"
echo "2) edit $TARGET_DIR/wechat-draft-publisher/config/settings.json"
echo "3) replace your persona template as needed"

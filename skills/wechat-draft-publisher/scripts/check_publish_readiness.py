#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PUBLISH_SCRIPT = SCRIPT_DIR / "publish_markdown.py"
CHECK_CONN_SCRIPT = SCRIPT_DIR / "check_wechat_connection.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify publish readiness before WeChat draft publishing")
    parser.add_argument("--file", required=True, help="Markdown file path")
    parser.add_argument("--content", help="Inline markdown content")
    parser.add_argument("--title")
    parser.add_argument("--author")
    parser.add_argument("--cover-image")
    parser.add_argument("--tail-image")
    parser.add_argument("--body-image", action="append", dest="body_image")
    parser.add_argument("--body-image-placement", choices=["after-intro", "before-ending", "after-first-h2", "before-signature"])
    parser.add_argument("--max-body-images", type=int)
    parser.add_argument("--image-state", choices=["article-specific", "fallback-approved", "text-only", "blocked-by-image"])
    parser.add_argument("--strict-illustration", action="store_true")
    parser.add_argument("--config")
    parser.add_argument("--asset-base-dir")
    parser.add_argument("--style-theme")
    parser.add_argument("--accent-color")
    return parser.parse_args()


def _exists(path_text: str | None) -> bool | None:
    if not path_text:
        return None
    src = str(path_text).strip()
    if not src:
        return None
    if src.startswith(("http://", "https://")):
        return True
    return Path(src).expanduser().exists()


def _run_json(cmd: list[str]) -> tuple[int, dict]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    payload = {}
    text = (proc.stdout or "").strip()
    if text:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = {"raw_stdout": text}
    else:
        payload = {"raw_stdout": ""}
    if proc.stderr:
        payload["stderr"] = proc.stderr
    return proc.returncode, payload


async def main() -> int:
    args = parse_args()

    conn_cmd = [sys.executable, str(CHECK_CONN_SCRIPT), "--all"]
    if args.config:
        conn_cmd.extend(["--config", args.config])
    conn_code, conn_payload = _run_json(conn_cmd)

    publish_cmd = [sys.executable, str(PUBLISH_SCRIPT), "--check", "--file", args.file]
    if args.content:
        publish_cmd.extend(["--content", args.content])
    if args.title:
        publish_cmd.extend(["--title", args.title])
    if args.author:
        publish_cmd.extend(["--author", args.author])
    if args.cover_image:
        publish_cmd.extend(["--cover-image", args.cover_image])
    if args.tail_image:
        publish_cmd.extend(["--tail-image", args.tail_image])
    for item in args.body_image or []:
        publish_cmd.extend(["--body-image", item])
    if args.body_image_placement:
        publish_cmd.extend(["--body-image-placement", args.body_image_placement])
    if args.max_body_images is not None:
        publish_cmd.extend(["--max-body-images", str(args.max_body_images)])
    if args.image_state:
        publish_cmd.extend(["--image-state", args.image_state])
    if args.strict_illustration:
        publish_cmd.append("--strict-illustration")
    if args.config:
        publish_cmd.extend(["--config", args.config])
    if args.asset_base_dir:
        publish_cmd.extend(["--asset-base-dir", args.asset_base_dir])
    if args.style_theme:
        publish_cmd.extend(["--style-theme", args.style_theme])
    if args.accent_color:
        publish_cmd.extend(["--accent-color", args.accent_color])

    publish_code, publish_payload = _run_json(publish_cmd)

    issues = []
    warnings = []
    conn_results = conn_payload.get("results") if isinstance(conn_payload, dict) else None
    valid_config_sources = set()
    if conn_results is not None:
        valid_config_sources = {item.get("config_source", "") for item in conn_results if item.get("ok")}
        if not valid_config_sources:
            issues.append("没有任何可用的公众号发布配置")
        if any((not item.get("ok")) for item in conn_results):
            warnings.append("存在失效配置，建议清理或显式指定可用配置")
    elif conn_code != 0:
        issues.append("公众号连接校核失败")

    cover_exists = _exists(args.cover_image)
    tail_exists = _exists(args.tail_image)
    body_image_exists = [item for item in [(_exists(src), src) for src in (args.body_image or [])] if item[0] is False]
    if cover_exists is False:
        issues.append("封面图不存在")
    if tail_exists is False:
        issues.append("尾图不存在")
    if body_image_exists:
        issues.append("存在正文图路径不存在")

    image_state = publish_payload.get("image_state") if isinstance(publish_payload, dict) else None
    inserted_body_images = publish_payload.get("inserted_body_images") if isinstance(publish_payload, dict) else []
    tail_image_src = publish_payload.get("tail_image_src") if isinstance(publish_payload, dict) else None
    selected_config_source = publish_payload.get("config_source") if isinstance(publish_payload, dict) else None
    image_sources = ((publish_payload.get("image_analysis") or {}).get("sources") or []) if isinstance(publish_payload, dict) else []
    if selected_config_source and valid_config_sources and selected_config_source not in valid_config_sources:
        issues.append("发布检查选中的配置并不是可用配置")
    if image_state == "article-specific" and not inserted_body_images:
        issues.append("image_state=article-specific，但没有实际正文图")
    if args.tail_image and tail_image_src and str(args.tail_image).strip() != str(tail_image_src).strip():
        issues.append("尾图来源与预期不一致")
    if args.tail_image:
        explicit_tail = str(args.tail_image).strip()
        default_tail_leftover = [
            item.get("src", "") for item in image_sources
            if "default-article-tail" in str(item.get("src", "")) and str(item.get("src", "")).strip() != explicit_tail
        ]
        if default_tail_leftover:
            issues.append("检测到默认尾图残留，与显式尾图同时存在")

    ok = conn_code == 0 and publish_code == 0 and not issues
    result = {
        "ok": ok,
        "connection_check": conn_payload,
        "publish_check": publish_payload,
        "asset_check": {
            "cover_image": {"path": args.cover_image or "", "exists": cover_exists},
            "tail_image": {"path": args.tail_image or "", "exists": tail_exists},
            "body_images": [
                {"path": src, "exists": _exists(src)} for src in (args.body_image or [])
            ],
        },
        "issues": issues,
        "warnings": warnings,
        "next_action": None if ok else "请先修复 issues 中的问题，再执行正式发布",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

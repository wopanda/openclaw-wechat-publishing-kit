#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Optional polish stage + publish to WeChat draft")
    parser.add_argument("--file", required=True, help="Markdown file path")
    parser.add_argument("--work-dir", help="Working directory for intermediate files")
    parser.add_argument("--cover-image", help="Cover image path")
    parser.add_argument("--thumb-media-id", help="Explicit thumb media id")
    parser.add_argument("--title", help="Explicit title")
    parser.add_argument("--author", help="Explicit author")
    parser.add_argument("--config", help="Path to config settings JSON or config directory")
    parser.add_argument("--style-theme", help="Override style theme (wechat-pro|cyan-clean|slate-blue)")
    parser.add_argument("--accent-color", help="Override accent color, e.g. #1f9d55")
    parser.add_argument("--check", action="store_true", help="Only preflight publish after polish")
    parser.add_argument("--polish-command", help="Override polish command template; supports {input} and {output}")
    parser.add_argument("--skip-polish", action="store_true", help="Skip polish stage")
    return parser.parse_args()


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, capture_output=True, text=True)


def main() -> int:
    args = parse_args()
    source = Path(args.file).resolve()
    if not source.exists():
        print(json.dumps({"ok": False, "error": f"输入文件不存在: {source}"}, ensure_ascii=False, indent=2))
        return 1

    work_dir = Path(args.work_dir).resolve() if args.work_dir else source.parent / '.wechat-publish-work'
    work_dir.mkdir(parents=True, exist_ok=True)
    polished = work_dir / f"{source.stem}.polished.md"

    polish_cmd = [sys.executable, str(SCRIPT_DIR / 'polish_markdown.py'), '--input', str(source), '--output', str(polished)]
    if args.config:
        polish_cmd.extend(['--config', args.config])
    if args.polish_command:
        polish_cmd.extend(['--command', args.polish_command])
    if args.skip_polish:
        polish_cmd.append('--copy-only')

    polish_proc = run_cmd(polish_cmd)
    publish_input = polished if polish_proc.returncode == 0 else source

    publish_cmd = [
        sys.executable,
        str(SCRIPT_DIR / 'publish_markdown.py'),
        '--file', str(publish_input),
        '--asset-base-dir', str(source.parent.parent if source.parent.name == 'output' else source.parent),
    ]
    if args.config:
        publish_cmd.extend(['--config', args.config])
    if args.cover_image:
        publish_cmd.extend(['--cover-image', args.cover_image])
    if args.thumb_media_id:
        publish_cmd.extend(['--thumb-media-id', args.thumb_media_id])
    if args.title:
        publish_cmd.extend(['--title', args.title])
    if args.author:
        publish_cmd.extend(['--author', args.author])
    if args.style_theme:
        publish_cmd.extend(['--style-theme', args.style_theme])
    if args.accent_color:
        publish_cmd.extend(['--accent-color', args.accent_color])
    if args.check:
        publish_cmd.append('--check')

    publish_proc = run_cmd(publish_cmd)

    result = {
        'ok': publish_proc.returncode == 0,
        'source_markdown': str(source),
        'publish_input': str(publish_input),
        'work_dir': str(work_dir),
        'polish': {
            'exit_code': polish_proc.returncode,
            'stdout': polish_proc.stdout,
            'stderr': polish_proc.stderr,
        },
        'publish': {
            'exit_code': publish_proc.returncode,
            'stdout': publish_proc.stdout,
            'stderr': publish_proc.stderr,
        }
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if publish_proc.returncode == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())

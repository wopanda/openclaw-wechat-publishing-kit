#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert a Feishu draft-pool record into a WeChat draft publish command")
    parser.add_argument("--record-json", required=True, help="Path to a normalized record JSON file")
    parser.add_argument("--doc-markdown", required=True, help="Path to raw markdown fetched from feishu preview doc")
    parser.add_argument("--output-dir", required=True, help="Directory to place prepared publish assets")
    parser.add_argument("--publisher-script", default=str(SCRIPT_DIR / "publish_markdown.py"))
    parser.add_argument("--prepare-script", default=str(SCRIPT_DIR / "prepare_feishu_doc_for_wechat.py"))
    parser.add_argument("--publish", action="store_true", help="Actually publish after preparing")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    record = load_json(Path(args.record_json))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    title = record.get("title", "未命名草稿")
    record_id = record.get("record_id", "unknown-record")
    prepared_md = output_dir / f"{record_id}-publish.md"

    subprocess.run(
        [
            sys.executable,
            args.prepare_script,
            "--input",
            args.doc_markdown,
            "--output",
            str(prepared_md),
            "--title",
            title,
        ],
        check=True,
    )

    command = [sys.executable, args.publisher_script, "--file", str(prepared_md)]

    cover_path = str(record.get("cover_asset_path", "")).strip()
    if cover_path:
        command.extend(["--cover-image", cover_path])

    result = {
        "ok": True,
        "record_id": record_id,
        "title": title,
        "prepared_markdown": str(prepared_md),
        "publish_command": command,
        "would_use_cover_image": cover_path or None,
    }

    if args.publish:
        publish_proc = subprocess.run(command, check=False, capture_output=True, text=True)
        result["publish_exit_code"] = publish_proc.returncode
        result["publish_stdout"] = publish_proc.stdout
        result["publish_stderr"] = publish_proc.stderr
        result["published_ok"] = publish_proc.returncode == 0

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

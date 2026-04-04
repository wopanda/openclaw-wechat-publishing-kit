#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Feishu preview markdown for WeChat publishing")
    parser.add_argument("--input", required=True, help="Raw markdown exported from feishu_fetch_doc")
    parser.add_argument("--output", required=True, help="Output markdown path for publish_markdown.py")
    parser.add_argument("--title", default="", help="Fallback title to prepend when body has no H1")
    return parser.parse_args()


def strip_callouts(text: str) -> str:
    while True:
        start = text.find("<callout")
        if start == -1:
            return text
        end = text.find("</callout>", start)
        if end == -1:
            return text
        text = text[:start] + text[end + len("</callout>"):]


def clean_feishu_markdown(raw_markdown: str, fallback_title: str = "") -> str:
    text = raw_markdown.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    text = strip_callouts(text).strip()

    marker = "\n---\n"
    if marker in text:
        prefix, body = text.split(marker, 1)
        prefix = prefix.strip()
        if any(token in prefix for token in ("当前状态", "来源素材", "本次处理")):
            text = body.strip()

    lines = text.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    text = "\n".join(lines).strip()

    if fallback_title and not text.startswith("# "):
        text = f"# {fallback_title.strip()}\n\n{text}".strip()

    return text + "\n"


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    raw_markdown = input_path.read_text(encoding="utf-8")
    cleaned = clean_feishu_markdown(raw_markdown, fallback_title=args.title)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(cleaned, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

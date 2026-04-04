#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Feishu preview markdown for WeChat publishing")
    parser.add_argument("--input", required=True, help="Raw markdown exported from feishu_fetch_doc")
    parser.add_argument("--output", required=True, help="Output markdown path for publish_markdown.py")
    parser.add_argument("--title", default="", help="Fallback title to prepend when body has no H1")
    parser.add_argument("--body-image", "--illustration", dest="body_images", action="append", default=[], help="Insert body illustration (repeatable)")
    parser.add_argument("--illustration-placement", choices=["after-intro", "before-ending"], default="before-ending", help="Where to place explicit illustrations")
    parser.add_argument("--max-body-images", type=int, default=1, help="Maximum number of inserted body images")
    parser.add_argument("--cover-image", default="", help="Optional cover image path; if same as body image, body insert is skipped")
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


def append_body_images(markdown_text: str, body_images: list[str], placement: str, max_body_images: int, exclude_sources: list[str]) -> tuple[str, dict]:
    requested: list[str] = []
    for src in body_images:
        item = str(src or "").strip()
        if item and item not in requested:
            requested.append(item)

    excluded = {str(src or "").strip() for src in exclude_sources if str(src or "").strip()}
    inserted: list[str] = []
    for src in requested:
        if src in excluded or src in markdown_text:
            continue
        inserted.append(src)
        if len(inserted) >= max(0, int(max_body_images)):
            break

    if not inserted:
        return markdown_text, {"requested": requested, "inserted": []}

    image_block = "\n\n".join(f"![]({src})" for src in inserted)
    body = (markdown_text or "").strip()
    if placement == "after-intro":
        blocks = body.split("\n\n") if body else []
        intro_index = None
        for index, block in enumerate(blocks):
            stripped = block.strip()
            if not stripped:
                continue
            if stripped.startswith("#") and "\n" not in stripped:
                continue
            intro_index = index
            break
        if intro_index is None:
            intro_index = max(0, len(blocks) - 1) if blocks else 0
        if blocks:
            blocks.insert(intro_index + 1, image_block)
            updated = "\n\n".join(part.strip("\n") for part in blocks if part is not None).strip() + "\n"
        else:
            updated = image_block + "\n"
    else:
        updated = body.rstrip() + "\n\n" + image_block + "\n" if body else image_block + "\n"

    return updated, {"requested": requested, "inserted": inserted}


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    raw_markdown = input_path.read_text(encoding="utf-8")
    cleaned = clean_feishu_markdown(raw_markdown, fallback_title=args.title)
    cleaned, _report = append_body_images(
        markdown_text=cleaned,
        body_images=args.body_images,
        placement=args.illustration_placement,
        max_body_images=max(0, int(args.max_body_images)),
        exclude_sources=[args.cover_image],
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(cleaned, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

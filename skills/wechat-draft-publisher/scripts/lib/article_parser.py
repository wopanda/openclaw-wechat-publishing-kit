from __future__ import annotations

import re
from pathlib import Path


ILLEGAL_FILENAME_CHARS = '<>:"/\\|?*'


IGNORE_HEADING_TITLES = {
    "文章信息",
    "标题候选",
}


AUTHOR_LINE_RE = re.compile(r"^[-*]\s*作者\s*[:：]\s*(.+?)\s*$")


def read_article(file_path: str | None, content: str | None) -> str:
    if file_path:
        return Path(file_path).read_text(encoding="utf-8")
    if content:
        return content
    raise ValueError("必须提供 --file 或 --content 其中之一")


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def looks_like_generated_wrapper(prefix: str) -> bool:
    normalized = normalize_newlines(prefix)
    for title in IGNORE_HEADING_TITLES:
        if f"# {title}" in normalized:
            return True
    return False


def extract_main_body(markdown_text: str) -> str:
    """提取真正正文。

    兼容旧生成稿格式：
    - # 文章信息
    - # 标题候选
    - ---
    - 正文

    如果不匹配该结构，则返回原文（strip 后）。
    """
    normalized = normalize_newlines(markdown_text).lstrip("\ufeff")
    marker = "\n---\n"

    if marker in normalized:
        prefix, suffix = normalized.split(marker, 1)
        if looks_like_generated_wrapper(prefix):
            return suffix.strip()

    return normalized.strip()


def strip_leading_h1(body_markdown: str, expected_title: str | None = None) -> str:
    body = normalize_newlines(body_markdown).strip()
    lines = body.splitlines()
    if not lines:
        return body

    first = lines[0].strip()
    if not first.startswith("# "):
        return body

    heading = first[2:].strip()
    if expected_title and heading != expected_title.strip():
        return body

    remaining = "\n".join(lines[1:]).lstrip("\n").strip()
    return remaining


def extract_title(markdown_text: str, explicit_title: str | None = None) -> str:
    if explicit_title and explicit_title.strip():
        return explicit_title.strip()[:64]

    body = extract_main_body(markdown_text)
    lines = body.splitlines()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("#"):
            candidate = stripped.lstrip("#").strip()
            return (candidate or "无标题")[:64]

        return stripped[:64]

    return "无标题"


def sanitize_title_for_filename(title: str) -> str:
    cleaned = title
    for ch in ILLEGAL_FILENAME_CHARS:
        cleaned = cleaned.replace(ch, "_")
    return cleaned.strip() or "无标题"


def detect_author(explicit_author: str | None, default_author: str | None, markdown_text: str | None = None) -> str:
    if explicit_author and explicit_author.strip():
        return explicit_author.strip()

    if markdown_text:
        normalized = normalize_newlines(markdown_text)
        marker = "\n---\n"
        prefix = normalized.split(marker, 1)[0] if marker in normalized else normalized
        for line in prefix.splitlines():
            match = AUTHOR_LINE_RE.match(line.strip())
            if match:
                author = match.group(1).strip()
                if author:
                    return author

    if default_author and default_author.strip():
        return default_author.strip()
    return ""

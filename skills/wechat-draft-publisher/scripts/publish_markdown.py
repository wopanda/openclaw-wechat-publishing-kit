#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
LIB_DIR = SCRIPT_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from article_parser import detect_author, extract_main_body, extract_title, read_article, strip_leading_h1
from config_loader import ConfigError, load_config
from image_compressor import ImageCompressor
from markdown_to_wechat import WeChatMarkdownFormatter, normalize_inline_images
from signature_builder import build_signature_block
from wechat_client import WeChatAPIError, WeChatClient


IMG_SRC_RE = re.compile(r'(<img[^>]+src=")(.+?)("[^>]*>)', flags=re.I)


class BodyImageUploadError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish Markdown to WeChat draft box")
    parser.add_argument("--file", dest="file_path", help="Markdown file path")
    parser.add_argument("--content", help="Inline markdown content")
    parser.add_argument("--title", help="Explicit title")
    parser.add_argument("--author", help="Explicit author")
    parser.add_argument("--thumb-media-id", help="Explicit thumb media id")
    parser.add_argument("--cover-image", help="Cover image file path (optional)")
    parser.add_argument("--tail-image", help="Tail image file path appended to the end of article body")
    parser.add_argument("--body-image", "--illustration", dest="body_image", action="append", help="Insert body illustration (repeatable, local path or URL)")
    parser.add_argument(
        "--body-image-placement", "--illustration-placement",
        dest="body_image_placement",
        choices=["after-intro", "before-ending", "after-first-h2", "before-signature"],
        help="Where to insert body illustrations (default: before-ending)",
    )
    parser.add_argument("--max-body-images", type=int, help="Maximum number of inserted body images")
    parser.add_argument(
        "--image-state", "--illustration-state",
        dest="image_state",
        choices=["article-specific", "fallback-approved", "text-only", "blocked-by-image"],
        help="Explicit image state reported in output",
    )
    parser.add_argument("--strict-illustration", action="store_true", help="Fail fast when image_state and body image availability conflict")
    parser.add_argument("--config", help="Path to config settings JSON or config directory")
    parser.add_argument("--asset-base-dir", help="Base directory for resolving relative local images")
    parser.add_argument("--style-theme", help="Override style theme (wechat-pro|cyan-clean|slate-blue)")
    parser.add_argument("--accent-color", help="Override accent color, e.g. #1f9d55")
    parser.add_argument("--dry-run", action="store_true", help="Validate and render only")
    parser.add_argument("--check", action="store_true", help="Preflight config and rendering without publish")
    parser.add_argument(
        "--check-images",
        action="store_true",
        help="Analyze body images, including local path resolution, without publishing",
    )
    return parser.parse_args()


def fail(message: str, **extra: object) -> int:
    payload = {"ok": False, "error": message}
    payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1


def append_signature_block(markdown_body: str, author: str, signature_template_path: str | None, title: str) -> tuple[str, dict]:
    info = build_signature_block(
        author=author,
        title=title,
        body=markdown_body,
        fallback_template_path=signature_template_path,
    )
    rendered = (info.get('text') or '').strip()
    if rendered and rendered not in markdown_body:
        body = markdown_body.rstrip()
        markdown_body = f"{body}\n\n---\n\n{rendered}\n"
    return markdown_body, info


def append_tail_image(markdown_body: str, tail_image_path: str | None) -> tuple[str, str | None]:
    src = (tail_image_path or '').strip()
    if not src:
        return markdown_body, None
    if src in markdown_body:
        return markdown_body, src
    body = markdown_body.rstrip()
    return f"{body}\n\n![]({src})\n", src


def normalize_image_list(values: object) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, list):
        return []

    normalized: list[str] = []
    seen = set()
    for item in values:
        src = str(item).strip()
        if not src or src in seen:
            continue
        seen.add(src)
        normalized.append(src)
    return normalized


def _insert_after_first_h2(markdown_body: str, image_block: str) -> str:
    lines = markdown_body.splitlines()
    for index, line in enumerate(lines):
        if line.strip().startswith("## "):
            insert_at = index + 1
            lines.insert(insert_at, "")
            lines.insert(insert_at + 1, image_block)
            lines.insert(insert_at + 2, "")
            return "\n".join(lines).strip() + "\n"
    body = markdown_body.rstrip()
    return f"{body}\n\n{image_block}\n"


def _insert_after_intro(markdown_body: str, image_block: str) -> str:
    blocks = markdown_body.strip().split("\n\n")
    if not blocks:
        return image_block.strip() + "\n"

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
        intro_index = min(len(blocks) - 1, 0)

    insert_at = intro_index + 1
    blocks.insert(insert_at, image_block.strip())
    return "\n\n".join(part.strip("\n") for part in blocks if part is not None).strip() + "\n"


def insert_body_images(markdown_body: str, body_images: list[str], placement: str, max_images: int) -> tuple[str, list[str]]:
    if max_images <= 0 or not body_images:
        return markdown_body, []

    selected: list[str] = []
    for src in body_images:
        if src in markdown_body:
            continue
        selected.append(src)
        if len(selected) >= max_images:
            break

    if not selected:
        return markdown_body, []

    image_block = "\n\n".join(f"![]({src})" for src in selected)
    if placement == "after-first-h2":
        return _insert_after_first_h2(markdown_body, image_block), selected
    if placement == "after-intro":
        return _insert_after_intro(markdown_body, image_block), selected

    body = markdown_body.rstrip()
    return f"{body}\n\n{image_block}\n", selected


def build_missing_cover_hint(body_image_report: dict) -> str:
    if body_image_report.get("unresolved_sources"):
        return (
            "缺少可用封面：当前文章没有可自动作为封面的已上传图片，且这些图片路径未解析/上传成功。"
            "请改成正确的本地路径，或显式提供 --cover-image / --thumb-media-id，"
            "或在配置中设置 default_thumb_media_id"
        )
    return (
        "缺少可用封面：请显式提供 --cover-image 或 --thumb-media-id，"
        "或在配置中设置 default_thumb_media_id，"
        "或在正文中加入至少一张可访问的图片供自动取首图封面"
    )


def resolve_local_image(src: str, article_file: Optional[Path], asset_base_dir: Optional[Path] = None) -> Optional[Path]:
    if src.startswith(("http://", "https://")):
        return None

    candidates = []
    raw = Path(src)
    raw_str = src.replace('\\', '/').lstrip('./')

    if asset_base_dir is not None:
        candidates.append((asset_base_dir / raw).resolve())
        if raw_str.startswith('output/'):
            trimmed = Path(raw_str[len('output/'):])
            candidates.append((asset_base_dir / trimmed).resolve())

    if article_file is not None:
        parent = article_file.parent
        candidates.append((parent / raw).resolve())
        candidates.append((parent.parent / raw).resolve())
        if raw_str.startswith('output/'):
            trimmed = Path(raw_str[len('output/'):])
            candidates.append((parent / trimmed).resolve())
            candidates.append((parent.parent / trimmed).resolve())

    candidates.append(Path(src).expanduser().resolve())

    seen = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def classify_image_sources(markdown_body: str, article_file: Optional[Path], asset_base_dir: Optional[Path] = None) -> dict:
    normalized_body = normalize_inline_images(markdown_body)
    matches = list(IMG_SRC_RE.finditer(normalized_body))
    sources = []
    for index, match in enumerate(matches, start=1):
        src = match.group(2).strip()
        if not src:
            continue
        if src.startswith(("http://", "https://")):
            kind = "remote"
            resolved_path = None
            exists = None
        else:
            resolved = resolve_local_image(src, article_file=article_file, asset_base_dir=asset_base_dir)
            kind = "local"
            resolved_path = str(resolved) if resolved else None
            exists = resolved is not None
        sources.append(
            {
                "index": index,
                "src": src,
                "kind": kind,
                "resolved_path": resolved_path,
                "exists": exists,
            }
        )

    return {
        "normalized_body": normalized_body,
        "sources": sources,
        "found_image_count": len(sources),
        "local_image_count": sum(1 for item in sources if item["kind"] == "local"),
        "remote_image_count": sum(1 for item in sources if item["kind"] == "remote"),
        "unresolved_local_image_count": sum(1 for item in sources if item["kind"] == "local" and not item["exists"]),
    }


async def fetch_remote_image_bytes(url: str, timeout_seconds: int, max_bytes: int = 10 * 1024 * 1024) -> bytes:
    async with httpx.AsyncClient(timeout=float(timeout_seconds), follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        content = response.content
    if len(content) > max_bytes:
        raise BodyImageUploadError(f"远程图片过大，超过 {max_bytes // (1024 * 1024)}MB: {url}")
    return content


async def upload_body_images(
    markdown_body: str,
    article_file: Optional[Path],
    client: WeChatClient,
    asset_base_dir: Optional[Path] = None,
    upload_remote_images: bool = True,
    exclude_auto_cover_src: Optional[str] = None,
) -> Tuple[str, Optional[str], dict]:
    src_to_url: dict[str, str] = {}
    src_to_media: dict[str, str] = {}
    unresolved: list[str] = []
    uploaded: list[str] = []
    remote_uploaded: list[str] = []
    remote_passthrough: list[str] = []
    failures: list[dict[str, str]] = []

    normalized_body = normalize_inline_images(markdown_body)
    matches = list(IMG_SRC_RE.finditer(normalized_body))
    if not matches:
        return markdown_body, None, {
            "found_image_count": 0,
            "uploaded_image_count": 0,
            "uploaded_sources": uploaded,
            "remote_uploaded_sources": remote_uploaded,
            "passthrough_remote_sources": remote_passthrough,
            "unresolved_sources": unresolved,
            "failed_uploads": failures,
        }

    compressor = ImageCompressor()

    for match in matches:
        src = match.group(2).strip()
        if not src or src in src_to_url:
            continue

        try:
            if src.startswith(("http://", "https://")):
                if not upload_remote_images:
                    src_to_url[src] = src
                    remote_passthrough.append(src)
                    continue
                remote_bytes = await fetch_remote_image_bytes(src, timeout_seconds=int(client.timeout_seconds))
                upload_bytes, upload_name = compressor.compress_for_wechat_upload(remote_bytes, filename=Path(src.split("?", 1)[0]).name or "remote-image.jpg")
                upload_result = await client.upload_image(upload_bytes, filename=upload_name)
                url = upload_result.get("url", "")
                media_id = upload_result.get("media_id", "")
                if url:
                    src_to_url[src] = url
                    uploaded.append(src)
                    remote_uploaded.append(src)
                else:
                    src_to_url[src] = src
                    remote_passthrough.append(src)
                    failures.append({"src": src, "reason": "微信返回了空 url"})
                if media_id:
                    src_to_media[src] = media_id
                continue

            local_path = resolve_local_image(src, article_file=article_file, asset_base_dir=asset_base_dir)
            if local_path is None:
                unresolved.append(src)
                failures.append({"src": src, "reason": "本地图片路径未解析成功"})
                continue

            upload_bytes, upload_name = compressor.compress_for_wechat_upload(local_path.read_bytes(), filename=local_path.name)
            upload_result = await client.upload_image(upload_bytes, filename=upload_name)
            url = upload_result.get("url", "")
            media_id = upload_result.get("media_id", "")
            if url:
                src_to_url[src] = url
                uploaded.append(src)
            else:
                unresolved.append(src)
                failures.append({"src": src, "reason": "微信返回了空 url"})
            if media_id:
                src_to_media[src] = media_id
        except (httpx.HTTPError, BodyImageUploadError, WeChatAPIError, ValueError) as exc:
            if src.startswith(("http://", "https://")):
                src_to_url[src] = src
                remote_passthrough.append(src)
                failures.append({"src": src, "reason": str(exc)})
            else:
                unresolved.append(src)
                failures.append({"src": src, "reason": str(exc)})

    def repl(match: re.Match[str]) -> str:
        pre, src, post = match.group(1), match.group(2).strip(), match.group(3)
        return f'{pre}{src_to_url.get(src, src)}{post}'

    replaced = IMG_SRC_RE.sub(repl, normalized_body)

    auto_cover_media_id = None
    for match in matches:
        src = match.group(2).strip()
        if exclude_auto_cover_src and src == exclude_auto_cover_src:
            continue
        if src in src_to_media:
            auto_cover_media_id = src_to_media[src]
            break

    return replaced, auto_cover_media_id, {
        "found_image_count": len(matches),
        "uploaded_image_count": len(uploaded),
        "uploaded_sources": uploaded,
        "remote_uploaded_sources": remote_uploaded,
        "passthrough_remote_sources": remote_passthrough,
        "unresolved_sources": unresolved,
        "failed_uploads": failures,
    }


def persist_publish_receipt(config: dict, payload: dict, article_file: Optional[Path]) -> str | None:
    output_dir_value = config.get("output_dir")
    if not output_dir_value:
        return None

    out_dir = Path(str(output_dir_value)).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_title = re.sub(r"[^\w\-\u4e00-\u9fff]+", "-", (payload.get("title") or "untitled").strip())
    safe_title = re.sub(r"-{2,}", "-", safe_title).strip("-")[:80] or "untitled"
    receipt_path = out_dir / f"{timestamp}-{safe_title}-draft-receipt.json"

    receipt_payload = dict(payload)
    receipt_payload["receipt_saved_at"] = datetime.now().isoformat(timespec="seconds")
    receipt_payload["receipt_path"] = str(receipt_path)
    receipt_payload["source_markdown"] = str(article_file) if article_file else ""

    receipt_path.write_text(json.dumps(receipt_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(receipt_path)


async def main() -> int:
    args = parse_args()

    try:
        config = load_config(args.config)
        markdown_text = read_article(args.file_path, args.content)
    except (ConfigError, FileNotFoundError, ValueError) as exc:
        return fail(str(exc))

    article_file = Path(args.file_path).resolve() if args.file_path else None
    asset_base_dir = Path(args.asset_base_dir).expanduser().resolve() if args.asset_base_dir else None
    article_body = extract_main_body(markdown_text)
    title = extract_title(markdown_text, args.title)
    article_body = strip_leading_h1(article_body, expected_title=title)
    author = detect_author(args.author, config.get("default_author"), markdown_text)

    cover_image_hint = (args.cover_image or "").strip()
    tail_image_hint = (args.tail_image or config.get("default_tail_image_path", "") or "").strip()
    cli_body_images = normalize_image_list(args.body_image)
    cfg_body_images = normalize_image_list(config.get("default_body_images"))
    body_image_input_strategy = "cli" if cli_body_images else ("config-default" if cfg_body_images else "none")
    requested_body_images = [
        src
        for src in (cli_body_images + [item for item in cfg_body_images if item not in cli_body_images])
        if src not in {cover_image_hint, tail_image_hint}
    ]

    raw_max_body_images = args.max_body_images if args.max_body_images is not None else config.get("max_body_images", 1)
    try:
        max_body_images = max(0, int(raw_max_body_images))
    except (TypeError, ValueError):
        max_body_images = 1

    strict_illustration = bool(args.strict_illustration or config.get("strict_illustration", False))

    body_image_placement = (args.body_image_placement or config.get("body_image_placement") or "before-ending").strip()
    if body_image_placement == "before-ending":
        body_image_placement = "before-signature"
    elif body_image_placement not in {"after-first-h2", "before-signature", "after-intro"}:
        body_image_placement = "before-signature"

    article_body, inserted_body_images = insert_body_images(
        markdown_body=article_body,
        body_images=requested_body_images,
        placement=body_image_placement,
        max_images=max_body_images,
    )

    article_body, signature_info = append_signature_block(
        article_body,
        author,
        config.get("default_signature_template_path", ""),
        title,
    )
    tail_image = (args.tail_image or config.get("default_tail_image_path", "") or "").strip()
    article_body, tail_image_src = append_tail_image(article_body, tail_image)
    theme_name = args.style_theme or config.get("style_theme", "wechat-pro")
    accent_color = args.accent_color or config.get("accent_color")
    formatter = WeChatMarkdownFormatter(theme=theme_name, accent_color=accent_color)
    content_html = formatter.format(article_body) if config.get("format_markdown", True) else article_body

    explicit_thumb = (args.thumb_media_id or "").strip()
    default_thumb = (config.get("default_thumb_media_id", "") or "").strip()
    cover_image = (args.cover_image or "").strip()

    thumb_media_id = explicit_thumb
    if explicit_thumb:
        cover_strategy = "explicit-thumb-media-id"
    elif cover_image:
        cover_strategy = "cover-image-upload"
    elif default_thumb:
        thumb_media_id = default_thumb
        cover_strategy = "default-thumb-media-id"
    else:
        cover_strategy = "auto-first-body-image-or-missing"

    used_default_thumb = bool((not explicit_thumb) and (not cover_image) and default_thumb)

    image_state = (args.image_state or config.get("default_image_state") or "").strip()
    if image_state not in {"article-specific", "fallback-approved", "text-only", "blocked-by-image"}:
        image_state = "article-specific" if inserted_body_images else "text-only"

    image_analysis = classify_image_sources(article_body, article_file=article_file, asset_base_dir=asset_base_dir)
    preview_image_count = image_analysis["found_image_count"]
    cover_candidate_count = sum(1 for item in image_analysis["sources"] if item["src"] != tail_image_src)

    has_any_body_images = cover_candidate_count > 0
    if image_state == "article-specific" and not has_any_body_images:
        image_state = "text-only"

    disclosure_required = image_state == "fallback-approved"
    used_fallback_body_images = bool(image_state == "fallback-approved" and inserted_body_images)
    if strict_illustration and image_state != "text-only" and not has_any_body_images:
        return fail(
            "当前要求严格插图，但正文里没有可用插图",
            title=title,
            author=author,
            image_state=image_state,
            next_action="请补 --body-image/--illustration，或把 image_state 改成 text-only",
        )

    if args.check or args.dry_run or args.check_images:
        next_action = None
        if image_state == "blocked-by-image":
            next_action = "当前 image_state=blocked-by-image：按发布门禁应先修复配图，再进入草稿箱"
        elif not explicit_thumb and not default_thumb and not cover_image and cover_candidate_count == 0:
            next_action = "请提供 --cover-image 或 --thumb-media-id，或在配置中设置 default_thumb_media_id；否则微信大概率会因缺少有效封面而拒绝发布"
        elif image_analysis["unresolved_local_image_count"] > 0:
            next_action = "存在未解析成功的本地图片路径，请先修正图片路径，或改用 --asset-base-dir 指定素材根目录"

        print(json.dumps({
            "ok": True,
            "mode": "check-images" if args.check_images else ("check" if args.check else "dry-run"),
            "title": title,
            "author": author,
            "config_source": config.get("config_source", "unknown"),
            "config_format": config.get("config_format", "unknown"),
            "cover_strategy": cover_strategy,
            "thumb_media_id": thumb_media_id,
            "used_default_thumb_media_id": used_default_thumb,
            "style_theme": theme_name,
            "accent_color": accent_color,
            "format_markdown": bool(config.get("format_markdown", True)),
            "weixin_api_base": config.get("weixin_api_base", "https://api.weixin.qq.com"),
            "request_timeout_seconds": int(config.get("request_timeout_seconds", 30)),
            "body_chars": len(article_body),
            "html_preview_chars": len(content_html),
            "body_image_count": preview_image_count,
            "cover_candidate_image_count": cover_candidate_count,
            "body_image_placement": body_image_placement,
            "max_body_images": max_body_images,
            "strict_illustration": strict_illustration,
            "requested_body_images": requested_body_images,
            "inserted_body_images": inserted_body_images,
            "body_image_input_strategy": body_image_input_strategy,
            "image_state": image_state,
            "disclosure_required": disclosure_required,
            "used_fallback_body_images": used_fallback_body_images,
            "signature_template_src": signature_info.get("source"),
            "signature_strategy": signature_info.get("strategy"),
            "signature_variant": signature_info.get("variant"),
            "signature_appended": bool(signature_info.get("text")),
            "tail_image_src": tail_image_src,
            "tail_image_appended": bool(tail_image_src),
            "image_analysis": {
                "found_image_count": image_analysis["found_image_count"],
                "local_image_count": image_analysis["local_image_count"],
                "remote_image_count": image_analysis["remote_image_count"],
                "unresolved_local_image_count": image_analysis["unresolved_local_image_count"],
                "sources": image_analysis["sources"],
            },
            "next_action": next_action,
        }, ensure_ascii=False, indent=2))
        return 0

    if image_state == "blocked-by-image":
        return fail(
            "当前配图状态为 blocked-by-image，按门禁不继续推进草稿箱",
            title=title,
            author=author,
            image_state=image_state,
            next_action="请先修复专属配图或改为 text-only / fallback-approved 后再发布",
        )

    appid = config.get("wechat_appid", "")
    secret = config.get("wechat_secret", "")
    if not appid or not secret:
        return fail("缺少微信配置：wechat_appid / wechat_secret", config_source=config.get("config_source", "unknown"))

    client = WeChatClient(
        appid=appid,
        secret=secret,
        api_base=config.get("weixin_api_base", "https://api.weixin.qq.com"),
        timeout_seconds=int(config.get("request_timeout_seconds", 30)),
    )
    upload_remote_images = bool(config.get("upload_remote_images", True))

    auto_cover_media_id = None
    image_report = {
        "found_image_count": 0,
        "uploaded_image_count": 0,
        "uploaded_sources": [],
        "remote_uploaded_sources": [],
        "passthrough_remote_sources": [],
        "unresolved_sources": [],
        "failed_uploads": [],
    }

    try:
        body_with_remote_images, auto_cover_media_id, image_report = await upload_body_images(
            markdown_body=article_body,
            article_file=article_file,
            client=client,
            asset_base_dir=asset_base_dir,
            upload_remote_images=upload_remote_images,
            exclude_auto_cover_src=tail_image_src,
        )

        content_html = formatter.format(body_with_remote_images) if config.get("format_markdown", True) else body_with_remote_images

        if not thumb_media_id and cover_image:
            cover_path = Path(cover_image).expanduser().resolve()
            if not cover_path.exists():
                return fail(f"封面图不存在: {cover_path}", title=title, author=author)
            compressor = ImageCompressor()
            compressed = compressor.compress(cover_path.read_bytes(), max_size_kb=64)
            upload_result = await client.upload_image(compressed, filename=f"{cover_path.stem or 'cover'}.jpg")
            thumb_media_id = upload_result.get("media_id", "")
            cover_strategy = "cover-image-upload"

        if not thumb_media_id and auto_cover_media_id:
            thumb_media_id = auto_cover_media_id
            cover_strategy = "auto-first-body-image"

        result = await client.add_draft(
            title=title,
            author=author,
            content_html=content_html,
            thumb_media_id=thumb_media_id,
        )
    except WeChatAPIError as exc:
        error_message = str(exc)
        if "errcode=40007" in error_message and not thumb_media_id:
            return fail(
                error_message,
                title=title,
                author=author,
                cover_strategy=cover_strategy,
                image_report=image_report,
                next_action=build_missing_cover_hint(image_report),
            )
        return fail(str(exc), title=title, author=author)
    except Exception as exc:  # noqa: BLE001
        return fail(f"发布时出现未预期错误: {exc}", title=title, author=author)
    finally:
        await client.close()

    payload = {
        "ok": True,
        "title": title,
        "author": author,
        "config_source": config.get("config_source", "unknown"),
        "config_format": config.get("config_format", "unknown"),
        "cover_strategy": cover_strategy,
        "thumb_media_id": thumb_media_id,
        "used_default_thumb_media_id": used_default_thumb,
        "style_theme": theme_name,
        "accent_color": accent_color,
        "body_image_placement": body_image_placement,
        "max_body_images": max_body_images,
        "strict_illustration": strict_illustration,
        "requested_body_images": requested_body_images,
        "inserted_body_images": inserted_body_images,
        "body_image_input_strategy": body_image_input_strategy,
        "image_state": image_state,
        "disclosure_required": disclosure_required,
        "used_fallback_body_images": used_fallback_body_images,
        "signature_template_src": signature_info.get("source"),
        "signature_strategy": signature_info.get("strategy"),
        "signature_variant": signature_info.get("variant"),
        "signature_appended": bool(signature_info.get("text")),
        "tail_image_src": tail_image_src,
        "tail_image_appended": bool(tail_image_src),
        "auto_cover_media_id": auto_cover_media_id,
        "image_report": image_report,
        "media_id": result.get("media_id", ""),
        "draft_id": result.get("draft_id", result.get("media_id", "")),
        "draft_url": result.get("draft_url", "https://mp.weixin.qq.com/"),
        "raw": result.get("raw", result),
    }
    receipt_path = persist_publish_receipt(config=config, payload=payload, article_file=article_file)
    if receipt_path:
        payload["receipt_path"] = receipt_path
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

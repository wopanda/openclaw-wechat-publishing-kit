from __future__ import annotations

import html
import re
from pathlib import Path

import markdown


OBSIDIAN_IMAGE_PATTERN = re.compile(r"!\[\[(.*?)\]\]")
MARKDOWN_IMAGE_PATTERN = re.compile(r'!\[(?P<alt>[^\]]*)\]\((?P<src>[^)\s]+)(?:\s+"(?P<title>[^"]*)")?\)')
# Feishu markdown export uses <image url="..." /> tags (not standard HTML <img />)
FEISHU_IMAGE_PATTERN = re.compile(r'<image[^>]*\burl=["\'](?P<url>[^"\']+)["\'][^>]*/?>', re.IGNORECASE)
CODE_SPAN_OR_FENCE_PATTERN = re.compile(r'(```.*?```|`[^`\n]+`)', re.DOTALL)

LIST_BLOCK_PATTERN = re.compile(r'<(?P<tag>ul|ol)>(?P<body>.*?)</(?P=tag)>', re.IGNORECASE | re.DOTALL)
LIST_ITEM_PATTERN = re.compile(r'<li>(.*?)</li>', re.IGNORECASE | re.DOTALL)

THEMES = {
    "wechat-pro": {
        "body": "#2f3441",
        "muted": "#5f6b7a",
        "accent": "#1f9d55",
        "heading": "#16202a",
        "quote_bg": "#f4fbf6",
        "quote_border": "#72c690",
        "code_bg": "#0f1720",
        "code_fg": "#d7fbe8",
        "inline_code_bg": "#f3f5f7",
        "inline_code_fg": "#0f5132",
        "hr": "#b7e4c7",
        "link": "#157347",
        "table_head_bg": "#f4fbf6",
        "table_border": "#d9e8df",
        "image_radius": "12px",
    },
    "cyan-clean": {
        "body": "#11324d",
        "muted": "#36566f",
        "accent": "#2d6f91",
        "heading": "#0a2236",
        "quote_bg": "#eaf7fb",
        "quote_border": "#7eb6d1",
        "code_bg": "#0a2236",
        "code_fg": "#c6f3ff",
        "inline_code_bg": "#edf7fb",
        "inline_code_fg": "#0f4c75",
        "hr": "#b7d9e8",
        "link": "#1f6f8b",
        "table_head_bg": "#eef8fb",
        "table_border": "#d7e7ef",
        "image_radius": "10px",
    },
    "slate-blue": {
        "body": "#2d3748",
        "muted": "#5a6475",
        "accent": "#3b82f6",
        "heading": "#1f2a37",
        "quote_bg": "#f5f8ff",
        "quote_border": "#8fb3ff",
        "code_bg": "#111827",
        "code_fg": "#dbeafe",
        "inline_code_bg": "#eef2f7",
        "inline_code_fg": "#1e40af",
        "hr": "#d7e3ff",
        "link": "#2563eb",
        "table_head_bg": "#f5f8ff",
        "table_border": "#dde5f4",
        "image_radius": "12px",
    },
}


class WeChatMarkdownFormatter:
    def __init__(self, theme: str = "wechat-pro", accent_color: str | None = None):
        self.theme_name = theme if theme in THEMES else "wechat-pro"
        self.theme = dict(THEMES[self.theme_name])
        if accent_color:
            self.theme["accent"] = accent_color

    def format(self, content: str) -> str:
        html_text = markdown_to_wechat_html(content)
        return _apply_theme_styles(html_text, self.theme)


def normalize_inline_images(text: str) -> str:
    normalized = _replace_feishu_images(text)
    normalized = _replace_obsidian_images(normalized)
    normalized = _normalize_markdown_images(normalized)
    return normalized


def _build_image_tag(src: str, alt: str = "", title: str = "") -> str:
    attrs = [f'src="{html.escape(src, quote=True)}"']
    if alt:
        attrs.append(f'alt="{html.escape(alt, quote=True)}"')
    if title:
        attrs.append(f'title="{html.escape(title, quote=True)}"')
    return f'<img {" ".join(attrs)} />'


def _replace_feishu_images(text: str) -> str:
    placeholders: dict[str, str] = {}

    def protect(match: re.Match[str]) -> str:
        key = f"__CODE_SPAN_{len(placeholders)}__"
        placeholders[key] = match.group(0)
        return key

    protected = CODE_SPAN_OR_FENCE_PATTERN.sub(protect, text)

    def repl(match: re.Match[str]) -> str:
        src = (match.group("url") or "").strip()
        if not src:
            return ""
        alt = Path(src.split("?", 1)[0]).stem or "image"
        return "\n\n" + _build_image_tag(src=src, alt=alt) + "\n\n"

    replaced = FEISHU_IMAGE_PATTERN.sub(repl, protected)
    for key, original in placeholders.items():
        replaced = replaced.replace(key, original)
    return replaced


def _replace_obsidian_images(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        target = match.group(1).strip()
        parts = [part.strip() for part in target.split("|")]
        src = parts[0] if parts else target
        alt = parts[1] if len(parts) > 1 else Path(src).stem

        if src.startswith(("http://", "https://")):
            return "\n\n" + _build_image_tag(src=src, alt=alt) + "\n\n"
        if any(src.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg")):
            return "\n\n" + _build_image_tag(src=src, alt=alt) + "\n\n"
        return f"\n> [图片占位：{target}]\n"

    return OBSIDIAN_IMAGE_PATTERN.sub(repl, text)


def _normalize_markdown_images(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        alt = (match.group("alt") or "").strip()
        src = (match.group("src") or "").strip()
        title = (match.group("title") or "").strip()
        return _build_image_tag(src=src, alt=alt, title=title)

    return MARKDOWN_IMAGE_PATTERN.sub(repl, text)


def _flatten_list_item_html(content: str) -> str:
    flattened = content.strip()
    flattened = re.sub(r'^\s*<p>\s*', '', flattened, flags=re.IGNORECASE)
    flattened = re.sub(r'\s*</p>\s*$', '', flattened, flags=re.IGNORECASE)
    flattened = re.sub(r'</p>\s*<p>', '<br/>', flattened, flags=re.IGNORECASE)
    return flattened.strip()


def _render_list_block(match: re.Match[str]) -> str:
    tag = match.group('tag').lower()
    body = match.group('body')
    items = LIST_ITEM_PATTERN.findall(body)
    rendered = []
    for idx, item in enumerate(items, start=1):
        prefix = '•' if tag == 'ul' else f'{idx}.'
        rendered.append(f'<p data-oc-list="{tag}" data-oc-index="{idx}">{prefix} {_flatten_list_item_html(item)}</p>')
    return '\n'.join(rendered)


def _convert_html_lists_to_paragraphs(html_text: str) -> str:
    previous = None
    current = html_text
    while previous != current:
        previous = current
        current = LIST_BLOCK_PATTERN.sub(_render_list_block, current)
    return current


def markdown_to_wechat_html(markdown_text: str) -> str:
    normalized = normalize_inline_images(markdown_text)
    html_text = markdown.markdown(
        normalized,
        extensions=["extra", "sane_lists", "tables", "nl2br", "fenced_code"],
        output_format="html5",
    )
    return _convert_html_lists_to_paragraphs(html_text)


def _style_img_tags(html_text: str, theme: dict) -> str:
    radius = theme["image_radius"]
    return re.sub(
        r'<img(?![^>]*\bstyle=)([^>]*?)(/?)>',
        f'<img\\1 style="display:block;max-width:100%;width:100%;border-radius:{radius};margin:18px auto;"\\2>',
        html_text,
        flags=re.IGNORECASE,
    )


def _apply_theme_styles(html_text: str, theme: dict) -> str:
    html_text = re.sub(r"<script[^>]*>.*?</script>", "", html_text, flags=re.DOTALL | re.IGNORECASE)
    html_text = _style_img_tags(html_text, theme)

    replacements = [
        (r"<h1>(.*?)</h1>", f'<h1 style="font-size:26px;line-height:1.45;font-weight:800;margin:10px 0 22px;text-align:center;color:{theme["heading"]};letter-spacing:0.02em;">\\1</h1>'),
        (r"<h2>(.*?)</h2>", f'<h2 style="font-size:20px;line-height:1.45;font-weight:700;margin:18px 0 6px;padding-left:10px;border-left:4px solid {theme["accent"]};color:{theme["heading"]};">\\1</h2>'),
        (r"<h3>(.*?)</h3>", f'<h3 style="font-size:17px;line-height:1.45;font-weight:700;margin:14px 0 4px;color:{theme["accent"]};">\\1</h3>'),
        (r'<p([^>]*)data-oc-list="(ul|ol)"([^>]*)>(.*?)</p>', f'<p\\1data-oc-list="\\2"\\3 style="font-size:15px;line-height:1.86;letter-spacing:0.03em;margin:0;padding:4px 0 4px 1.2em;color:{theme["body"]};text-align:left;word-break:break-word;">\\4</p>'),
        (r"<p(?![^>]*data-oc-list)(?![^>]*style=)([^>]*)>(.*?)</p>", f'<p\\1 style="font-size:15px;line-height:1.86;letter-spacing:0.03em;margin:0;padding:6px 0;color:{theme["body"]};text-align:justify;word-break:break-word;">\\2</p>'),
        (r"<blockquote>(.*?)</blockquote>", f'<blockquote style="border-left:4px solid {theme["quote_border"]};background:{theme["quote_bg"]};padding:10px 14px;margin:16px 0;border-radius:8px;color:{theme["muted"]};">\\1</blockquote>'),
        (r"<ul>(.*?)</ul>", '<ul style="margin:8px 0;padding:0 0 0 24px;list-style-position:outside;">\\1</ul>'),
        (r"<ol>(.*?)</ol>", '<ol style="margin:8px 0;padding:0 0 0 24px;list-style-position:outside;">\\1</ol>'),
        (r"<li>(.*?)</li>", f'<li style="display:list-item;margin:6px 0;line-height:1.85;color:{theme["body"]};">\\1</li>'),
        (r"<hr ?/?>", f'<hr style="border:none;border-top:1px solid {theme["hr"]};margin:24px 0;" />'),
        (r"<table>(.*?)</table>", f'<table style="width:100%;border-collapse:collapse;margin:16px 0;font-size:14px;line-height:1.7;color:{theme["body"]};">\\1</table>'),
        (r"<thead>(.*?)</thead>", f'<thead style="background:{theme["table_head_bg"]};">\\1</thead>'),
        (r"<th>(.*?)</th>", f'<th style="border:1px solid {theme["table_border"]};padding:8px 10px;text-align:left;font-weight:700;color:{theme["heading"]};">\\1</th>'),
        (r"<td>(.*?)</td>", f'<td style="border:1px solid {theme["table_border"]};padding:8px 10px;vertical-align:top;">\\1</td>'),
        (r"<pre><code>(.*?)</code></pre>", f'<pre style="background:{theme["code_bg"]};color:{theme["code_fg"]};padding:14px 16px;border-radius:10px;overflow-x:auto;font-size:13px;line-height:1.7;margin:16px 0;"><code>\\1</code></pre>'),
        (r"<code>(.*?)</code>", f'<code style="background:{theme["inline_code_bg"]};color:{theme["inline_code_fg"]};padding:2px 6px;border-radius:6px;font-size:0.92em;">\\1</code>'),
        (r"<a href=\"(.*?)\">(.*?)</a>", f'<a href="\\1" style="color:{theme["link"]};text-decoration:none;border-bottom:1px solid {theme["accent"]};">\\2</a>'),
        (r"<strong>(.*?)</strong>", f'<strong style="color:{theme["accent"]};font-weight:700;">\\1</strong>'),
        (r"<em>(.*?)</em>", f'<em style="color:{theme["muted"]};font-style:italic;">\\1</em>'),
    ]

    for pattern, replacement in replacements:
        html_text = re.sub(pattern, replacement, html_text, flags=re.DOTALL | re.IGNORECASE)

    return (
        f'<section style="font-family:Optima,\'PingFang SC\',\'Microsoft YaHei\',sans-serif;font-size:16px;line-height:1.85;color:{theme["body"]};word-break:break-word;overflow-wrap:break-word;">'
        + html_text
        + '</section>'
    )

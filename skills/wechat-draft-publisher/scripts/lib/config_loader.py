from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List


DEFAULTS: Dict[str, Any] = {
    "default_author": "日新",
    "default_thumb_media_id": "",
    "default_cover_image_path": "",
    "default_tail_image_path": "",
    "default_signature_template_path": "",
    "default_body_images": [],
    "max_body_images": 1,
    "body_image_placement": "before-ending",
    "default_image_state": "text-only",
    "weixin_api_base": "https://api.weixin.qq.com",
    "format_markdown": True,
    "request_timeout_seconds": 30,
    "upload_remote_images": True,
    "style_theme": "wechat-pro",
    "accent_color": "#1f9d55",
    "strict_illustration": False,
}


class ConfigError(RuntimeError):
    pass


def _skill_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"配置文件 JSON 解析失败: {path}: {exc}") from exc


def _is_split_config_dir(path: Path) -> bool:
    return path.is_dir() and ((path / "settings.json").exists() or (path / "credentials.json").exists())


def _load_split_config(config_dir: Path) -> Dict[str, Any]:
    settings_file = config_dir / "settings.json"
    credentials_file = config_dir / "credentials.json"

    if not settings_file.exists() and not credentials_file.exists():
        raise ConfigError(f"配置目录中未找到 settings.json / credentials.json: {config_dir}")

    settings = _read_json(settings_file) if settings_file.exists() else {}
    credentials = _read_json(credentials_file) if credentials_file.exists() else {}

    merged = dict(DEFAULTS)
    merged.update(
        {
            "default_author": settings.get("author", DEFAULTS["default_author"]),
            "default_thumb_media_id": settings.get("default_thumb_media_id", DEFAULTS["default_thumb_media_id"]),
            "default_cover_image_path": settings.get("default_cover_image_path", DEFAULTS["default_cover_image_path"]),
            "default_tail_image_path": settings.get("default_tail_image_path", DEFAULTS["default_tail_image_path"]),
            "default_signature_template_path": settings.get("default_signature_template_path", DEFAULTS["default_signature_template_path"]),
            "output_dir": settings.get("output_dir"),
            "server_ip": settings.get("server_ip"),
            "use_custom_prompts": settings.get("use_custom_prompts", False),
            "default_body_images": settings.get("default_body_images", DEFAULTS["default_body_images"]),
            "max_body_images": settings.get("max_body_images", DEFAULTS["max_body_images"]),
            "body_image_placement": settings.get("body_image_placement", DEFAULTS["body_image_placement"]),
            "default_image_state": settings.get("default_image_state", DEFAULTS["default_image_state"]),
            "weixin_api_base": settings.get("weixin_api_base", DEFAULTS["weixin_api_base"]),
            "format_markdown": settings.get("format_markdown", DEFAULTS["format_markdown"]),
            "request_timeout_seconds": settings.get("request_timeout_seconds", DEFAULTS["request_timeout_seconds"]),
            "upload_remote_images": settings.get("upload_remote_images", DEFAULTS["upload_remote_images"]),
            "style_theme": settings.get("style_theme", DEFAULTS["style_theme"]),
            "accent_color": settings.get("accent_color", DEFAULTS["accent_color"]),
            "strict_illustration": settings.get("strict_illustration", DEFAULTS["strict_illustration"]),
            "wechat_appid": credentials.get("wechat", {}).get("appid", ""),
            "wechat_secret": credentials.get("wechat", {}).get("secret", ""),
            "llm": credentials.get("llm", {}),
            "image": credentials.get("image", {}),
            "config_source": str(config_dir),
            "config_format": "split",
        }
    )
    return merged


def _load_single_json(path: Path) -> Dict[str, Any]:
    data = _read_json(path)
    merged = dict(DEFAULTS)
    merged.update(data)
    merged["config_source"] = str(path)
    merged["config_format"] = "single-json"
    return merged


def discover_config_candidates(explicit_path: str | None = None) -> List[Path]:
    if explicit_path:
        return [Path(explicit_path).expanduser()]

    env_candidates = [
        os.getenv("OPENCLAW_WECHAT_PUBLISH_CONFIG", "").strip(),
        os.getenv("WECHAT_PUBLISH_CONFIG", "").strip(),
    ]
    builtins = [
        "/tmp/openclaw/wechat-publish-config",
        str(Path.home() / ".local/openclaw-wechat-publisher/config"),
        str(_skill_root() / "config"),
    ]

    candidates: List[Path] = []
    seen = set()
    for raw in [*env_candidates, *builtins]:
        if not raw:
            continue
        path = Path(raw).expanduser()
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        if path.is_file() or _is_split_config_dir(path):
            candidates.append(path)
    return candidates


def load_config(config_path: str | None) -> Dict[str, Any]:
    if config_path:
        candidate = Path(config_path).expanduser()
        if candidate.is_dir():
            return _load_split_config(candidate)
        if candidate.exists():
            return _load_single_json(candidate)
        raise ConfigError(f"配置路径不存在: {candidate}")

    candidates = discover_config_candidates()
    for candidate in candidates:
        try:
            return load_config(str(candidate))
        except ConfigError:
            continue

    merged = dict(DEFAULTS)
    merged["config_source"] = "defaults"
    merged["config_format"] = "defaults"
    return merged

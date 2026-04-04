#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


def print_header() -> None:
    print("\n" + "=" * 60)
    print("  📰 微信公众号草稿箱发布助手 - 初次设置")
    print("=" * 60)
    print("\n先把‘发布’这一步设置好。排版、润色、去 AI 味等能力可以作为上游模块后续接入。\n")


def ask_with_default(prompt: str, default: str | None = None, required: bool = True) -> Optional[str]:
    prompt_text = f"{prompt} [{default}]: " if default else f"{prompt}: "
    while True:
        value = input(prompt_text).strip()
        if not value and default is not None:
            return default
        if not value and required:
            print("  ⚠️  这一项还需要你填一下")
            continue
        if not value and not required:
            return None
        return value


def save_config(credentials: dict, settings: dict) -> Path:
    config_dir = Path(__file__).parent / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    credentials_file = config_dir / "credentials.json"
    settings_file = config_dir / "settings.json"

    credentials_file.write_text(json.dumps(credentials, ensure_ascii=False, indent=2), encoding="utf-8")
    settings_file.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    return config_dir


def setup_minimal_config() -> tuple[dict, dict]:
    print("这一步只收集发布草稿箱真正必需的信息。\n")
    print("你现在只需要准备 3 个东西：")
    print("  1) 公众号 AppID")
    print("  2) 公众号 AppSecret")
    print("  3) 默认作者名\n")
    print("💡 AppID / AppSecret 在微信公众平台里可以找到：")
    print("   设置与开发 > 基本配置\n")

    appid = ask_with_default("请输入公众号 AppID")
    secret = ask_with_default("请输入公众号 AppSecret")
    author = ask_with_default("文章默认作者名", "日新", required=False) or "日新"

    credentials = {"wechat": {"appid": appid, "secret": secret}}
    settings = {
        "author": author,
        "default_thumb_media_id": "",
        "output_dir": None,
        "server_ip": None,
        "use_custom_prompts": False,
        "weixin_api_base": "https://api.weixin.qq.com",
        "format_markdown": True,
        "request_timeout_seconds": 30,
    }
    return credentials, settings


def main() -> int:
    print_header()
    credentials, settings = setup_minimal_config()
    config_dir = save_config(credentials, settings)
    print("\n✅ 设置完成。")
    print(f"   配置已保存到：{config_dir}")
    print("\n建议你立刻做两步验证：")
    print("  1) python3 scripts/check_wechat_connection.py")
    print("  2) python3 scripts/publish_markdown.py --check --file /path/to/article.md --cover-image /path/to/cover.jpg")
    print("\n说明：")
    print("- 这个 Skill 默认只负责发布到草稿箱")
    print("- 去 AI 味、润色、排版增强等能力，建议作为上游步骤接入")
    print("- 草稿箱不等于正式群发，最终是否发布仍应人工确认")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n已取消。")
        raise SystemExit(1)

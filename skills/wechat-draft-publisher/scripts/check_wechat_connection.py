#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
LIB_DIR = SCRIPT_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from config_loader import ConfigError, load_config
from wechat_client import WeChatAPIError, WeChatClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check WeChat AppID/AppSecret connectivity")
    parser.add_argument("--config", help="Path to config settings JSON or config directory")
    return parser.parse_args()


async def _run(config_path: str | None) -> int:
    try:
        config = load_config(config_path)
    except ConfigError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    appid = config.get("wechat_appid", "")
    secret = config.get("wechat_secret", "")
    if not appid or not secret:
        print(json.dumps({
            "ok": False,
            "error": "缺少微信配置：wechat_appid / wechat_secret",
            "config_source": config.get("config_source", "unknown"),
        }, ensure_ascii=False, indent=2))
        return 1

    client = WeChatClient(
        appid=appid,
        secret=secret,
        api_base=config.get("weixin_api_base", "https://api.weixin.qq.com"),
        timeout_seconds=int(config.get("request_timeout_seconds", 30)),
    )
    try:
        token = await client.get_access_token()
        print(json.dumps({
            "ok": True,
            "config_source": config.get("config_source", "unknown"),
            "api_base": config.get("weixin_api_base", "https://api.weixin.qq.com"),
            "token_prefix": token[:10] + "...",
            "message": "已成功拿到 access_token。若后续发布时报 40164，请继续检查公众号后台 IP 白名单。",
        }, ensure_ascii=False, indent=2))
        return 0
    except (WeChatAPIError, Exception) as exc:
        print(json.dumps({
            "ok": False,
            "config_source": config.get("config_source", "unknown"),
            "api_base": config.get("weixin_api_base", "https://api.weixin.qq.com"),
            "error": str(exc),
        }, ensure_ascii=False, indent=2))
        return 1
    finally:
        await client.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_run(parse_args().config)))

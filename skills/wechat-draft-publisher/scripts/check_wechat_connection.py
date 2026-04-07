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

from config_loader import ConfigError, discover_config_candidates, load_config
from wechat_client import WeChatAPIError, WeChatClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check WeChat AppID/AppSecret connectivity")
    parser.add_argument("--config", help="Path to config settings JSON or config directory")
    parser.add_argument("--all", action="store_true", help="Check all discovered config candidates")
    return parser.parse_args()


async def _check_one(config_path: str | None) -> dict:
    try:
        config = load_config(config_path)
    except ConfigError as exc:
        return {"ok": False, "error": str(exc), "config_source": config_path or "auto"}

    appid = config.get("wechat_appid", "")
    secret = config.get("wechat_secret", "")
    if not appid or not secret:
        return {
            "ok": False,
            "error": "缺少微信配置：wechat_appid / wechat_secret",
            "config_source": config.get("config_source", "unknown"),
        }

    client = WeChatClient(
        appid=appid,
        secret=secret,
        api_base=config.get("weixin_api_base", "https://api.weixin.qq.com"),
        timeout_seconds=int(config.get("request_timeout_seconds", 30)),
    )
    try:
        token = await client.get_access_token()
        return {
            "ok": True,
            "config_source": config.get("config_source", "unknown"),
            "api_base": config.get("weixin_api_base", "https://api.weixin.qq.com"),
            "token_prefix": token[:10] + "...",
            "message": "已成功拿到 access_token。若后续发布时报 40164，请继续检查公众号后台 IP 白名单。",
        }
    except (WeChatAPIError, Exception) as exc:
        return {
            "ok": False,
            "config_source": config.get("config_source", "unknown"),
            "api_base": config.get("weixin_api_base", "https://api.weixin.qq.com"),
            "error": str(exc),
        }
    finally:
        await client.close()


async def _run(config_path: str | None, check_all: bool) -> int:
    if check_all:
        candidates = discover_config_candidates(config_path)
        results = []
        for candidate in candidates:
            results.append(await _check_one(str(candidate)))
        ok_any = any(item.get("ok") for item in results)
        print(json.dumps({
            "ok": ok_any,
            "checked_count": len(results),
            "results": results,
        }, ensure_ascii=False, indent=2))
        return 0 if ok_any else 1

    result = await _check_one(config_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(asyncio.run(_run(args.config, args.all)))

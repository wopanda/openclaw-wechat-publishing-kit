from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx


class WeChatAPIError(RuntimeError):
    pass


class AccessTokenCache:
    def __init__(self):
        self._token: Optional[str] = None
        self._expires_at: float = 0
        self._lock = asyncio.Lock()

    def is_valid(self) -> bool:
        return self._token is not None and time.time() < self._expires_at

    def get(self) -> Optional[str]:
        if self.is_valid():
            return self._token
        return None

    def set(self, token: str, ttl_seconds: int):
        self._token = token
        self._expires_at = time.time() + ttl_seconds

    def clear(self):
        self._token = None
        self._expires_at = 0

    async def get_lock(self):
        return self._lock


@dataclass
class WeChatClient:
    appid: str
    secret: str
    api_base: str = "https://api.weixin.qq.com"
    timeout_seconds: int = 30
    cache_seconds: int = 7000

    def __post_init__(self):
        if not self.appid or not self.secret:
            raise ValueError("缺少 wechat_appid / wechat_secret")
        self.logger = logging.getLogger(__name__)
        self._token_cache = AccessTokenCache()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=float(self.timeout_seconds), follow_redirects=True)
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_access_token(self, force_refresh: bool = False) -> str:
        if not force_refresh:
            cached = self._token_cache.get()
            if cached:
                return cached

        async with await self._token_cache.get_lock():
            if not force_refresh:
                cached = self._token_cache.get()
                if cached:
                    return cached

            client = await self._get_client()
            response = await client.post(
                f"{self.api_base}/cgi-bin/stable_token",
                json={
                    "grant_type": "client_credential",
                    "appid": self.appid,
                    "secret": self.secret,
                    "force_refresh": force_refresh,
                },
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()
            errcode = payload.get("errcode", 0)
            if errcode not in (0, None):
                raise WeChatAPIError(f"获取 access_token 失败: {payload.get('errmsg', 'unknown error')} (errcode={errcode})")

            token = payload.get("access_token")
            if not token:
                raise WeChatAPIError("获取 access_token 失败: 响应中缺少 access_token")
            expires_in = int(payload.get("expires_in", 7200))
            cache_duration = max(1, min(expires_in - 200, self.cache_seconds))
            self._token_cache.set(token, cache_duration)
            return token

    async def upload_image(self, image_bytes: bytes, filename: str = "image.jpg", max_retries: int = 2) -> Dict[str, Any]:
        for attempt in range(max_retries + 1):
            try:
                token = await self.get_access_token(force_refresh=(attempt > 0))
                client = await self._get_client()
                response = await client.post(
                    f"{self.api_base}/cgi-bin/material/add_material",
                    params={"access_token": token, "type": "image"},
                    files={"media": (filename, image_bytes, "image/jpeg")},
                )
                response.raise_for_status()
                payload = response.json()
                errcode = payload.get("errcode", 0)
                if errcode not in (0, None):
                    if errcode in [40001, 40014, 42001] and attempt < max_retries:
                        self._token_cache.clear()
                        continue
                    raise WeChatAPIError(f"上传图片失败: {payload.get('errmsg', 'unknown error')} (errcode={errcode})")
                return {
                    "media_id": payload.get("media_id", ""),
                    "url": payload.get("url", ""),
                }
            except httpx.HTTPError as exc:
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise WeChatAPIError(f"上传图片网络请求失败: {exc}") from exc

        raise WeChatAPIError("上传图片失败: 超过最大重试次数")

    async def add_draft(self, title: str, author: str, content_html: str, thumb_media_id: str = "", max_retries: int = 2) -> Dict[str, Any]:
        for attempt in range(max_retries + 1):
            try:
                token = await self.get_access_token(force_refresh=(attempt > 0))
                article = {
                    "title": title,
                    "author": author,
                    "content": content_html,
                    "digest": "",
                    "content_source_url": "",
                    "need_open_comment": 0,
                    "only_fans_can_comment": 0,
                }
                if thumb_media_id:
                    article["thumb_media_id"] = thumb_media_id
                    article["show_cover_pic"] = 1

                body = {"articles": [article]}
                client = await self._get_client()
                response = await client.post(
                    f"{self.api_base}/cgi-bin/draft/add",
                    params={"access_token": token},
                    json=body,
                )
                response.raise_for_status()
                payload = response.json()
                errcode = payload.get("errcode", 0)
                if errcode not in (0, None):
                    if errcode in [40001, 40014, 42001] and attempt < max_retries:
                        self._token_cache.clear()
                        continue
                    raise WeChatAPIError(f"发布草稿失败: {payload.get('errmsg', 'unknown error')} (errcode={errcode})")
                media_id = payload.get("media_id", "")
                return {
                    "media_id": media_id,
                    "draft_id": media_id,
                    "draft_url": "https://mp.weixin.qq.com/",
                    "raw": payload,
                }
            except httpx.HTTPError as exc:
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise WeChatAPIError(f"发布草稿网络请求失败: {exc}") from exc

        raise WeChatAPIError("发布草稿失败: 超过最大重试次数")

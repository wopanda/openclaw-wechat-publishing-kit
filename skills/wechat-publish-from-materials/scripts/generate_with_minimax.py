#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

DEFAULT_BASE_URL = 'https://api.minimaxi.com/v1/image_generation'
DEFAULT_MODEL = 'image-01'
DEFAULT_TIMEOUT = 120.0
OPENCLAW_CONFIG_PATHS = [
    Path.home() / '.openclaw' / 'openclaw.json',
    Path('/root/.openclaw/openclaw.json'),
]


def slugify(text: str) -> str:
    text = re.sub(r'[^\w\-\u4e00-\u9fff]+', '-', text.strip())
    text = re.sub(r'-{2,}', '-', text).strip('-')
    return text[:60] or 'image'


def load_slots(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(data, dict) and 'slots' in data:
        return data['slots']
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and 'slot_id' in data:
        return [data]
    raise ValueError('无法识别 slots 输入格式；请提供单图对象、slots 数组或包含 slots 的对象')


def normalize_aspect_ratio(slot: dict[str, Any]) -> str:
    aspect = str(slot.get('aspect_ratio', '')).strip() or '4:3'
    allowed = {'1:1', '16:9', '4:3', '3:2', '2:3', '3:4', '9:16', '21:9'}
    return aspect if aspect in allowed else '4:3'


def build_prompt(slot: dict[str, Any]) -> str:
    prompt = str(slot.get('prompt') or '').strip()
    if prompt:
        return prompt
    title = slot.get('title', '')
    purpose = slot.get('purpose', '')
    visual_type = slot.get('visual_type', '')
    scene = slot.get('scene_description', '')
    style = slot.get('style', '')
    aspect = slot.get('aspect_ratio', '')
    return f'{title}，{purpose}，{visual_type}，{scene}，{style}，{aspect}'.strip('， ')


def resolve_api_key_from_openclaw() -> str:
    for path in OPENCLAW_CONFIG_PATHS:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            continue
        value = (
            (((data or {}).get('models') or {}).get('providers') or {}).get('minimax') or {}
        ).get('apiKey', '')
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ''


def resolve_api_key(explicit: str) -> str:
    if explicit.strip():
        return explicit.strip()
    for env_name in ('MINIMAX_API_KEY', 'MINIMAX_APIKEY', 'ABAB_API_KEY'):
        value = os.environ.get(env_name, '').strip()
        if value:
            return value
    value = resolve_api_key_from_openclaw()
    if value:
        return value
    raise RuntimeError('缺少 MiniMax API key；请传 --api-key，或设置 MINIMAX_API_KEY，或在 ~/.openclaw/openclaw.json 配置 minimax provider')


def guess_extension(url: str, content_type: str) -> str:
    ext = ''
    if content_type:
        ext = mimetypes.guess_extension(content_type.split(';', 1)[0].strip()) or ''
    if not ext:
        path = urlparse(url).path
        ext = Path(path).suffix
    if not ext or len(ext) > 8:
        ext = '.jpeg'
    if ext == '.jpe':
        ext = '.jpeg'
    return ext


def generate_one(slot: dict[str, Any], output_dir: Path, api_key: str, model: str, base_url: str) -> dict[str, Any]:
    slot_id = str(slot.get('slot_id') or 'image')
    prompt = build_prompt(slot)
    aspect_ratio = normalize_aspect_ratio(slot)
    payload = {
        'model': model,
        'prompt': prompt,
        'aspect_ratio': aspect_ratio,
        'response_format': 'url',
        'n': 1,
        'prompt_optimizer': False,
        'aigc_watermark': False,
    }
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }

    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = client.post(base_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            image_url = (((data or {}).get('data') or {}).get('image_urls') or [''])[0]
            base_resp = (data or {}).get('base_resp') or {}
            if base_resp.get('status_code') not in (None, 0):
                return {
                    'slot_id': slot_id,
                    'status': 'failed',
                    'reason': f"minimax_status_{base_resp.get('status_code')}: {base_resp.get('status_msg', '')}".strip(),
                    'model': model,
                    'base_url': base_url,
                    'prompt': prompt,
                    'aspect_ratio': aspect_ratio,
                }
            if not image_url:
                return {
                    'slot_id': slot_id,
                    'status': 'failed',
                    'reason': f'minimax_missing_image_url: {json.dumps(data, ensure_ascii=False)[:500]}',
                    'model': model,
                    'base_url': base_url,
                    'prompt': prompt,
                    'aspect_ratio': aspect_ratio,
                }
            image_resp = client.get(image_url)
            image_resp.raise_for_status()
            ext = guess_extension(image_url, image_resp.headers.get('content-type', ''))
            filename = output_dir / f'{slugify(slot_id)}{ext}'
            filename.write_bytes(image_resp.content)
    except Exception as exc:
        return {
            'slot_id': slot_id,
            'status': 'failed',
            'reason': str(exc),
            'model': model,
            'base_url': base_url,
            'prompt': prompt,
            'aspect_ratio': aspect_ratio,
        }

    return {
        'slot_id': slot_id,
        'status': 'generated',
        'local_path': str(filename),
        'remote_url': image_url,
        'aspect_ratio': aspect_ratio,
        'model': model,
        'base_url': base_url,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Generate slot-based images via MiniMax official image generation API')
    parser.add_argument('--slots-file', required=True, help='JSON file following image-generation-input-contract.md')
    parser.add_argument('--output-dir', required=True, help='Directory for generated images')
    parser.add_argument('--model', default=os.environ.get('MINIMAX_IMAGE_MODEL', DEFAULT_MODEL))
    parser.add_argument('--base-url', default=os.environ.get('MINIMAX_IMAGE_BASE_URL', DEFAULT_BASE_URL))
    parser.add_argument('--api-key', default='')
    args = parser.parse_args()

    slots = load_slots(Path(args.slots_file))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        api_key = resolve_api_key(args.api_key)
    except Exception as exc:
        print(json.dumps({'results': [], 'error': str(exc)}, ensure_ascii=False, indent=2))
        return 1

    results = [generate_one(slot, output_dir, api_key, args.model, args.base_url) for slot in slots]
    print(json.dumps({'results': results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

DEFAULT_TIMEOUT = 120.0
OPENCLAW_CONFIG_PATHS = [
    Path.home() / '.openclaw' / 'openclaw.json',
    Path('/root/.openclaw/openclaw.json'),
]

PROVIDER_PRESETS = {
    'minimax': {
        'base_url': 'https://api.minimaxi.com/v1/image_generation',
        'model': 'image-01',
        'env_keys': ('MINIMAX_API_KEY', 'MINIMAX_APIKEY', 'ABAB_API_KEY'),
        'config_keys': ('minimax',),
        'prompt_limit': 1450,
    },
    'seedream': {
        'base_url': 'https://ark.cn-beijing.volces.com/api/v3/images/generations',
        'model': 'doubao-seedream-4-5-251128',
        'env_keys': ('JIMENG_API_KEY', 'ARK_API_KEY', 'DOUBAO_API_KEY', 'VOLCENGINE_API_KEY'),
        'config_keys': ('jimeng', 'seedream', 'ark', 'volcengine'),
        'prompt_limit': 1800,
    },
}

PROVIDER_ALIASES = {
    'minimax': 'minimax',
    'mini_max': 'minimax',
    'abab': 'minimax',
    'jimeng': 'seedream',
    '即梦': 'seedream',
    'seedream': 'seedream',
    'ark': 'seedream',
    'volcengine': 'seedream',
}


def canonical_provider(name: str | None) -> str:
    raw = (name or '').strip().lower()
    if not raw:
        return 'minimax'
    return PROVIDER_ALIASES.get(raw, raw)


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


def pick_size(slot: dict[str, Any]) -> str:
    aspect = normalize_aspect_ratio(slot)
    if aspect in {'16:9', '21:9'}:
        return '2560x1440'
    if aspect == '1:1':
        return '1024x1024'
    if aspect in {'3:4'}:
        return '1536x2048'
    if aspect in {'9:16'}:
        return '1440x2560'
    return '2048x1536'


def dedupe_phrases(text: str) -> str:
    parts = [part.strip() for part in text.split(',') if part.strip()]
    seen: set[str] = set()
    result: list[str] = []
    for part in parts:
        key = re.sub(r'\s+', ' ', part.lower())
        if key in seen:
            continue
        seen.add(key)
        result.append(part)
    return ', '.join(result)


def trim_prompt(text: str, limit: int) -> str:
    compact = dedupe_phrases(text)
    if len(compact) <= limit:
        return compact

    parts = [part.strip() for part in compact.split(',') if part.strip()]
    selected: list[str] = []
    total = 0
    for part in parts:
        candidate = part if not selected else f', {part}'
        if total + len(candidate) > limit:
            break
        selected.append(part)
        total += len(candidate)
    return ', '.join(selected) if selected else compact[:limit]


def build_prompt(slot: dict[str, Any], provider: str) -> str:
    prompt_block = slot.get('prompt')
    if isinstance(prompt_block, dict):
        main_en = str(prompt_block.get('main_en') or '').strip()
        negative_en = str(prompt_block.get('negative_en') or '').strip()
        prompt = main_en
        if main_en and negative_en:
            prompt = f'{main_en}, negative prompt: {negative_en}'
        if prompt:
            limit = PROVIDER_PRESETS.get(provider, PROVIDER_PRESETS['minimax']).get('prompt_limit', 1450)
            return trim_prompt(prompt, int(limit))

    prompt = str(prompt_block or '').strip()
    if prompt:
        limit = PROVIDER_PRESETS.get(provider, PROVIDER_PRESETS['minimax']).get('prompt_limit', 1450)
        return trim_prompt(prompt, int(limit))

    prompt_main = str(slot.get('prompt_main') or '').strip()
    negative_prompt = str(slot.get('negative_prompt') or '').strip()
    if prompt_main:
        composed = f'{prompt_main}, negative prompt: {negative_prompt}' if negative_prompt else prompt_main
        limit = PROVIDER_PRESETS.get(provider, PROVIDER_PRESETS['minimax']).get('prompt_limit', 1450)
        return trim_prompt(composed, int(limit))

    title = slot.get('title', '')
    purpose = slot.get('purpose', '')
    visual_type = slot.get('visual_type', '')
    scene = slot.get('scene_description', '')
    style = slot.get('style', '')
    aspect = slot.get('aspect_ratio', '')
    composed = f'{title}，{purpose}，{visual_type}，{scene}，{style}，{aspect}'.strip('， ')
    limit = PROVIDER_PRESETS.get(provider, PROVIDER_PRESETS['minimax']).get('prompt_limit', 1450)
    return trim_prompt(composed, int(limit))


def resolve_api_key_from_openclaw(provider: str) -> str:
    config_keys = PROVIDER_PRESETS.get(provider, PROVIDER_PRESETS['minimax'])['config_keys']
    for path in OPENCLAW_CONFIG_PATHS:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            continue
        providers = (((data or {}).get('models') or {}).get('providers') or {})
        for key in config_keys:
            provider_config = providers.get(key) or {}
            if not isinstance(provider_config, dict):
                continue
            for field in ('apiKey', 'api_key', 'key'):
                value = provider_config.get(field, '')
                if isinstance(value, str) and value.strip():
                    return value.strip()
    return ''


def resolve_api_key(provider: str, explicit: str) -> str:
    if explicit.strip():
        return explicit.strip()
    env_keys = PROVIDER_PRESETS.get(provider, PROVIDER_PRESETS['minimax'])['env_keys']
    for env_name in env_keys:
        value = os.environ.get(env_name, '').strip()
        if value:
            return value
    value = resolve_api_key_from_openclaw(provider)
    if value:
        return value
    if provider == 'seedream':
        raise RuntimeError('缺少即梦/Seedream API key；请传 --api-key，或设置 JIMENG_API_KEY / ARK_API_KEY / VOLCENGINE_API_KEY')
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


def bool_from_any(value: Any, default: bool = False) -> bool:
    if value in (None, ''):
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}
    return bool(value)


def generate_one_minimax(
    slot: dict[str, Any],
    output_dir: Path,
    api_key: str,
    model: str,
    base_url: str,
    prompt_optimizer: bool,
) -> dict[str, Any]:
    slot_id = str(slot.get('slot_id') or 'image')
    prompt = build_prompt(slot, 'minimax')
    aspect_ratio = normalize_aspect_ratio(slot)
    payload = {
        'model': model,
        'prompt': prompt,
        'aspect_ratio': aspect_ratio,
        'response_format': 'url',
        'n': 1,
        'prompt_optimizer': prompt_optimizer,
        'aigc_watermark': False,
    }
    if slot.get('seed') not in (None, ''):
        payload['seed'] = slot.get('seed')
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
                    'provider': 'minimax',
                    'model': model,
                    'base_url': base_url,
                    'prompt': prompt,
                    'aspect_ratio': aspect_ratio,
                    'prompt_optimizer': prompt_optimizer,
                }
            if not image_url:
                return {
                    'slot_id': slot_id,
                    'status': 'failed',
                    'reason': f'minimax_missing_image_url: {json.dumps(data, ensure_ascii=False)[:500]}',
                    'provider': 'minimax',
                    'model': model,
                    'base_url': base_url,
                    'prompt': prompt,
                    'aspect_ratio': aspect_ratio,
                    'prompt_optimizer': prompt_optimizer,
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
            'provider': 'minimax',
            'model': model,
            'base_url': base_url,
            'prompt': prompt,
            'aspect_ratio': aspect_ratio,
            'prompt_optimizer': prompt_optimizer,
        }

    return {
        'slot_id': slot_id,
        'status': 'generated',
        'local_path': str(filename),
        'remote_url': image_url,
        'provider': 'minimax',
        'aspect_ratio': aspect_ratio,
        'model': model,
        'base_url': base_url,
        'prompt_optimizer': prompt_optimizer,
    }


def generate_one_seedream(
    slot: dict[str, Any],
    output_dir: Path,
    api_key: str,
    model: str,
    base_url: str,
) -> dict[str, Any]:
    slot_id = str(slot.get('slot_id') or 'image')
    prompt = build_prompt(slot, 'seedream')
    size = pick_size(slot)
    payload = {
        'model': model,
        'prompt': prompt,
        'size': size,
        'response_format': 'url',
        'watermark': False,
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
            image_url = (((data or {}).get('data') or [{}])[0]).get('url', '')
            if not image_url:
                return {
                    'slot_id': slot_id,
                    'status': 'failed',
                    'reason': f'seedream_missing_image_url: {json.dumps(data, ensure_ascii=False)[:500]}',
                    'provider': 'seedream',
                    'model': model,
                    'base_url': base_url,
                    'prompt': prompt,
                    'size': size,
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
            'provider': 'seedream',
            'model': model,
            'base_url': base_url,
            'prompt': prompt,
            'size': size,
        }

    return {
        'slot_id': slot_id,
        'status': 'generated',
        'local_path': str(filename),
        'provider': 'seedream',
        'size': size,
        'model': model,
        'base_url': base_url,
    }


def generate_one(
    slot: dict[str, Any],
    output_dir: Path,
    default_provider: str,
    default_api_key: str,
    default_model: str,
    default_base_url: str,
    default_prompt_optimizer: bool | None = None,
) -> dict[str, Any]:
    provider = canonical_provider(
        slot.get('image_provider') or slot.get('provider') or default_provider
    )
    if provider not in PROVIDER_PRESETS:
        return {
            'slot_id': str(slot.get('slot_id') or 'image'),
            'status': 'failed',
            'reason': f'unsupported_provider: {provider}',
            'provider': provider,
        }

    api_key = str(slot.get('image_api_key') or slot.get('api_key') or default_api_key).strip()
    model = str(slot.get('image_model') or default_model or PROVIDER_PRESETS[provider]['model']).strip()
    base_url = str(slot.get('image_base_url') or slot.get('base_url') or default_base_url or PROVIDER_PRESETS[provider]['base_url']).strip()

    if provider == 'minimax':
        slot_prompt_optimizer = slot.get('prompt_optimizer', None)
        prompt_optimizer = bool_from_any(slot_prompt_optimizer, default=bool(default_prompt_optimizer))
        return generate_one_minimax(slot, output_dir, api_key, model, base_url, prompt_optimizer)
    return generate_one_seedream(slot, output_dir, api_key, model, base_url)


def main() -> int:
    parser = argparse.ArgumentParser(description='Generate slot-based images via configurable providers (default: MiniMax, optional: Jimeng/Seedream)')
    parser.add_argument('--slots-file', required=True, help='JSON file following image-generation-input-contract.md')
    parser.add_argument('--output-dir', required=True, help='Directory for generated images')
    parser.add_argument('--provider', default=os.environ.get('WECHAT_IMAGE_PROVIDER', os.environ.get('IMAGE_PROVIDER', 'minimax')), help='Image provider: minimax | jimeng | seedream | ark')
    parser.add_argument('--model', default='', help='Override model for the selected provider')
    parser.add_argument('--base-url', default='', help='Override base URL for the selected provider')
    parser.add_argument('--api-key', default='', help='Override API key for the selected provider')
    parser.add_argument('--prompt-optimizer', default='', help='MiniMax only: override prompt_optimizer for all slots: true/false')
    args = parser.parse_args()

    provider = canonical_provider(args.provider)
    if provider not in PROVIDER_PRESETS:
        print(json.dumps({'results': [], 'error': f'unsupported_provider: {args.provider}'}, ensure_ascii=False, indent=2))
        return 1

    slots = load_slots(Path(args.slots_file))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        api_key = resolve_api_key(provider, args.api_key)
    except Exception as exc:
        print(json.dumps({'results': [], 'error': str(exc), 'provider': provider}, ensure_ascii=False, indent=2))
        return 1

    model = args.model.strip() or PROVIDER_PRESETS[provider]['model']
    base_url = args.base_url.strip() or PROVIDER_PRESETS[provider]['base_url']
    prompt_optimizer_override = None
    if str(args.prompt_optimizer).strip():
        prompt_optimizer_override = bool_from_any(args.prompt_optimizer)

    results = [
        generate_one(slot, output_dir, provider, api_key, model, base_url, prompt_optimizer_override)
        for slot in slots
    ]
    print(json.dumps({
        'provider': provider,
        'model': model,
        'base_url': base_url,
        'results': results,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

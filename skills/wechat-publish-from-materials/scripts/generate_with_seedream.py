#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

import httpx

DEFAULT_BASE_URL = 'https://ark.cn-beijing.volces.com/api/v3/images/generations'
DEFAULT_MODEL = 'doubao-seedream-4-5-251128'
DEFAULT_TIMEOUT = 120.0


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


def pick_size(slot: dict[str, Any]) -> str:
    aspect = str(slot.get('aspect_ratio', '')).strip()
    if aspect in {'16:9', '21:9'}:
        return '2560x1440'
    if aspect == '1:1':
        return '1024x1024'
    if aspect in {'3:4', '4:5'}:
        return '1536x2048'
    return '2048x1536'


def build_prompt(slot: dict[str, Any]) -> str:
    prompt_block = slot.get('prompt')
    if isinstance(prompt_block, dict):
        main_zh = str(prompt_block.get('main_zh') or '').strip()
        negative_zh = str(prompt_block.get('negative_zh') or '').strip()
        main_en = str(prompt_block.get('main_en') or '').strip()
        negative_en = str(prompt_block.get('negative_en') or '').strip()
        if main_zh and negative_zh:
            return f'{main_zh}。负面约束：{negative_zh}'
        if main_zh:
            return main_zh
        if main_en and negative_en:
            return f'{main_en}, negative prompt: {negative_en}'
        if main_en:
            return main_en

    prompt = str(prompt_block or '').strip()
    if prompt:
        return prompt
    prompt_main = str(slot.get('prompt_main') or slot.get('prompt_cn') or slot.get('prompt_en') or '').strip()
    if prompt_main:
        return prompt_main
    title = slot.get('title', '')
    purpose = slot.get('purpose', '')
    visual_type = slot.get('visual_type', '')
    scene = slot.get('scene_description', '')
    style = slot.get('style', '')
    aspect = slot.get('aspect_ratio', '')
    return f'{title}，{purpose}，{visual_type}，{scene}，{style}，{aspect}'.strip('， ')


def resolve_api_key(explicit: str) -> str:
    if explicit.strip():
        return explicit.strip()
    for env_name in ('ARK_API_KEY', 'DOUBAO_API_KEY', 'VOLCENGINE_API_KEY', 'JIMENG_API_KEY'):
        value = os.environ.get(env_name, '').strip()
        if value:
            return value
    raise RuntimeError('缺少即梦/Ark API key；请传 --api-key，或设置 ARK_API_KEY / DOUBAO_API_KEY / VOLCENGINE_API_KEY / JIMENG_API_KEY')


def generate_one(slot: dict[str, Any], output_dir: Path, api_key: str, model: str, base_url: str) -> dict[str, Any]:
    slot_id = str(slot.get('slot_id') or 'image')
    filename = output_dir / f'{slugify(slot_id)}.png'
    prompt = build_prompt(slot)
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
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            resp = client.post(base_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            image_url = (((data or {}).get('data') or [{}])[0]).get('url', '')
            if not image_url:
                return {
                    'slot_id': slot_id,
                    'status': 'failed',
                    'reason': f'ark_missing_image_url: {json.dumps(data, ensure_ascii=False)[:500]}',
                    'model': model,
                    'base_url': base_url,
                    'prompt': prompt,
                }
            image_resp = client.get(image_url)
            image_resp.raise_for_status()
            filename.write_bytes(image_resp.content)
    except Exception as exc:
        return {
            'slot_id': slot_id,
            'status': 'failed',
            'reason': str(exc),
            'model': model,
            'base_url': base_url,
            'prompt': prompt,
        }

    return {
        'slot_id': slot_id,
        'status': 'generated',
        'local_path': str(filename),
        'size': size,
        'model': model,
        'base_url': base_url,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Generate slot-based images via Seedream (Ark API)')
    parser.add_argument('--slots-file', required=True, help='JSON file following image-generation-input-contract.md')
    parser.add_argument('--output-dir', required=True, help='Directory for generated images')
    parser.add_argument('--model', default=os.environ.get('ARK_IMAGE_MODEL', DEFAULT_MODEL))
    parser.add_argument('--base-url', default=os.environ.get('ARK_BASE_URL', DEFAULT_BASE_URL))
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

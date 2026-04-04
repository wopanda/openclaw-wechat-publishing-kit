#!/usr/bin/env python3
"""Generate slot-based images for material-to-graphic-report via nano-banana-pro.

This script is the default real-image execution bridge for `material-to-graphic-report`.
It reads slot-based image requests, then calls the local nano-banana-pro skill script
with the correct image model (`gemini-3-pro-image-preview`).
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

NANO_SCRIPT = Path('/root/.openclaw/skills/nano-banana-pro-2/scripts/generate_image.py')
DEFAULT_BASE_URL = 'https://api.huandutech.com'
DEFAULT_MODEL = 'gemini-3-pro-image-preview'


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


def pick_resolution(slot: dict[str, Any]) -> str:
    aspect = str(slot.get('aspect_ratio', '')).strip()
    if aspect in {'16:9', '21:9'}:
        return '2K'
    return '1K'


def build_prompt(slot: dict[str, Any]) -> str:
    prompt = (slot.get('prompt') or '').strip()
    if prompt:
        return prompt
    title = slot.get('title', '')
    purpose = slot.get('purpose', '')
    visual_type = slot.get('visual_type', '')
    scene = slot.get('scene_description', '')
    style = slot.get('style', '')
    aspect = slot.get('aspect_ratio', '')
    return f'{title}，{purpose}，{visual_type}，{scene}，{style}，{aspect}'.strip('， ')


def run_one(slot: dict[str, Any], output_dir: Path, model: str, base_url: str) -> dict[str, Any]:
    slot_id = slot['slot_id']
    filename = output_dir / f"{slugify(slot_id)}.png"
    prompt = build_prompt(slot)
    resolution = pick_resolution(slot)

    cmd = [
        sys.executable,
        str(NANO_SCRIPT),
        '--prompt', prompt,
        '--filename', str(filename),
        '--resolution', resolution,
        '--model', model,
        '--base-url', base_url,
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()

    if proc.returncode == 0 and filename.exists():
        return {
            'slot_id': slot_id,
            'status': 'generated',
            'local_path': str(filename),
            'resolution': resolution,
            'model': model,
            'base_url': base_url,
            'stdout': stdout,
        }

    reason = stderr or stdout or f'process_exit_{proc.returncode}'
    return {
        'slot_id': slot_id,
        'status': 'failed',
        'reason': reason,
        'model': model,
        'base_url': base_url,
        'prompt': prompt,
    }


def main():
    parser = argparse.ArgumentParser(description='Generate slot-based images via nano-banana-pro')
    parser.add_argument('--slots-file', required=True, help='JSON file following image-generation-input-contract.md')
    parser.add_argument('--output-dir', required=True, help='Directory for generated images')
    parser.add_argument('--model', default=DEFAULT_MODEL)
    parser.add_argument('--base-url', default=os.environ.get('GOOGLE_GEMINI_BASE_URL', DEFAULT_BASE_URL))
    args = parser.parse_args()

    if not NANO_SCRIPT.exists():
        raise FileNotFoundError(f'nano-banana-pro script not found: {NANO_SCRIPT}')
    if not os.environ.get('GEMINI_API_KEY'):
        raise RuntimeError('缺少 GEMINI_API_KEY，无法调用 nano-banana-pro 生图')

    slots = load_slots(Path(args.slots_file))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = [run_one(slot, output_dir, args.model, args.base_url) for slot in slots]
    print(json.dumps({'results': results}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

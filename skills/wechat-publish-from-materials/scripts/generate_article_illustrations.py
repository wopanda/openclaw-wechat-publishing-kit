#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

IMAGE_BRIDGE = Path(__file__).resolve().parent / 'generate_with_minimax.py'


def load_plan(path: Path) -> dict:
    data = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(data, dict) and 'slots' in data:
        return data
    raise ValueError('插图计划必须是包含 slots 的 JSON 对象')


def build_slots_payload(plan: dict) -> dict:
    slots = []
    for slot in plan.get('slots', []):
        slots.append({
            'slot_id': slot.get('slot_id'),
            'title': slot.get('title'),
            'purpose': slot.get('purpose'),
            'position': slot.get('insert_after_heading') or slot.get('position', ''),
            'visual_type': slot.get('visual_type'),
            'scene_description': slot.get('scene_description'),
            'prompt': slot.get('prompt') or {
                'zh_brief': slot.get('prompt_cn', ''),
                'main_en': slot.get('prompt_main', ''),
                'negative_en': slot.get('negative_prompt', ''),
            },
            'prompt_main': slot.get('prompt_main', ''),
            'negative_prompt': slot.get('negative_prompt', ''),
            'prompt_schema': slot.get('prompt_schema', {}),
            'aspect_ratio': slot.get('aspect_ratio', '4:3'),
            'style': slot.get('style', ''),
            'caption': slot.get('caption', ''),
        })
    return {
        'article_title': plan.get('article_title', ''),
        'slots': slots,
    }


def merge_results(plan: dict, results: dict) -> dict:
    mapping = {item.get('slot_id'): item for item in results.get('results', [])}
    merged_slots = []
    for slot in plan.get('slots', []):
        result = mapping.get(slot.get('slot_id'), {})
        merged = dict(slot)
        if result:
            merged.update({
                'status': result.get('status', slot.get('status', 'generated')),
                'local_path': result.get('local_path', slot.get('local_path', '')),
                'generation_reason': result.get('reason', ''),
                'image_provider': result.get('provider', ''),
                'image_model': result.get('model', ''),
            })
        merged_slots.append(merged)
    merged_plan = dict(plan)
    merged_plan['slots'] = merged_slots
    merged_plan['generation_results'] = results.get('results', [])
    return merged_plan


def main() -> int:
    parser = argparse.ArgumentParser(description='Generate article illustrations from an illustration plan')
    parser.add_argument('--plan', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--slots-file', default='')
    parser.add_argument('--merged-plan-output', default='')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--image-provider', default='', help='Image provider: minimax | jimeng | seedream | ark')
    parser.add_argument('--image-api-key', default='', help='Override API key for selected image provider')
    parser.add_argument('--image-base-url', default='', help='Override base URL for selected image provider')
    parser.add_argument('--image-model', default='', help='Override model for selected image provider')
    parser.add_argument('--prompt-optimizer', default='', help='MiniMax only: override prompt_optimizer')
    args = parser.parse_args()

    plan_path = Path(args.plan).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    plan = load_plan(plan_path)
    slots_payload = build_slots_payload(plan)
    slots_file = Path(args.slots_file).expanduser().resolve() if args.slots_file else output_dir / 'illustration-slots.json'
    slots_file.write_text(json.dumps(slots_payload, ensure_ascii=False, indent=2), encoding='utf-8')

    if args.dry_run:
        print(json.dumps({
            'ok': True,
            'mode': 'dry-run',
            'image_provider': args.image_provider or 'minimax',
            'slots_file': str(slots_file),
            'output_dir': str(output_dir),
            'slot_count': len(slots_payload.get('slots', [])),
        }, ensure_ascii=False, indent=2))
        return 0

    cmd = [
        sys.executable,
        str(IMAGE_BRIDGE),
        '--slots-file', str(slots_file),
        '--output-dir', str(output_dir),
    ]
    if args.image_provider.strip():
        cmd.extend(['--provider', args.image_provider.strip()])
    if args.image_api_key.strip():
        cmd.extend(['--api-key', args.image_api_key.strip()])
    if args.image_base_url.strip():
        cmd.extend(['--base-url', args.image_base_url.strip()])
    if args.image_model.strip():
        cmd.extend(['--model', args.image_model.strip()])
    if args.prompt_optimizer.strip():
        cmd.extend(['--prompt-optimizer', args.prompt_optimizer.strip()])

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)

    results = json.loads(proc.stdout)
    merged_plan = merge_results(plan, results)
    merged_out = Path(args.merged_plan_output).expanduser().resolve() if args.merged_plan_output else output_dir / 'illustration-plan.generated.json'
    merged_out.write_text(json.dumps(merged_plan, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({
        'ok': True,
        'image_provider': results.get('provider', args.image_provider or 'minimax'),
        'slots_file': str(slots_file),
        'merged_plan_output': str(merged_out),
        'results': results.get('results', []),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

MINIMAX_BRIDGE = Path(__file__).resolve().parent / 'generate_with_minimax.py'
JIMENG_BRIDGE = Path(__file__).resolve().parent / 'generate_with_seedream.py'


def normalize_provider(provider: str) -> str:
    value = (provider or '').strip().lower()
    if value in {'', 'minimax'}:
        return 'minimax'
    if value in {'jimeng', 'seedream', 'ark', 'doubao'}:
        return 'jimeng'
    raise ValueError(f'不支持的 provider: {provider}；可选: minimax, jimeng')


def pick_bridge(provider: str) -> Path:
    if provider == 'minimax':
        return MINIMAX_BRIDGE
    return JIMENG_BRIDGE


def resolve_effective_api_key(provider: str, generic: str, minimax_key: str, jimeng_key: str) -> str:
    if provider == 'minimax':
        return (minimax_key or generic).strip()
    return (jimeng_key or generic).strip()


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

    parser.add_argument('--provider', '--image-provider', dest='provider', default=os.environ.get('WECHAT_ILLUSTRATION_PROVIDER', 'minimax'), help='Image provider: minimax | jimeng (aliases: seedream/ark/doubao)')
    parser.add_argument('--api-key', '--image-api-key', dest='api_key', default='', help='Generic API key for selected provider')
    parser.add_argument('--minimax-api-key', default='', help='MiniMax API key (higher priority than --api-key when provider=minimax)')
    parser.add_argument('--jimeng-api-key', default='', help='Jimeng/Seedream API key (higher priority than --api-key when provider=jimeng)')
    parser.add_argument('--model', '--image-model', dest='model', default='', help='Override provider model id')
    parser.add_argument('--base-url', '--image-base-url', dest='base_url', default='', help='Override provider endpoint base url')
    parser.add_argument('--prompt-optimizer', default='', help='MiniMax only: override prompt_optimizer for all slots: true/false')
    args = parser.parse_args()

    plan_path = Path(args.plan).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    provider = normalize_provider(args.provider)
    bridge = pick_bridge(provider)

    plan = load_plan(plan_path)
    slots_payload = build_slots_payload(plan)
    slots_file = Path(args.slots_file).expanduser().resolve() if args.slots_file else output_dir / 'illustration-slots.json'
    slots_file.write_text(json.dumps(slots_payload, ensure_ascii=False, indent=2), encoding='utf-8')

    if args.dry_run:
        print(json.dumps({
            'ok': True,
            'mode': 'dry-run',
            'provider': provider,
            'bridge': str(bridge),
            'slots_file': str(slots_file),
            'output_dir': str(output_dir),
            'slot_count': len(slots_payload.get('slots', [])),
        }, ensure_ascii=False, indent=2))
        return 0

    effective_api_key = resolve_effective_api_key(provider, args.api_key, args.minimax_api_key, args.jimeng_api_key)

    cmd = [
        sys.executable,
        str(bridge),
        '--slots-file', str(slots_file),
        '--output-dir', str(output_dir),
    ]

    if effective_api_key:
        cmd.extend(['--api-key', effective_api_key])
    if args.model.strip():
        cmd.extend(['--model', args.model.strip()])
    if args.base_url.strip():
        cmd.extend(['--base-url', args.base_url.strip()])
    if provider == 'minimax' and args.prompt_optimizer.strip():
        cmd.extend(['--prompt-optimizer', args.prompt_optimizer.strip()])

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        stderr = (proc.stderr or '').strip()
        stdout = (proc.stdout or '').strip()
        raise SystemExit(f'{stderr}\n{stdout}'.strip())

    results = json.loads(proc.stdout)

    # — Permanent fix: ensure every generated image has local_path persisted —
    # OSS pre-signed URLs expire quickly (403 after ~1h).
    # Download all successfully-generated images to local files so downstream
    # merge and publish steps always have stable local paths, never a fleeting URL.
    for r in results.get('results', []):
        if r.get('status') != 'generated':
            continue
        local = str(r.get('local_path', '')).strip()
        remote = str(r.get('remote_url', '')).strip()
        if local and Path(local).expanduser().resolve().exists():
            continue  # already have a valid local file
        if not remote:
            continue
        # download to local
        local_path = Path(output_dir) / (r.get('slot_id', 'image') + '.jpg')
        try:
            with httpx.Client(timeout=60.0, follow_redirects=True) as client:
                resp = client.get(remote)
                resp.raise_for_status()
                local_path.write_bytes(resp.content)
            r['local_path'] = str(local_path)
            r['remote_url'] = ''   # local takes priority; clear the fragile remote URL
        except Exception:
            pass  # leave remote_url intact if download fails; publish will handle it

    merged_plan = merge_results(plan, results)
    merged_out = Path(args.merged_plan_output).expanduser().resolve() if args.merged_plan_output else output_dir / 'illustration-plan.generated.json'
    merged_out.write_text(json.dumps(merged_plan, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({
        'ok': True,
        'provider': provider,
        'bridge': str(bridge),
        'slots_file': str(slots_file),
        'merged_plan_output': str(merged_out),
        'results': results.get('results', []),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

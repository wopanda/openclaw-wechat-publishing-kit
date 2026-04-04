#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
SKILLS_DIR = SKILL_ROOT.parent
MATERIALS_ROOT = SKILLS_DIR / 'wechat-publish-from-materials'
PUBLISHER_ROOT = SKILLS_DIR / 'wechat-draft-publisher'

FLOW_SCRIPT = MATERIALS_ROOT / 'scripts' / 'run_illustrated_publish_flow.py'
PUBLISH_SCRIPT = PUBLISHER_ROOT / 'scripts' / 'publish_markdown.py'


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True)


def parse_json_output(proc: subprocess.CompletedProcess[str]) -> dict:
    text = (proc.stdout or '').strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {'raw_stdout': text, 'stderr': (proc.stderr or '').strip()}


def fail(stage: str, proc: subprocess.CompletedProcess[str], **extra: object) -> int:
    payload = {
        'ok': False,
        'stage': stage,
        'returncode': proc.returncode,
        'stdout': (proc.stdout or '').strip(),
        'stderr': (proc.stderr or '').strip(),
    }
    payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description='Unified illustrated WeChat publishing skill entry')
    parser.add_argument('--article', required=True)
    parser.add_argument('--output-dir', default='')
    parser.add_argument('--title', default='')
    parser.add_argument('--density', default='medium', choices=['light', 'medium', 'heavy'])
    parser.add_argument('--max-body-slots', type=int, default=4)
    parser.add_argument('--existing-generated-plan', default='')
    parser.add_argument('--generate', action='store_true')
    parser.add_argument('--publisher-config', default='')
    parser.add_argument('--cover-image', default='')
    parser.add_argument('--image-state', default='')
    parser.add_argument('--check', action='store_true', help='Run publisher --check after flow')
    parser.add_argument('--publish', action='store_true', help='Publish to WeChat drafts after flow')
    args = parser.parse_args()

    article_path = Path(args.article).expanduser().resolve()
    if not article_path.exists():
        print(json.dumps({'ok': False, 'error': f'文章不存在: {article_path}'}, ensure_ascii=False, indent=2))
        return 1

    flow_cmd = [
        sys.executable,
        str(FLOW_SCRIPT),
        '--article', str(article_path),
        '--density', args.density,
        '--max-body-slots', str(args.max_body_slots),
    ]
    if args.output_dir.strip():
        flow_cmd.extend(['--output-dir', args.output_dir.strip()])
    if args.title.strip():
        flow_cmd.extend(['--title', args.title.strip()])
    if args.existing_generated_plan.strip():
        flow_cmd.extend(['--existing-generated-plan', args.existing_generated_plan.strip()])
    if args.generate:
        flow_cmd.append('--generate')
    if args.check:
        flow_cmd.append('--publisher-check')
    if args.publisher_config.strip():
        flow_cmd.extend(['--publisher-config', args.publisher_config.strip()])
    if args.cover_image.strip():
        flow_cmd.extend(['--cover-image', args.cover_image.strip()])
    if args.image_state.strip():
        flow_cmd.extend(['--image-state', args.image_state.strip()])

    flow_proc = run_cmd(flow_cmd)
    if flow_proc.returncode != 0:
        return fail('illustrated-flow', flow_proc, command=flow_cmd)
    flow_result = parse_json_output(flow_proc)

    publish_result: dict = {}
    if args.publish:
        generated_plan = str(flow_result.get('generated_plan_path') or '').strip()
        if not generated_plan:
            print(json.dumps({
                'ok': False,
                'stage': 'publish',
                'error': '没有可发布的 generated plan；请提供 --existing-generated-plan 或加 --generate',
                'flow': flow_result,
            }, ensure_ascii=False, indent=2))
            return 1

        publish_cmd = [
            sys.executable,
            str(PUBLISH_SCRIPT),
            '--file', str(article_path),
            '--illustration-plan', generated_plan,
        ]
        if args.publisher_config.strip():
            publish_cmd.extend(['--config', args.publisher_config.strip()])
        if args.cover_image.strip():
            publish_cmd.extend(['--cover-image', args.cover_image.strip()])
        if args.image_state.strip():
            publish_cmd.extend(['--image-state', args.image_state.strip()])

        publish_proc = run_cmd(publish_cmd)
        if publish_proc.returncode != 0:
            return fail('publish', publish_proc, command=publish_cmd, flow=flow_result)
        publish_result = parse_json_output(publish_proc)

    payload = {
        'ok': True,
        'flow': flow_result,
        'publish_result': publish_result,
        'next_action': None,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

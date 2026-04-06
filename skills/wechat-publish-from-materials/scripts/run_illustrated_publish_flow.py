#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
PUBLISHER_ROOT = SKILL_ROOT.parent / 'wechat-draft-publisher'

BUILD_PLAN = SCRIPT_DIR / 'build_illustration_plan.py'
GENERATE = SCRIPT_DIR / 'generate_article_illustrations.py'
HANDOFF = SCRIPT_DIR / 'handoff_to_publisher.py'
PUBLISH_CHECK = PUBLISHER_ROOT / 'scripts' / 'publish_markdown.py'


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True)


def parse_json_output(proc: subprocess.CompletedProcess[str]) -> dict:
    text = (proc.stdout or '').strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {'raw_stdout': text}


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


def ensure_output_dir(path: str | None, article_path: Path) -> Path:
    if path:
        out = Path(path).expanduser().resolve()
    else:
        out = (article_path.parent / f'{article_path.stem}-illustration-flow').resolve()
    out.mkdir(parents=True, exist_ok=True)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description='Run article -> illustration plan -> optional generation -> optional publisher check')
    parser.add_argument('--article', required=True)
    parser.add_argument('--output-dir', default='')
    parser.add_argument('--title', default='')
    parser.add_argument('--density', default='medium', choices=['light', 'medium', 'heavy'])
    parser.add_argument('--max-body-slots', type=int, default=4)
    parser.add_argument('--existing-generated-plan', default='')
    parser.add_argument('--generate', action='store_true', help='Actually generate illustrations via the configured bridge')
    parser.add_argument('--publisher-check', action='store_true', help='Run publisher --check when a generated plan is available')
    parser.add_argument('--publisher-config', default='')
    parser.add_argument('--cover-image', default='')
    parser.add_argument('--image-state', default='')
    parser.add_argument('--image-provider', default='', help='Image provider: minimax | jimeng | seedream | ark')
    parser.add_argument('--image-api-key', default='', help='Override API key for selected image provider')
    parser.add_argument('--image-base-url', default='', help='Override base URL for selected image provider')
    parser.add_argument('--image-model', default='', help='Override model for selected image provider')
    parser.add_argument('--prompt-optimizer', default='', help='MiniMax only: override prompt_optimizer')
    args = parser.parse_args()

    article_path = Path(args.article).expanduser().resolve()
    if not article_path.exists():
        print(json.dumps({'ok': False, 'error': f'文章不存在: {article_path}'}, ensure_ascii=False, indent=2))
        return 1

    output_dir = ensure_output_dir(args.output_dir, article_path)
    plan_path = output_dir / 'illustration-plan.json'
    slots_path = output_dir / 'illustration-slots.json'
    prompts_path = output_dir / 'illustration-prompts.md'
    generated_plan_path = output_dir / 'illustration-plan.generated.json'

    build_cmd = [
        sys.executable,
        str(BUILD_PLAN),
        '--article', str(article_path),
        '--output', str(plan_path),
        '--visual-density', args.density,
        '--max-body-slots', str(args.max_body_slots),
    ]
    build_proc = run_cmd(build_cmd)
    if build_proc.returncode != 0:
        return fail('build-plan', build_proc, command=build_cmd)

    slots_cmd = [
        sys.executable,
        str(SCRIPT_DIR / 'build_illustration_slots.py'),
        '--article', str(article_path),
        '--density', args.density,
        '--slots-output', str(slots_path),
        '--prompts-output', str(prompts_path),
    ]
    if args.title.strip():
        slots_cmd.extend(['--title', args.title.strip()])
    slots_proc = run_cmd(slots_cmd)
    if slots_proc.returncode != 0:
        return fail('build-slots', slots_proc, command=slots_cmd)

    generation_mode = 'skipped'
    generation_result: dict = {}
    effective_generated_plan = ''

    if args.existing_generated_plan.strip():
        effective_generated_plan = str(Path(args.existing_generated_plan).expanduser().resolve())
        generation_mode = 'external-plan'
    elif args.generate:
        gen_cmd = [
            sys.executable,
            str(GENERATE),
            '--plan', str(plan_path),
            '--output-dir', str(output_dir),
            '--slots-file', str(slots_path),
            '--merged-plan-output', str(generated_plan_path),
        ]
        if args.image_provider.strip():
            gen_cmd.extend(['--image-provider', args.image_provider.strip()])
        if args.image_api_key.strip():
            gen_cmd.extend(['--image-api-key', args.image_api_key.strip()])
        if args.image_base_url.strip():
            gen_cmd.extend(['--image-base-url', args.image_base_url.strip()])
        if args.image_model.strip():
            gen_cmd.extend(['--image-model', args.image_model.strip()])
        if args.prompt_optimizer.strip():
            gen_cmd.extend(['--prompt-optimizer', args.prompt_optimizer.strip()])
        gen_proc = run_cmd(gen_cmd)
        if gen_proc.returncode != 0:
            return fail('generate-illustrations', gen_proc, command=gen_cmd)
        generation_result = parse_json_output(gen_proc)
        effective_generated_plan = str(generated_plan_path)
        generation_mode = 'generated'
    else:
        gen_cmd = [
            sys.executable,
            str(GENERATE),
            '--plan', str(plan_path),
            '--output-dir', str(output_dir),
            '--slots-file', str(slots_path),
            '--dry-run',
        ]
        if args.image_provider.strip():
            gen_cmd.extend(['--image-provider', args.image_provider.strip()])
        if args.image_model.strip():
            gen_cmd.extend(['--image-model', args.image_model.strip()])
        if args.image_base_url.strip():
            gen_cmd.extend(['--image-base-url', args.image_base_url.strip()])
        dry_proc = run_cmd(gen_cmd)
        if dry_proc.returncode != 0:
            return fail('generate-dry-run', dry_proc, command=gen_cmd)
        generation_result = parse_json_output(dry_proc)
        generation_mode = 'dry-run'

    handoff_cmd = [
        sys.executable,
        str(HANDOFF),
        '--draft', str(article_path),
    ]
    if args.cover_image.strip():
        handoff_cmd.extend(['--cover-image', args.cover_image.strip()])
    if effective_generated_plan:
        handoff_cmd.extend(['--illustration-plan', effective_generated_plan])
    if args.image_state.strip():
        handoff_cmd.extend(['--image-state', args.image_state.strip()])
    handoff_proc = run_cmd(handoff_cmd)
    if handoff_proc.returncode != 0:
        return fail('handoff-command', handoff_proc, command=handoff_cmd)

    publisher_check_result: dict = {}
    if args.publisher_check and effective_generated_plan:
        publish_cmd = [
            sys.executable,
            str(PUBLISH_CHECK),
            '--check',
            '--file', str(article_path),
            '--illustration-plan', effective_generated_plan,
        ]
        if args.publisher_config.strip():
            publish_cmd.extend(['--config', args.publisher_config.strip()])
        if args.cover_image.strip():
            publish_cmd.extend(['--cover-image', args.cover_image.strip()])
        if args.image_state.strip():
            publish_cmd.extend(['--image-state', args.image_state.strip()])
        publish_proc = run_cmd(publish_cmd)
        if publish_proc.returncode != 0:
            return fail('publisher-check', publish_proc, command=publish_cmd)
        publisher_check_result = parse_json_output(publish_proc)

    payload = {
        'ok': True,
        'article': str(article_path),
        'output_dir': str(output_dir),
        'plan_path': str(plan_path),
        'slots_path': str(slots_path),
        'prompts_path': str(prompts_path),
        'generation_mode': generation_mode,
        'image_provider': args.image_provider or 'minimax',
        'generated_plan_path': effective_generated_plan,
        'generation_result': generation_result,
        'handoff_command': (handoff_proc.stdout or '').strip(),
        'publisher_check': publisher_check_result,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Prepare workflow context bundles for wechat-article-workflow.

This version keeps the legacy combined bundle for compatibility,
while also generating stage-specific context files so downstream steps
can adopt progressive disclosure instead of one-shot full injection.
"""
import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path('/root/obsidian-vault/Projects/Active/微信公众号文章自动化发布')
SKILL_ROOT = Path('/root/.openclaw/skills/wechat-article-workflow')

STAGE_FILES = {
    'stage1_core': [
        PROJECT_ROOT / '00-主线与流程/17-默认执行链-v2.md',
        PROJECT_ROOT / '02-个人上下文库/01-主线与价值观.md',
        PROJECT_ROOT / '02-个人上下文库/04-表达偏好.md',
        PROJECT_ROOT / '02-个人上下文库/05-人物定位.md',
    ],
    'stage2_samples': [
        PROJECT_ROOT / '03-样板库/02-外部样板/01-外部样板使用地图-v1.md',
    ],
    'stage3_evidence': [
        PROJECT_ROOT / '02-个人上下文库/02-真实项目经历.md',
        PROJECT_ROOT / '02-个人上下文库/03-失败教训.md',
    ],
    'stage4_finish': [
        PROJECT_ROOT / '00-主线与流程/16-公众号内容质量门-v1.md',
        PROJECT_ROOT / '00-主线与流程/12-配图状态机-v1.md',
        PROJECT_ROOT / '00-主线与流程/13-飞书预览稿到微信发布稿转换规则-v1.md',
        PROJECT_ROOT / '00-主线与流程/14-草稿箱后验收清单-v1.md',
    ],
}

RUN_RECORD_HINTS = ['观点卡', '证据包', '样例说明', '成稿候选']
STAGE_SEQUENCE = ['stage1_core', 'stage2_samples', 'stage3_evidence', 'stage4_finish']
STAGE_PURPOSE = {
    'stage1_core': '先定方向：只对齐主线、人设、表达偏好与默认执行链。',
    'stage2_samples': '方向稳定后，再补主样板 / 辅样板的结构参考。',
    'stage3_evidence': '起草前再补真实经历、失败教训、观点卡与证据包。',
    'stage4_finish': '进入预览 / 发布前，再补质量门、排版与验收规则。',
}


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8') if path.exists() else f'[缺失文件] {path}'


def slugify(text: str) -> str:
    text = re.sub(r'[^\w\-\u4e00-\u9fff]+', '-', text.strip())
    text = re.sub(r'-{2,}', '-', text).strip('-')
    return text[:40] or 'workflow'


def collect_run_records(record_dir: Path) -> list[Path]:
    if not record_dir.exists() or not record_dir.is_dir():
        return []
    files = []
    for p in sorted(record_dir.glob('*.md')):
        if any(hint in p.name for hint in RUN_RECORD_HINTS):
            files.append(p)
    return files


def load_input_text(input_text: str = '', input_file: str = '') -> str:
    text = input_text
    if input_file:
        p = Path(input_file)
        if p.exists() and p.is_file():
            text = p.read_text(encoding='utf-8')
    return text


def render_stage_context(
    stage_name: str,
    topic: str,
    input_mode: str,
    loaded_input_text: str,
    files: list[Path],
    record_files: list[Path] | None = None,
) -> str:
    parts = []
    parts.append(f'# {stage_name} context\n')
    parts.append(f'- topic: {topic or "（未提供）"}')
    parts.append(f'- input_mode: {input_mode}')
    parts.append(f'- purpose: {STAGE_PURPOSE.get(stage_name, "") }\n')

    parts.append('## 当前输入\n')
    parts.append(loaded_input_text.strip() or '（未提供额外输入文本）')

    parts.append('\n## 本阶段说明\n')
    parts.append(STAGE_PURPOSE.get(stage_name, ''))
    parts.append('不要把后续阶段的材料平均混入当前阶段。')

    parts.append('\n## 本阶段文件\n')
    for p in files:
        parts.append(f'\n### {p.name}\n')
        parts.append(read_text(p))

    if record_files:
        parts.append('\n## 贴题运行记录\n')
        for p in record_files:
            parts.append(f'\n### {p.name}\n')
            parts.append(read_text(p))

    return '\n'.join(parts)


def render_combined_context(
    topic: str,
    input_mode: str,
    loaded_input_text: str,
    progressive_context: dict[str, Any],
) -> str:
    parts = []
    parts.append('# Workflow Context Bundle\n')
    parts.append(f'- input_mode: {input_mode}')
    parts.append(f'- topic: {topic or "（未提供）"}')
    parts.append(f'- generated_at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')

    parts.append('## 当前输入\n')
    parts.append(loaded_input_text.strip() or '（未提供额外输入文本）')

    parts.append('\n## 渐进式披露规则\n')
    parts.append('1. 先用最小上下文定方向，不要一上来全量灌入。')
    parts.append('2. 方向稳定后，再补样板。')
    parts.append('3. 起草时再补真实经历、失败教训与证据包。')
    parts.append('4. 预览 / 发布前，再补质量门与后链规则。')

    parts.append('\n## 阶段文件索引\n')
    for stage in STAGE_SEQUENCE:
        info = progressive_context[stage]
        parts.append(f"- {stage}: {info['path']}\n  - purpose: {info['purpose']}")

    parts.append('\n## 固定口径\n')
    parts.append('- `wechat-article` 只作为抓参考文、拆样板、提取内容的辅助能力，不充当创作主流程的大脑。')
    parts.append('- 用户自己的主线、真实经历、失败教训优先于外部样板。')
    parts.append('- 外部样板只借结构、节奏、冲突推进和收口，不直接照搬作者腔调。')
    parts.append('- 封面与配图判断后置到发布前状态机，不前置为写作必经步骤。')

    parts.append('\n## 下一步\n')
    parts.append('1. Stage 1 先收点和定方向')
    parts.append('2. Stage 2 再补样板')
    parts.append('3. Stage 3 再进入正文起草')
    parts.append('4. Stage 4 再推进预览与发布')

    return '\n'.join(parts)


def prepare_context_bundle(
    input_mode: str,
    topic: str = '',
    input_text: str = '',
    input_file: str = '',
    record_dir: str = '',
    output_dir: str = str(SKILL_ROOT / 'output'),
) -> dict[str, Any]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    loaded_input_text = load_input_text(input_text=input_text, input_file=input_file)
    record_files = collect_run_records(Path(record_dir)) if record_dir else []

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base = slugify(topic or input_mode)

    context_file = out_dir / f'{timestamp}_{base}_workflow_context.md'
    manifest_file = out_dir / f'{timestamp}_{base}_workflow_manifest.json'
    topic_tpl = SKILL_ROOT / 'templates/topic-pick-template.md'
    angle_tpl = SKILL_ROOT / 'templates/angle-brief-template.md'

    progressive_context: dict[str, Any] = {}
    for stage in STAGE_SEQUENCE:
        stage_path = out_dir / f'{timestamp}_{base}_{stage}.md'
        extra_records = record_files if stage == 'stage3_evidence' else []
        stage_path.write_text(
            render_stage_context(
                stage_name=stage,
                topic=topic,
                input_mode=input_mode,
                loaded_input_text=loaded_input_text,
                files=STAGE_FILES[stage],
                record_files=extra_records,
            ),
            encoding='utf-8',
        )
        progressive_context[stage] = {
            'path': str(stage_path),
            'purpose': STAGE_PURPOSE[stage],
            'files': [str(p) for p in STAGE_FILES[stage]] + [str(p) for p in extra_records],
        }

    context_file.write_text(
        render_combined_context(
            topic=topic,
            input_mode=input_mode,
            loaded_input_text=loaded_input_text,
            progressive_context=progressive_context,
        ),
        encoding='utf-8',
    )

    manifest = {
        'input_mode': input_mode,
        'topic': topic,
        'input_text': loaded_input_text,
        'context_bundle': str(context_file),
        'topic_pick_template': str(topic_tpl),
        'angle_brief_template': str(angle_tpl),
        'record_dir': record_dir,
        'record_files': [str(p) for p in record_files],
        'progressive_context': progressive_context,
        'stage_sequence': STAGE_SEQUENCE,
        'current_context_stage': 'stage1_core',
        'next_stage': 'topic_pick',
        'stages': {},
        'downstream': {
            'preview_skill': 'material-to-graphic-report',
            'publish_skill': 'wechat-draft-publisher'
        }
    }
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    manifest['manifest_file'] = str(manifest_file)
    return manifest


def main():
    parser = argparse.ArgumentParser(description='Prepare progressive context bundle for wechat-article-workflow')
    parser.add_argument('--input-mode', choices=['digest', 'article', 'topic', 'materials'], required=True)
    parser.add_argument('--topic', default='')
    parser.add_argument('--input-text', default='')
    parser.add_argument('--input-file', default='')
    parser.add_argument('--record-dir', default='')
    parser.add_argument('--output-dir', default=str(SKILL_ROOT / 'output'))
    args = parser.parse_args()

    manifest = prepare_context_bundle(
        input_mode=args.input_mode,
        topic=args.topic,
        input_text=args.input_text,
        input_file=args.input_file,
        record_dir=args.record_dir,
        output_dir=args.output_dir,
    )
    print(manifest['context_bundle'])
    print(manifest['manifest_file'])


if __name__ == '__main__':
    main()

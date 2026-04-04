#!/usr/bin/env python3
"""Build a compact draft handoff bundle from workflow manifest.

This script does NOT call any external LLM API.
It only packages the minimum writing-ready materials for the current agent/model.
"""
import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from prepare_context import prepare_context_bundle
from path_config import resolve_output_dir, resolve_project_root, resolve_skill_root

SKILL_ROOT = resolve_skill_root(__file__)
PROJECT_ROOT = resolve_project_root(__file__)


def set_project_root(project_root: Path) -> None:
    global PROJECT_ROOT, MAINLINE_FILE, PROJECTS_FILE, FAILURES_FILE, STYLE_FILE, ROLE_FILE
    PROJECT_ROOT = project_root
    MAINLINE_FILE = PROJECT_ROOT / '02-个人上下文库/01-主线与价值观.md'
    PROJECTS_FILE = PROJECT_ROOT / '02-个人上下文库/02-真实项目经历.md'
    FAILURES_FILE = PROJECT_ROOT / '02-个人上下文库/03-失败教训.md'
    STYLE_FILE = PROJECT_ROOT / '02-个人上下文库/04-表达偏好.md'
    ROLE_FILE = PROJECT_ROOT / '02-个人上下文库/05-人物定位.md'

MAINLINE_FILE = PROJECT_ROOT / '02-个人上下文库/01-主线与价值观.md'
PROJECTS_FILE = PROJECT_ROOT / '02-个人上下文库/02-真实项目经历.md'
FAILURES_FILE = PROJECT_ROOT / '02-个人上下文库/03-失败教训.md'
STYLE_FILE = PROJECT_ROOT / '02-个人上下文库/04-表达偏好.md'
ROLE_FILE = PROJECT_ROOT / '02-个人上下文库/05-人物定位.md'


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def save_json(path: Path, obj: dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def slugify(text: str) -> str:
    text = re.sub(r'[^\w\-\u4e00-\u9fff]+', '-', text.strip())
    text = re.sub(r'-{2,}', '-', text).strip('-')
    return text[:40] or 'workflow'


def read_if_exists(path_str: str) -> str:
    if not path_str:
        return ''
    p = Path(path_str)
    return p.read_text(encoding='utf-8') if p.exists() else ''


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8') if path.exists() else ''


def extract_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == heading.strip():
            start = i + 1
            break
    if start is None:
        return ''

    collected = []
    base_level = heading.lstrip().split(' ')[0].count('#')
    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith('#'):
            level = stripped.split(' ')[0].count('#')
            if level <= base_level:
                break
        collected.append(line)
    return '\n'.join(collected).strip()


def extract_bullets(text: str) -> list[str]:
    bullets = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('- '):
            bullets.append(stripped[2:].strip())
    return bullets


def first_nonempty_paragraph(text: str) -> str:
    parts = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    return parts[0] if parts else ''


def compact_lines(lines: list[str], limit: int = 4) -> list[str]:
    result = []
    seen = set()
    for line in lines:
        x = line.strip()
        if not x or x in seen:
            continue
        seen.add(x)
        result.append(x)
        if len(result) >= limit:
            break
    return result


def select_relevant_project_sections(topic: str) -> list[tuple[str, str]]:
    text = read_text(PROJECTS_FILE)
    sections: list[tuple[str, str]] = []
    current_title = None
    current_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith('## '):
            if current_title:
                sections.append((current_title, '\n'.join(current_lines).strip()))
            current_title = line[3:].strip()
            current_lines = []
        elif current_title:
            current_lines.append(line)
    if current_title:
        sections.append((current_title, '\n'.join(current_lines).strip()))

    keywords = [k for k in ['数字员工', '工作流', '上岗', '接进', '分工', 'OpenClaw', '小龙虾', '公众号', '写作', '知识库', '判断', '系统'] if k in topic]
    if not keywords:
        keywords = ['数字员工', '工作流', '判断']

    scored = []
    for title, body in sections:
        score = 0
        haystack = f'{title}\n{body}'
        for kw in keywords:
            score += haystack.count(kw) * 3
        if '后来形成的判断' in haystack:
            score += 1
        scored.append((score, title, body))

    scored.sort(key=lambda x: x[0], reverse=True)
    picked = [(title, body) for score, title, body in scored[:2] if score > 0]
    if not picked:
        for title, body in sections:
            if '项目1' in title or '项目3' in title:
                picked.append((title, body))
        if not picked:
            picked = [(title, body) for title, body in sections[:2]]
    return picked[:2]


def build_project_evidence(topic: str) -> str:
    blocks = []
    for title, body in select_relevant_project_sections(topic):
        essence = first_nonempty_paragraph(extract_section(body, '### 这件事本质上是什么'))
        did = compact_lines(extract_bullets(extract_section(body, '### 我实际做了什么')), limit=3)
        pitfalls = compact_lines(extract_bullets(extract_section(body, '### 我在这个项目里踩过的坑')), limit=3)
        judgments = compact_lines(extract_bullets(extract_section(body, '### 后来形成的判断')), limit=3)
        parts = [f'### {title}']
        if essence:
            parts.append(f'- 本质：{essence}')
        for item in did:
            parts.append(f'- 我实际做过：{item}')
        for item in pitfalls:
            parts.append(f'- 我踩过的坑：{item}')
        for item in judgments:
            parts.append(f'- 后来形成的判断：{item}')
        blocks.append('\n'.join(parts))
    return '\n\n'.join(blocks)


def build_failure_evidence(topic: str) -> list[str]:
    text = read_text(FAILURES_FILE)
    lessons = []
    current = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('### '):
            current = stripped[4:].strip()
            lessons.append(current)
    keywords = [k for k in ['信号', '写', '工作流', '系统', '材料', '样板', '主线'] if k in topic or k in text]
    picked = []
    for lesson in lessons:
        score = sum(1 for kw in keywords if kw in lesson)
        picked.append((score, lesson))
    picked.sort(key=lambda x: x[0], reverse=True)
    result = [x[1] for x in picked[:4] if x[1]]
    return compact_lines(result, limit=4)


def build_mainline_summary() -> list[str]:
    text = read_text(MAINLINE_FILE)
    bullets = []
    bullets.extend(compact_lines(extract_bullets(extract_section(text, '## 我真正想追的问题')), limit=3))
    bullets.extend(compact_lines(extract_bullets(extract_section(text, '## 我做选择时更看重什么')), limit=3))
    first = first_nonempty_paragraph(extract_section(text, '## 当前长期主线'))
    if first:
        bullets.insert(0, first)
    return compact_lines(bullets, limit=5)


def build_style_constraints() -> list[str]:
    style = read_text(STYLE_FILE)
    role = read_text(ROLE_FILE)
    picked = []
    picked.extend(compact_lines(extract_bullets(extract_section(style, '## 写稿规则')), limit=4))
    picked.extend(compact_lines(extract_bullets(extract_section(style, '## 明确禁忌')), limit=4))
    picked.extend(compact_lines(extract_bullets(extract_section(role, '## 我写给谁')), limit=3))
    picked.extend(compact_lines(extract_bullets(extract_section(role, '## 我想提供什么价值')), limit=3))
    return compact_lines(picked, limit=8)


def pick_selected_angle(manifest: dict[str, Any]) -> dict[str, Any] | None:
    selected_id = manifest.get('selected_angle_id')
    for opt in manifest.get('angle_options', []) or []:
        if opt.get('id') == selected_id:
            return opt
    return None


def build_progressive_context_index(manifest: dict[str, Any]) -> str:
    progressive = manifest.get('progressive_context') or {}
    lines = []
    for key in ['stage1_core', 'stage2_samples', 'stage3_evidence', 'stage4_finish']:
        item = progressive.get(key)
        if item:
            lines.append(f'- {key}: {item.get("path", "") }')
            lines.append(f'  - purpose: {item.get("purpose", "") }')
    return '\n'.join(lines) if lines else '（未提供渐进式上下文索引）'


def build_expression_requirements(selected_angle: dict[str, Any]) -> str:
    enhancement = selected_angle.get('expression_enhancement') or {}
    guards = '\n'.join([f'- {x}' for x in enhancement.get('guardrails', [])]) or '- 只借表达能力，不照搬外部作者腔调。'
    return f"""- 当前文章类型：{enhancement.get('article_kind', '（未标记）')}
- 表达增强强度：{enhancement.get('strength', '（未标记）')}
- 标题增强：{enhancement.get('headline', '（未提供）')}
- 开头增强：{enhancement.get('lede', '（未提供）')}
- 类比增强：{enhancement.get('analogy', '（未提供）')}
- 结尾增强：{enhancement.get('ending', '（未提供）')}
- 护栏：
{guards}
"""


def build_handoff_bundle(manifest: dict[str, Any]) -> str:
    topic = manifest.get('topic') or '（未提供主题）'
    input_mode = manifest.get('input_mode') or 'unknown'
    input_text = (manifest.get('input_text') or '').strip() or '（无额外输入文本）'
    stages = manifest.get('stages', {})
    topic_pick = read_if_exists(stages.get('topic_pick', ''))
    guide = read_if_exists(str(SKILL_ROOT / 'references/draft-writing-guide.md'))

    selected_angle = pick_selected_angle(manifest)
    if not selected_angle:
        raise ValueError('还没有选定观点方向；请先在 angle menu 中选择 A/B/C，再生成 draft handoff。')

    mainline = build_mainline_summary()
    projects = build_project_evidence(topic)
    failures = build_failure_evidence(topic)
    style_constraints = build_style_constraints()

    mainline_block = '\n'.join([f'- {x}' for x in mainline])
    failures_block = '\n'.join([f'- {x}' for x in failures])
    style_block = '\n'.join([f'- {x}' for x in style_constraints])
    outline_block = '\n'.join([f'- {x}' for x in selected_angle.get('outline', [])])
    evidence_block = '\n'.join([f'- {x}' for x in selected_angle.get('must_keep', [])])
    boundaries_block = '\n'.join([f'- {x}' for x in selected_angle.get('boundaries', [])])
    progressive_index = build_progressive_context_index(manifest)
    expression_requirements = build_expression_requirements(selected_angle)

    return f"""# 直接起草包

## 你现在要做什么
请直接写一篇可继续进入飞书预览链的公众号正文。

- input_mode: {input_mode}
- topic: {topic}
- 输入补充: {input_text}
- 已选观点方向: {selected_angle.get('id')}. {selected_angle.get('name')}
- generated_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 输出要求
1. 直接输出完整正文，不要解释过程。
2. 不要复述“我读了哪些文件”“下面是选题卡/表达卡/观点菜单”。
3. 不要混入工作流说明、标题候选、图像提示词、交付备注。
4. 尽量像一个亲历者在写，而不是像整理员在汇总。
5. 如果真实经历不够，不要编造细节。
6. 外部样板只增强表达，不覆盖用户自己的口吻。
7. 标题和开头优先抓冲突、代价、误解、反常识，不写空泛正确话。
8. 默认遵循渐进式披露：当前正文阶段重点使用贴题证据与必要样板，不要把所有背景平均摊平。

## 当前选中的点
{topic_pick}

## 已选观点方向
- 核心主张：{selected_angle.get('core_claim')}
- 更像的标题句：{selected_angle.get('title_line')}
- 文章类型：{selected_angle.get('article_type')}

## 表达增强要求
{expression_requirements}

## 渐进式上下文索引
{progressive_index}

## 建议结构
{outline_block}

## 必须保住的内容
{evidence_block}

## 不要写歪的边界
{boundaries_block}

## 必须保住的长期主线
{mainline_block}

## 优先可调用的真实项目经历
{projects}

## 可直接借用的失败教训
{failures_block}

## 口吻与表达约束
{style_block}

## 起草时一定要做到
{guide}

## 最后提醒
- 开头尽快亮出判断，但不要固定成同一句式反复使用；可按题目灵活从判断、误解、场景、反常识事实、问题切入。
- 中间至少带一个真实项目感的锚点。
- 允许打 1 个强类比，把复杂问题讲清，但不要连续堆类比。
- 结尾要收回到更稳的判断，而不是空喊口号。
- 请尽量留下一句值得被转述的话。
- 如果要写得更像本人，优先使用贴题的自然判断句；只有当这篇真的包含认知修正、误判后修正或经验回看时，再用“我后来越来越确定……”。
"""


def main():
    parser = argparse.ArgumentParser(description='Build compact draft handoff bundle from workflow manifest (no external LLM)')
    parser.add_argument('--manifest', help='Existing workflow manifest')
    parser.add_argument('--input-mode', choices=['digest', 'article', 'topic', 'materials'])
    parser.add_argument('--topic', default='')
    parser.add_argument('--input-text', default='')
    parser.add_argument('--input-file', default='')
    parser.add_argument('--record-dir', default='')
    parser.add_argument('--project-root', default='')
    parser.add_argument('--output-dir', default='')
    args = parser.parse_args()
    set_project_root(resolve_project_root(__file__, args.project_root))

    manifest_path: Path
    if args.manifest:
        manifest_path = Path(args.manifest)
        manifest = load_json(manifest_path)
    else:
        if not args.input_mode:
            raise ValueError('未提供 --manifest 时，必须提供 --input-mode')
        prepared = prepare_context_bundle(
            input_mode=args.input_mode,
            topic=args.topic,
            input_text=args.input_text,
            input_file=args.input_file,
            record_dir=args.record_dir,
            output_dir=args.output_dir,
            project_root=args.project_root,
        )
        manifest_path = Path(prepared['manifest_file'])
        manifest = load_json(manifest_path)

    stages = manifest.setdefault('stages', {})
    if not stages.get('topic_pick') or not stages.get('angle_menu'):
        raise ValueError('请先运行 prepare_briefs.py 生成选题卡和观点菜单')

    output_dir = resolve_output_dir(__file__, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base = slugify(manifest.get('topic') or manifest.get('input_mode') or 'workflow')

    handoff_path = output_dir / f'{timestamp}_{base}.draft_handoff.md'
    handoff_path.write_text(build_handoff_bundle(manifest), encoding='utf-8')

    manifest['stages']['draft_handoff'] = str(handoff_path)
    manifest['current_context_stage'] = 'stage3_evidence'
    manifest['next_stage'] = 'draft_by_current_agent'
    manifest['workflow_only'] = True
    save_json(manifest_path, manifest)

    print(str(handoff_path))
    print(str(manifest_path))


if __name__ == '__main__':
    main()

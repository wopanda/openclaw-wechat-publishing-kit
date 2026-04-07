#!/usr/bin/env python3
"""Build illustration slots + prompt pack from markdown article."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from illustration_core import (
    NEGATIVE_DEFAULT,
    article_claim,
    compose_prompt,
    compose_prompt_zh,
    default_aspect,
    default_body_limit,
    extract_title,
    hero_scene_for_cover,
    hero_scene_for_section,
    pick_visual_type,
    purpose_en,
    purpose_text,
    purpose_zh,
    scene_hint_en,
    scene_hint_zh,
    section_priority,
    split_sections,
    style_goal,
    style_goal_zh,
    supporting_elements,
    supporting_elements_en,
    summarize,
)


def cap_slots(slots: list[dict], density: str) -> list[dict]:
    if not slots:
        return slots
    cover = [slot for slot in slots if slot.get('slot_id') == 'cover_01']
    body = [slot for slot in slots if slot.get('slot_id') != 'cover_01']
    limit = default_body_limit(density)
    ranked = sorted(body, key=lambda slot: (-slot.get('priority', 0), slot.get('order', 0)))[:limit]
    keep_ids = {slot['slot_id'] for slot in ranked}
    kept_body = [slot for slot in body if slot['slot_id'] in keep_ids]
    return cover + kept_body


def build_slot(index: int, heading: str, content: str, article_title: str, claim: str, density: str, total_sections: int) -> dict:
    is_cover = index == 0
    is_last = index == total_sections - 1
    visual_type = pick_visual_type(heading, content, is_cover=is_cover, is_last=is_last)
    section_name = '开头' if is_cover else heading
    hero_scene = hero_scene_for_cover(article_title, claim) if is_cover else hero_scene_for_section(heading, content, visual_type)
    purpose = purpose_text(heading, visual_type, is_cover=is_cover)
    purpose_hint = purpose_en(visual_type)
    element_labels = supporting_elements(f'{heading} {content}')
    element_en = supporting_elements_en(element_labels)
    aspect = default_aspect(visual_type, density)
    style = style_goal(visual_type)
    slot_id = 'cover_01' if is_cover else f'sec{index+1:02d}_img_01'
    anchor = '标题下方' if is_cover else '对应段落之后'
    source = claim if is_cover else summarize(content, 120)
    why_here = '开头需要先建立主题感和阅读预期' if is_cover else f'这一段在推进“{heading}”，仅靠文字理解速度会变慢'
    zh_brief = f'{section_name}配图，类型为{visual_type}。主画面：{hero_scene}。这张图主要用于{purpose}。'
    main_en = compose_prompt(
        visual_type,
        scene_hint_en(heading, content, visual_type, is_cover=is_cover),
        purpose_hint,
        style,
        aspect,
        element_en,
    )
    main_zh = compose_prompt_zh(
        visual_type,
        scene_hint_zh(heading, content, visual_type, is_cover=is_cover),
        purpose_zh(visual_type),
        style_goal_zh(visual_type),
        aspect,
        element_labels,
    )
    priority = 999 if is_cover else section_priority(heading, content, visual_type, index, total_sections)

    return {
        'slot_id': slot_id,
        'section': section_name,
        'anchor': anchor,
        'visual_type': visual_type,
        'purpose': purpose,
        'source_paragraph': source,
        'scene_description': hero_scene,
        'prompt_basis': {
            'article_claim': claim,
            'why_image_here': why_here,
            'hero_scene': hero_scene,
            'supporting_elements': element_labels,
            'style_goal': style,
        },
        'insert_after_heading': '' if is_cover else heading,
        'position': '' if is_cover else heading,
        'prompt': {
            'zh_brief': zh_brief,
            'main_zh': main_zh,
            'main_en': main_en,
            'negative_en': NEGATIVE_DEFAULT,
        },
        'aspect_ratio': aspect,
        'style': style,
        'caption': purpose,
        'image_state': 'article-specific',
        'priority': priority,
        'order': index,
    }


def render_prompt_md(article_title: str, slots: list[dict]) -> str:
    lines = [f'# Illustration Prompts｜{article_title}', '']
    for slot in slots:
        basis = slot['prompt_basis']
        prompt = slot['prompt']
        lines.extend([
            f"## {slot['slot_id']}｜{slot['visual_type']}",
            f"- 用途：{slot['purpose']}",
            f"- 位置：{slot['section']} / {slot['anchor']}",
            f"- 文章主张：{basis['article_claim']}",
            f"- 为什么这里需要图：{basis['why_image_here']}",
            f"- 主画面：{basis['hero_scene']}",
            f"- 辅助元素：{', '.join(basis['supporting_elements']) if basis['supporting_elements'] else '无'}",
            f"- 优先级：{slot.get('priority', 0)}",
            f"- 中文设计说明：{prompt['zh_brief']}",
            '',
            '### Main prompt (ZH)',
            prompt.get('main_zh', prompt['main_en']),
            '',
            '### Main prompt (EN fallback)',
            prompt['main_en'],
            '',
            '### Negative prompt (EN)',
            prompt['negative_en'],
            '',
        ])
    return '\n'.join(lines).strip() + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(description='Build illustration slot plan from markdown article')
    parser.add_argument('--article', required=True)
    parser.add_argument('--title', default='')
    parser.add_argument('--density', default='medium', choices=['light', 'medium', 'heavy'])
    parser.add_argument('--slots-output', required=True)
    parser.add_argument('--prompts-output', required=True)
    args = parser.parse_args()

    article_path = Path(args.article)
    text = article_path.read_text(encoding='utf-8')
    article_title = args.title.strip() or extract_title(text) or article_path.stem
    claim = article_claim(text, article_title)
    sections = split_sections(text)
    if not sections:
        sections = [{'heading': '开头', 'content': text, 'level': 1}]

    slots = [
        build_slot(i, section['heading'], section['content'], article_title, claim, args.density, len(sections))
        for i, section in enumerate(sections)
    ]
    slots = cap_slots(slots, args.density)

    slots_payload = {
        'article_title': article_title,
        'article_claim': claim,
        'visual_density': args.density,
        'slots': slots,
    }
    Path(args.slots_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.prompts_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.slots_output).write_text(json.dumps(slots_payload, ensure_ascii=False, indent=2), encoding='utf-8')
    Path(args.prompts_output).write_text(render_prompt_md(article_title, slots), encoding='utf-8')
    print(json.dumps({
        'ok': True,
        'article_title': article_title,
        'article_claim': claim,
        'slot_count': len(slots),
        'slots_output': args.slots_output,
        'prompts_output': args.prompts_output,
    }, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

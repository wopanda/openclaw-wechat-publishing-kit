#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from illustration_core import (
    NEGATIVE_DEFAULT,
    NEGATIVE_DEFAULT_ZH,
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


def build_plan(article_text: str, title: str, density: str, max_body_slots: int) -> dict:
    claim = article_claim(article_text, title)
    sections = split_sections(article_text)
    if not sections:
        sections = [{'heading': '开头', 'content': article_text, 'level': 1}]

    built_slots: list[dict] = []
    for idx, section in enumerate(sections):
        is_cover = idx == 0
        heading = section['heading']
        content = section['content']
        visual_type = pick_visual_type(heading, content, is_cover=is_cover, is_last=idx == len(sections) - 1)
        aspect = default_aspect(visual_type, density)
        style = style_goal(visual_type)
        style_zh = style_goal_zh(visual_type)
        purpose = purpose_text(heading, visual_type, is_cover=is_cover)
        hero_scene = hero_scene_for_cover(title, claim) if is_cover else hero_scene_for_section(heading, content, visual_type)
        element_labels = supporting_elements(f'{heading} {content}')
        element_labels_en = supporting_elements_en(element_labels)
        prompt_en = compose_prompt(
            visual_type,
            scene_hint_en(heading, content, visual_type, is_cover=is_cover),
            purpose_en(visual_type),
            style,
            aspect,
            element_labels_en,
        )
        prompt_zh = compose_prompt_zh(
            visual_type,
            scene_hint_zh(heading, content, visual_type, is_cover=is_cover),
            purpose_zh(visual_type),
            style_zh,
            aspect,
            element_labels,
        )
        priority = 999 if is_cover else section_priority(heading, content, visual_type, idx, len(sections))

        built_slots.append({
            'slot_id': 'cover_01' if is_cover else f'sec{idx+1:02d}_img_01',
            'title': '封面插图' if is_cover else heading,
            'insert_after_heading': '' if is_cover else heading,
            'position': '' if is_cover else heading,
            'purpose': purpose,
            'visual_type': visual_type,
            'scene_description': hero_scene,
            'prompt_basis': {
                'article_claim': claim,
                'why_image_here': '开头需要建立主题感' if is_cover else f'“{heading}”这段需要更快建立理解',
                'hero_scene': hero_scene,
                'supporting_elements': element_labels,
                'style_goal': style,
            },
            'prompt_cn': prompt_zh,
            'prompt_en': prompt_en,
            'aspect_ratio': aspect,
            'style': style,
            'style_zh': style_zh,
            'caption': purpose,
            'negative_prompt': NEGATIVE_DEFAULT_ZH,
            'negative_prompt_en': NEGATIVE_DEFAULT,
            'prompt': prompt_zh,
            'source_paragraph': claim if is_cover else summarize(content, 120),
            'image_state': 'article-specific',
            'priority': priority,
            'order': idx,
        })

    cover = [slot for slot in built_slots if slot['slot_id'] == 'cover_01']
    body = [slot for slot in built_slots if slot['slot_id'] != 'cover_01']
    body_limit = min(max_body_slots, default_body_limit(density)) if max_body_slots > 0 else default_body_limit(density)
    body = sorted(body, key=lambda slot: (-slot.get('priority', 0), slot.get('order', 0)))[:body_limit]
    body = sorted(body, key=lambda slot: slot.get('order', 0))

    return {
        'article_title': title,
        'article_claim': claim,
        'visual_density': density,
        'slot_strategy': 'rhetorical-role-first-v4',
        'slots': cover + body,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Build a structured illustration plan for a WeChat article')
    parser.add_argument('--article', required=True, help='Markdown article path')
    parser.add_argument('--output', required=True, help='JSON output path')
    parser.add_argument('--visual-density', default='medium', choices=['light', 'medium', 'heavy'])
    parser.add_argument('--max-body-slots', type=int, default=4)
    args = parser.parse_args()

    markdown_text = Path(args.article).read_text(encoding='utf-8')
    title = extract_title(markdown_text)
    plan = build_plan(markdown_text, title, args.visual_density, max(0, int(args.max_body_slots)))

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
    print(str(out))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

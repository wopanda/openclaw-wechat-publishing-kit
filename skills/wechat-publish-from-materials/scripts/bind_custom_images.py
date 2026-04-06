#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r'[\w\u4e00-\u9fff]+', re.UNICODE)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def to_bool(value: Any, default: bool = False) -> bool:
    if value in (None, ''):
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}
    return bool(value)


def normalize_text_tokens(text: str) -> set[str]:
    words = [w.lower() for w in TOKEN_RE.findall(text or '')]
    return {w for w in words if len(w) >= 2}


def normalize_mode(value: str | None) -> str:
    raw = (value or '').strip().lower()
    if raw in {'', 'assist'}:
        return 'assist'
    if raw in {'manual', 'auto'}:
        return raw
    return 'assist'


def normalize_plan(data: Any) -> dict[str, Any]:
    if isinstance(data, dict) and isinstance(data.get('slots'), list):
        return data
    if isinstance(data, list):
        return {'slots': data}
    raise ValueError('计划文件格式错误：必须是包含 slots 的对象，或 slots 数组')


def normalize_custom_images(data: Any, default_mode: str) -> list[dict[str, Any]]:
    if isinstance(data, dict):
        if isinstance(data.get('custom_images'), list):
            items = data['custom_images']
        elif isinstance(data.get('images'), list):
            items = data['images']
        else:
            items = []
    elif isinstance(data, list):
        items = data
    else:
        items = []

    result: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        image_path = str(item.get('image_path') or item.get('local_path') or '').strip()
        image_url = str(item.get('image_url') or item.get('url') or '').strip()
        if not image_path and not image_url:
            continue
        image_id = str(item.get('image_id') or item.get('id') or '').strip() or f'image_{i+1:03d}'
        mode = normalize_mode(str(item.get('mode') or default_mode))
        if item.get('slot_id') or item.get('insert_after_heading'):
            mode = 'manual'
        if to_bool(item.get('auto_match'), default=False):
            mode = 'auto'
        result.append({
            'image_id': image_id,
            'image_path': image_path,
            'image_url': image_url,
            'slot_id': str(item.get('slot_id') or '').strip(),
            'insert_after_heading': str(item.get('insert_after_heading') or item.get('heading') or '').strip(),
            'note': str(item.get('note') or item.get('description') or '').strip(),
            'mode': mode,
            'auto_match': to_bool(item.get('auto_match'), default=mode in {'assist', 'auto'}),
        })
    return result


def normalize_analysis(data: Any) -> dict[str, dict[str, Any]]:
    if isinstance(data, dict) and isinstance(data.get('images'), list):
        items = data['images']
    elif isinstance(data, list):
        items = data
    else:
        items = []

    result: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        image_id = str(item.get('image_id') or item.get('id') or '').strip()
        image_path = str(item.get('image_path') or item.get('local_path') or '').strip()
        keys = [k for k in [image_id, image_path, Path(image_path).name if image_path else ''] if k]
        payload = {
            'caption': str(item.get('caption') or '').strip(),
            'visual_type': str(item.get('visual_type') or '').strip(),
            'tags': item.get('tags') if isinstance(item.get('tags'), list) else [],
            'contains_text': item.get('contains_text'),
        }
        for key in keys:
            result[key] = payload
    return result


def find_slot_by_id(slots: list[dict[str, Any]], slot_id: str) -> dict[str, Any] | None:
    target = slot_id.strip().lower()
    if not target:
        return None
    for slot in slots:
        sid = str(slot.get('slot_id') or '').strip().lower()
        if sid == target:
            return slot
    return None


def find_slot_by_heading(slots: list[dict[str, Any]], heading: str) -> dict[str, Any] | None:
    target = heading.strip().lower()
    if not target:
        return None
    for slot in slots:
        candidate = str(slot.get('insert_after_heading') or slot.get('section_heading') or slot.get('title') or '').strip().lower()
        if not candidate:
            continue
        if candidate == target or target in candidate or candidate in target:
            return slot
    return None


def slot_has_image(slot: dict[str, Any]) -> bool:
    for key in ('local_path', 'image_path', 'image_url', 'src'):
        if str(slot.get(key) or '').strip():
            return True
    return False


def build_slot_text(slot: dict[str, Any]) -> str:
    return ' '.join([
        str(slot.get('slot_id') or ''),
        str(slot.get('title') or ''),
        str(slot.get('purpose') or ''),
        str(slot.get('visual_type') or ''),
        str(slot.get('scene_description') or ''),
        str(slot.get('insert_after_heading') or ''),
        str(slot.get('section_heading') or ''),
    ])


def build_image_text(image: dict[str, Any], analysis: dict[str, Any] | None) -> str:
    file_name = Path(str(image.get('image_path') or image.get('image_url') or '')).name
    note = str(image.get('note') or '')
    normalized_note = note
    replacements = {
        '上下文': 'context',
        '差异': 'comparison difference compare',
        '对比': 'comparison compare',
        '封面': 'cover hero',
        '流程': 'process workflow',
        '结构': 'structure framework',
        '案例': 'case scenario',
        '总结': 'summary closing',
        '结尾': 'summary closing',
        '截图': 'screenshot interface',
    }
    for src, dst in replacements.items():
        normalized_note = normalized_note.replace(src, f'{src} {dst}')

    parts = [
        note,
        normalized_note,
        file_name,
        str((analysis or {}).get('caption') or ''),
        str((analysis or {}).get('visual_type') or ''),
        str((analysis or {}).get('recommended_usage') or ''),
        ' '.join(str(t) for t in ((analysis or {}).get('tags') or [])),
        ' '.join(str(t) for t in ((analysis or {}).get('dominant_subjects') or [])),
    ]
    return ' '.join(parts)


def score_slot(slot: dict[str, Any], image: dict[str, Any], analysis: dict[str, Any] | None) -> float:
    slot_tokens = normalize_text_tokens(build_slot_text(slot))
    image_tokens = normalize_text_tokens(build_image_text(image, analysis))

    if not slot_tokens or not image_tokens:
        base = 0.0
    else:
        overlap = len(slot_tokens.intersection(image_tokens))
        base = overlap / math.sqrt(len(slot_tokens) * len(image_tokens))

    visual_bonus = 0.0
    image_visual = str((analysis or {}).get('visual_type') or '').strip().lower()
    slot_visual = str(slot.get('visual_type') or '').strip().lower()
    visual_aliases = {
        '封面图': {'封面图', 'cover', 'hero'},
        '对比图': {'对比图', 'comparison', 'compare'},
        '流程图': {'流程图', 'process', 'workflow'},
        '结构图': {'结构图', 'structure', 'framework'},
        '案例场景图': {'案例场景图', 'case', 'scenario'},
        '证据图': {'证据图', 'evidence', 'proof'},
        '收口图': {'收口图', 'summary', 'closing', 'end'},
        '截图': {'截图', 'screenshot', 'interface', 'ui'},
        '照片': {'照片', 'photo', 'portrait'},
        '图表': {'图表', 'chart', 'graph'},
    }
    if image_visual and slot_visual:
        if image_visual == slot_visual:
            visual_bonus += 0.35
        else:
            matched_alias = False
            for aliases in visual_aliases.values():
                if image_visual in aliases and slot_visual in aliases:
                    visual_bonus += 0.28
                    matched_alias = True
                    break
            if not matched_alias and '流程' in image_visual and any(k in slot_visual for k in ['流程', '结构']):
                visual_bonus += 0.18

    note = str(image.get('note') or '').lower()
    usage = str((analysis or {}).get('recommended_usage') or '').lower()
    slot_id = str(slot.get('slot_id') or '').lower()
    slot_purpose = str(slot.get('purpose') or '').lower()
    slot_title = str(slot.get('title') or '').lower()
    slot_heading = str(slot.get('insert_after_heading') or '').lower()
    joined_slot = ' '.join([slot_id, slot_visual, slot_purpose, slot_title, slot_heading])
    joined_signal = ' '.join([note, usage])

    keyword_rules = [
        (('封面', 'cover'), ('cover', 'hero', '封面'), 0.5),
        (('对比', '差异', 'comparison', 'compare', 'context'), ('compare', 'comparison', '对比', '差异'), 0.45),
        (('流程', 'workflow', 'process'), ('process', 'workflow', '流程'), 0.45),
        (('结构', 'framework', 'structure'), ('structure', 'framework', '结构'), 0.45),
        (('案例', '场景', 'case', 'scenario'), ('case', 'scenario', '场景', '案例'), 0.35),
        (('总结', '结尾', 'summary', 'closing'), ('summary', 'closing', '结尾', '总结'), 0.35),
    ]
    for note_keys, slot_keys, bonus in keyword_rules:
        if any(k in joined_signal for k in note_keys) and any(k in joined_slot for k in slot_keys):
            visual_bonus += bonus
            break

    if any(k in joined_signal for k in ['说明', '解释', '逻辑', 'process flow', 'workflow']) and any(k in joined_slot for k in ['流程', '结构']):
        visual_bonus += 0.22

    if ('封面' in note or 'cover' in note) and not slot_id.startswith('cover'):
        visual_bonus -= 0.15

    return max(0.0, base + visual_bonus)


def apply_binding(
    slot: dict[str, Any],
    image: dict[str, Any],
    mode: str,
    score: float | None,
    analysis: dict[str, Any] | None,
) -> None:
    image_path = str(image.get('image_path') or '').strip()
    image_url = str(image.get('image_url') or '').strip()

    if image_path:
        slot['local_path'] = image_path
        slot.pop('image_url', None)
    elif image_url:
        slot['image_url'] = image_url
        slot.pop('local_path', None)

    slot['image_state'] = 'user-uploaded'
    slot['image_source'] = 'user_upload'
    slot['binding'] = {
        'mode': mode,
        'image_id': image.get('image_id'),
        'score': score,
        'note': image.get('note', ''),
        'analysis': analysis or {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Bind user-uploaded images into illustration plan slots')
    parser.add_argument('--plan', required=True, help='Base illustration plan json')
    parser.add_argument('--custom-images', required=True, help='Custom image mapping json')
    parser.add_argument('--output', required=True, help='Bound plan output path')
    parser.add_argument('--mode', default='assist', choices=['manual', 'assist', 'auto'], help='Default binding mode when slot not explicitly specified')
    parser.add_argument('--analysis-file', default='', help='Optional image analysis json (from MiniMax vision or other mechanism)')
    parser.add_argument('--min-score', type=float, default=0.18, help='Min score for auto binding')
    parser.add_argument('--allow-cover-auto', action='store_true', help='Allow auto matcher to bind non-manual images to cover slot')
    parser.add_argument('--no-replace-existing', action='store_true', help='Do not replace slots that already have an image')
    args = parser.parse_args()

    plan_path = Path(args.plan).expanduser().resolve()
    custom_path = Path(args.custom_images).expanduser().resolve()
    out_path = Path(args.output).expanduser().resolve()

    plan = normalize_plan(load_json(plan_path))
    slots = [slot for slot in plan.get('slots', []) if isinstance(slot, dict)]
    custom_images = normalize_custom_images(load_json(custom_path), default_mode=args.mode)
    analysis_lookup = normalize_analysis(load_json(Path(args.analysis_file).expanduser().resolve())) if args.analysis_file.strip() else {}

    used_slot_ids: set[str] = set()
    report = {
        'total_custom_images': len(custom_images),
        'manual_bound': [],
        'auto_bound': [],
        'unmatched': [],
        'recommendations': [],
        'skipped_existing_slot': [],
    }

    pending_auto: list[dict[str, Any]] = []

    for image in custom_images:
        image_id = image['image_id']
        analysis = analysis_lookup.get(image_id) or analysis_lookup.get(image.get('image_path', '')) or analysis_lookup.get(Path(str(image.get('image_path') or '')).name)

        target_slot = None
        binding_mode = image['mode']
        explicit_target_requested = False

        if image.get('slot_id'):
            explicit_target_requested = True
            target_slot = find_slot_by_id(slots, image['slot_id'])
            binding_mode = 'manual'
        elif image.get('insert_after_heading'):
            explicit_target_requested = True
            target_slot = find_slot_by_heading(slots, image['insert_after_heading'])
            binding_mode = 'manual'

        if target_slot is not None:
            slot_id = str(target_slot.get('slot_id') or '')
            if args.no_replace_existing and slot_has_image(target_slot):
                report['skipped_existing_slot'].append({'image_id': image_id, 'slot_id': slot_id})
                continue
            apply_binding(target_slot, image, binding_mode, score=1.0, analysis=analysis)
            used_slot_ids.add(slot_id)
            report['manual_bound'].append({'image_id': image_id, 'slot_id': slot_id})
            continue

        if explicit_target_requested:
            report['unmatched'].append({
                'image_id': image_id,
                'reason': 'manual_target_not_found',
                'slot_id': image.get('slot_id', ''),
                'insert_after_heading': image.get('insert_after_heading', ''),
            })
            continue

        pending_auto.append({
            'image': image,
            'analysis': analysis,
        })

    for entry in pending_auto:
        image = entry['image']
        analysis = entry['analysis']
        image_id = image['image_id']

        candidates: list[tuple[float, dict[str, Any]]] = []
        for slot in slots:
            slot_id = str(slot.get('slot_id') or '')
            if not slot_id:
                continue
            if slot_id in used_slot_ids:
                continue
            if args.no_replace_existing and slot_has_image(slot):
                continue
            if (not args.allow_cover_auto) and slot_id.lower().startswith('cover'):
                continue
            score = score_slot(slot, image, analysis)
            candidates.append((score, slot))

        candidates.sort(key=lambda x: x[0], reverse=True)
        if not candidates:
            report['unmatched'].append({'image_id': image_id, 'reason': 'no_available_slot'})
            continue

        top_score, top_slot = candidates[0]
        if top_score >= args.min_score:
            slot_id = str(top_slot.get('slot_id') or '')
            apply_binding(top_slot, image, mode='auto', score=round(top_score, 4), analysis=analysis)
            used_slot_ids.add(slot_id)
            report['auto_bound'].append({'image_id': image_id, 'slot_id': slot_id, 'score': round(top_score, 4)})
            continue

        recs = [
            {'slot_id': str(slot.get('slot_id') or ''), 'score': round(score, 4)}
            for score, slot in candidates[:3]
        ]
        report['recommendations'].append({'image_id': image_id, 'candidates': recs})
        report['unmatched'].append({'image_id': image_id, 'reason': 'score_below_threshold', 'best_score': round(top_score, 4)})

    plan['slots'] = slots
    plan['custom_image_binding'] = {
        'mode': args.mode,
        'min_score': args.min_score,
        'allow_cover_auto': bool(args.allow_cover_auto),
        'replace_existing': not args.no_replace_existing,
        'report': report,
    }

    save_json(out_path, plan)

    print(json.dumps({
        'ok': True,
        'plan': str(plan_path),
        'custom_images': str(custom_path),
        'output': str(out_path),
        'report': report,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

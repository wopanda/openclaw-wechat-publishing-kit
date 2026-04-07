from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _normalize_slots(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict) and 'slots' in data:
        slots = data['slots']
    elif isinstance(data, list):
        slots = data
    elif isinstance(data, dict) and 'slot_id' in data:
        slots = [data]
    else:
        raise ValueError('无法识别插图计划格式；请提供 slots 数组或包含 slots 的对象')
    if not isinstance(slots, list):
        raise ValueError('插图计划中的 slots 必须是数组')
    return [slot for slot in slots if isinstance(slot, dict)]


def load_illustration_plan(plan_path: str | Path) -> dict[str, Any]:
    path = Path(plan_path).expanduser().resolve()
    data = json.loads(path.read_text(encoding='utf-8'))
    slots = _normalize_slots(data)
    # Enrich slots: if generation_results exists at top level, inject remote_url back
    # into the matching slot so _pick_image_src can find it
    gen_results = data.get('generation_results') if isinstance(data, dict) else None
    if gen_results and isinstance(gen_results, list):
        slot_id_to_url = {
            r.get('slot_id'): r.get('remote_url')
            for r in gen_results
            if isinstance(r, dict) and r.get('remote_url')
        }
        for slot in slots:
            sid = str(slot.get('slot_id', '')).strip()
            if sid in slot_id_to_url:
                slot['remote_url'] = slot_id_to_url[sid]
    return {
        'path': str(path),
        'meta': data if isinstance(data, dict) else {},
        'slots': slots,
    }


def _pick_image_src(slot: dict[str, Any]) -> str:
    # Priority: local_path (local file) > image_path > remote_url > image_url > src
    # Local files are always used when available — they are stable and upload
    # reliably to WeChat.  remote_url is a fallback only when local_path is absent.
    # This ordering matters because after enrichment from generation_results,
    # a slot may carry both local_path (set by merge_results) AND remote_url
    # (set by load_illustration_plan enrichment).  We must prefer the local file.
    for key in ('local_path', 'image_path'):
        value = str(slot.get(key, '') or '').strip()
        if value:
            return value
    for key in ('remote_url', 'image_url', 'src'):
        value = str(slot.get(key, '') or '').strip()
        if value:
            return value
    return ''


def pick_cover_image_from_plan(plan: dict[str, Any]) -> str:
    for slot in plan.get('slots', []):
        slot_id = str(slot.get('slot_id', '')).lower()
        visual_type = str(slot.get('visual_type', ''))
        if not (slot_id.startswith('cover') or '封面' in visual_type):
            continue
        src = _pick_image_src(slot)
        if not src or src.startswith(('http://', 'https://')):
            continue
        path = Path(src).expanduser()
        if path.exists() and path.is_file():
            return str(path.resolve())
    return ''


def _render_slot_markdown(slot: dict[str, Any]) -> str:
    src = _pick_image_src(slot)
    if not src:
        return ''
    # Alt text: never expose internal slot_id; use clean "配图" or visual_type
    visual_type = str(slot.get('visual_type', '')).strip()
    if visual_type and visual_type not in ('illustration', '配图'):
        alt = visual_type
    else:
        alt = '配图'
    body = f'![{alt}]({src})'
    # Caption blockquotes are internal notes — do NOT surface in final markdown
    return body


def _find_heading_index(lines: list[str], heading_text: str) -> int:
    target = re.sub(r'^#+\s*', '', heading_text.strip())
    if not target:
        return -1
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith('#'):
            continue
        current = re.sub(r'^#+\s*', '', stripped)
        if current == target or target in current:
            return idx
    return -1


def merge_illustrations_into_markdown(markdown_body: str, plan: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    lines = markdown_body.splitlines()
    merged_slot_ids: list[str] = []
    skipped_slot_ids: list[str] = []
    missing_image_slot_ids: list[str] = []
    unmatched_heading_slot_ids: list[str] = []
    pending_by_line: dict[int, list[str]] = {}
    tail_blocks: list[str] = []

    for slot in plan.get('slots', []):
        slot_id = str(slot.get('slot_id', '')).strip()
        if not slot_id:
            continue
        if slot_id.lower().startswith('cover'):
            skipped_slot_ids.append(slot_id)
            continue
        block = _render_slot_markdown(slot)
        if not block:
            missing_image_slot_ids.append(slot_id)
            continue
        src = _pick_image_src(slot)
        if src and src in markdown_body:
            skipped_slot_ids.append(slot_id)
            continue
        heading = str(slot.get('insert_after_heading') or slot.get('section_heading') or slot.get('after_heading') or '').strip()
        if heading:
            idx = _find_heading_index(lines, heading)
            if idx >= 0:
                pending_by_line.setdefault(idx, []).append(block)
                merged_slot_ids.append(slot_id)
            else:
                # Try fuzzy match: use section name as fallback heading
                section = str(slot.get('section', '') or '').strip()
                if section:
                    idx = _find_heading_index(lines, section)
                    if idx >= 0:
                        pending_by_line.setdefault(idx, []).append(block)
                        merged_slot_ids.append(slot_id)
                        continue
                tail_blocks.append(block)
                unmatched_heading_slot_ids.append(slot_id)
                merged_slot_ids.append(slot_id)
        else:
            # No heading specified — try section as fallback before tailing
            section = str(slot.get('section', '') or '').strip()
            if section:
                idx = _find_heading_index(lines, section)
                if idx >= 0:
                    pending_by_line.setdefault(idx, []).append(block)
                    merged_slot_ids.append(slot_id)
                    continue
            tail_blocks.append(block)
            merged_slot_ids.append(slot_id)

    if not merged_slot_ids and not tail_blocks:
        return markdown_body, {
            'plan_used': True,
            'slot_count': len(plan.get('slots', [])),
            'body_slot_count': 0,
            'merged_slot_ids': merged_slot_ids,
            'skipped_slot_ids': skipped_slot_ids,
            'missing_image_slot_ids': missing_image_slot_ids,
            'unmatched_heading_slot_ids': unmatched_heading_slot_ids,
        }

    out_lines: list[str] = []
    for idx, line in enumerate(lines):
        out_lines.append(line)
        if idx in pending_by_line:
            for block in pending_by_line[idx]:
                out_lines.extend(['', block, ''])

    merged = '\n'.join(out_lines).strip()
    if tail_blocks:
        merged = merged + '\n\n' + '\n\n'.join(tail_blocks)
    merged = merged.strip() + '\n'

    return merged, {
        'plan_used': True,
        'slot_count': len(plan.get('slots', [])),
        'body_slot_count': len(merged_slot_ids),
        'merged_slot_ids': merged_slot_ids,
        'skipped_slot_ids': skipped_slot_ids,
        'missing_image_slot_ids': missing_image_slot_ids,
        'unmatched_heading_slot_ids': unmatched_heading_slot_ids,
    }

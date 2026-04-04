#!/usr/bin/env python3
"""Replace generated images back into a markdown prototype by slot_id.

This is the final bridge for:
slot-based prompt -> nano image generation -> slot-based markdown replacement.
"""
import argparse
import json
import re
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def render_image_block(title: str, image_path: str, caption: str) -> str:
    title_line = f'### {title}\n' if title else ''
    caption_line = f'\n> {caption}\n' if caption else ''
    return f"{title_line}![]({image_path}){caption_line}".rstrip() + "\n"


def replace_one(text: str, slot_id: str, title: str, image_path: str, caption: str) -> tuple[str, bool]:
    pattern = re.compile(
        rf"###\s*图片位[｜|]\s*{re.escape(slot_id)}[｜|].*?(?=\n###\s*图片位[｜|]|\n##\s|\Z)",
        flags=re.S,
    )
    replacement = render_image_block(title=title, image_path=image_path, caption=caption)
    new_text, count = pattern.subn(replacement, text, count=1)
    return new_text, count > 0


def main():
    parser = argparse.ArgumentParser(description='Replace generated images into markdown prototype by slot_id')
    parser.add_argument('--prototype-file', required=True, help='Markdown prototype file containing slot blocks')
    parser.add_argument('--results-file', required=True, help='JSON file returned by generate_with_nano.py')
    parser.add_argument('--slots-file', required=True, help='Original slots JSON file to recover title/caption')
    parser.add_argument('--output-file', required=True, help='Output markdown file after replacement')
    args = parser.parse_args()

    prototype_path = Path(args.prototype_file)
    results_path = Path(args.results_file)
    slots_path = Path(args.slots_file)
    output_path = Path(args.output_file)

    prototype = prototype_path.read_text(encoding='utf-8')
    results = load_json(results_path).get('results', [])
    slots_data = load_json(slots_path)
    slots = slots_data['slots'] if isinstance(slots_data, dict) and 'slots' in slots_data else slots_data
    slot_map = {slot['slot_id']: slot for slot in slots}

    replaced = []
    missing = []
    text = prototype

    for item in results:
        if item.get('status') != 'generated':
            continue
        slot_id = item['slot_id']
        slot = slot_map.get(slot_id, {})
        title = slot.get('title', slot_id)
        caption = slot.get('caption', '')
        image_path = item.get('local_path') or item.get('image_url')
        if not image_path:
            continue
        text, ok = replace_one(text, slot_id, title, image_path, caption)
        if ok:
            replaced.append(slot_id)
        else:
            missing.append(slot_id)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding='utf-8')
    print(json.dumps({
        'output_file': str(output_path),
        'replaced_slot_ids': replaced,
        'missing_slot_ids': missing,
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FILLER_PATTERNS = [
    (re.compile(r'(^|\n)\s*首先[，,：:]?\s*'), r'\1'),
    (re.compile(r'(^|\n)\s*其次[，,：:]?\s*'), r'\1'),
    (re.compile(r'(^|\n)\s*再次[，,：:]?\s*'), r'\1'),
    (re.compile(r'(^|\n)\s*最后[，,：:]?\s*'), r'\1'),
    (re.compile(r'值得注意的是[，,：:]?'), ''),
    (re.compile(r'需要指出的是[，,：:]?'), ''),
    (re.compile(r'综上所述[，,：:]?'), ''),
    (re.compile(r'总而言之[，,：:]?'), ''),
    (re.compile(r'总的来说[，,：:]?'), ''),
    (re.compile(r'不难发现[，,：:]?'), ''),
    (re.compile(r'可以看到[，,：:]?'), ''),
]

ABSTRACT_PATTERNS = [
    (re.compile(r'在([^，。；\n]{1,12})方面'), r'在\1上'),
    (re.compile(r'在([^，。；\n]{1,12})层面'), r'在\1上'),
    (re.compile(r'具有重要意义'), '很关键'),
    (re.compile(r'具有深远影响'), '影响会很大'),
]


def clean_text(text: str) -> str:
    out = text.replace('\r\n', '\n').replace('\r', '\n')

    for pattern, repl in FILLER_PATTERNS:
        out = pattern.sub(repl, out)

    for pattern, repl in ABSTRACT_PATTERNS:
        out = pattern.sub(repl, out)

    out = re.sub(r'\n{3,}', '\n\n', out)
    out = re.sub(r'[ \t]{2,}', ' ', out)
    out = re.sub(r'([。！？；])\1+', r'\1', out)
    out = re.sub(r'\n +', '\n', out)
    return out.strip() + '\n'


def main() -> int:
    ap = argparse.ArgumentParser(description='Built-in low-risk polish / de-AI cleanup for markdown')
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()

    src = Path(args.input)
    dst = Path(args.output)
    dst.parent.mkdir(parents=True, exist_ok=True)

    original = src.read_text(encoding='utf-8')
    polished = clean_text(original)
    dst.write_text(polished, encoding='utf-8')

    result = {
        'ok': True,
        'mode': 'builtin-low-risk',
        'input': str(src),
        'output': str(dst),
        'input_chars': len(original),
        'output_chars': len(polished),
        'note': '这是仓库内置的低风险去 AI 味清理器。更强的润色可继续替换为自定义 polish.command。',
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

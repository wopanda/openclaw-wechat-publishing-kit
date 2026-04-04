#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]
PUBLISHER_LIB = SKILLS_DIR / 'wechat-draft-publisher' / 'scripts' / 'lib'
if str(PUBLISHER_LIB) not in sys.path:
    sys.path.insert(0, str(PUBLISHER_LIB))

from article_parser import extract_main_body, extract_title, strip_leading_h1
from illustration_plan import load_illustration_plan, merge_illustrations_into_markdown


def main() -> int:
    parser = argparse.ArgumentParser(description='Merge generated illustrations into article markdown')
    parser.add_argument('--article', required=True, help='Original markdown article path')
    parser.add_argument('--illustration-plan', required=True, help='Generated illustration plan JSON path')
    parser.add_argument('--output', required=True, help='Merged markdown output path')
    parser.add_argument('--prepend-title', action='store_true', help='Prepend # title to the merged markdown')
    args = parser.parse_args()

    article_path = Path(args.article).expanduser().resolve()
    plan_path = Path(args.illustration_plan).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    markdown_text = article_path.read_text(encoding='utf-8')
    title = extract_title(markdown_text)
    article_body = extract_main_body(markdown_text)
    article_body = strip_leading_h1(article_body, expected_title=title)

    plan = load_illustration_plan(plan_path)
    merged_body, report = merge_illustrations_into_markdown(article_body, plan)
    final_markdown = f'# {title}\n\n{merged_body.strip()}\n' if args.prepend_title and title else merged_body

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(final_markdown, encoding='utf-8')

    print(json.dumps({
        'ok': True,
        'article': str(article_path),
        'illustration_plan': str(plan_path),
        'output': str(output_path),
        'title': title,
        'illustration_report': report,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

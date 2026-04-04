#!/usr/bin/env python3
"""Print a suggested handoff command to the publisher stage."""
from pathlib import Path
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--draft', required=True)
parser.add_argument('--cover-image', default='')
parser.add_argument('--body-image', action='append', default=[])
parser.add_argument('--image-state', default='')
args = parser.parse_args()

draft = Path(args.draft)
cmd = [
    'python3 scripts/publish_markdown.py',
    f'--file "{draft}"',
]
if args.cover_image:
    cmd.append(f'--cover-image "{args.cover_image}"')
for body_image in args.body_image:
    if str(body_image).strip():
        cmd.append(f'--body-image "{body_image}"')
if args.image_state.strip():
    cmd.append(f'--image-state "{args.image_state.strip()}"')
print(' \\\n  '.join(cmd))

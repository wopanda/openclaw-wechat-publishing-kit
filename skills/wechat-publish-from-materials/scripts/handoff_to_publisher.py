#!/usr/bin/env python3
"""Print a suggested handoff command to the publisher stage."""
from pathlib import Path
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--draft', required=True)
parser.add_argument('--cover-image', default='')
args = parser.parse_args()

draft = Path(args.draft)
cmd = [
    'python3 scripts/publish_markdown.py',
    f'--input "{draft}"',
]
if args.cover_image:
    cmd.append(f'--cover-image "{args.cover_image}"')
print(' \\\n  '.join(cmd))

#!/usr/bin/env python3
"""Build a minimal article brief from persona summary and reference extract."""
from pathlib import Path
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--persona', required=True)
parser.add_argument('--reference', required=True)
parser.add_argument('--topic', default='')
parser.add_argument('--output', required=True)
args = parser.parse_args()

persona = Path(args.persona).read_text(encoding='utf-8').strip()
reference = Path(args.reference).read_text(encoding='utf-8').strip()
out = f"# Article Brief\n\n## Topic\n- {args.topic or '待补'}\n\n## Persona Signals\n{persona[:1200]}\n\n## Reference Signals\n{reference[:1200]}\n"
Path(args.output).write_text(out, encoding='utf-8')
print(args.output)

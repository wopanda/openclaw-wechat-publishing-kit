#!/usr/bin/env python3
"""Extract a compact persona summary from a persona markdown file.

This is a light helper script for packaging/demo purposes.
"""
from pathlib import Path
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--input', required=True)
parser.add_argument('--output', required=True)
args = parser.parse_args()

text = Path(args.input).read_text(encoding='utf-8')
lines = [line.rstrip() for line in text.splitlines()]
out = ['# Persona Summary', '']
keep = False
for line in lines:
    if line.startswith('## '):
        keep = any(key in line for key in ['基础信息', '个人经历锚点', '推广品牌', '目标读者'])
    if keep:
        out.append(line)

Path(args.output).write_text('\n'.join(out).strip() + '\n', encoding='utf-8')
print(args.output)

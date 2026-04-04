#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
LIB_DIR = SCRIPT_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from config_loader import ConfigError, load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run optional polish / de-AI stage before WeChat draft publishing")
    parser.add_argument("--input", required=True, help="Input markdown path")
    parser.add_argument("--output", required=True, help="Output markdown path")
    parser.add_argument("--config", help="Path to config settings JSON or config directory")
    parser.add_argument("--command", help="Override polish command template; supports {input} and {output}")
    parser.add_argument("--copy-only", action="store_true", help="Bypass polish and copy input to output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(json.dumps({"ok": False, "error": f"输入文件不存在: {input_path}"}, ensure_ascii=False, indent=2))
        return 1

    if args.copy_only:
        output_path.write_text(input_path.read_text(encoding='utf-8'), encoding='utf-8')
        print(json.dumps({
            "ok": True,
            "mode": "copy-only",
            "input": str(input_path),
            "output": str(output_path),
        }, ensure_ascii=False, indent=2))
        return 0

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    polish_cfg = config.get('polish', {}) or {}
    command_template = args.command or polish_cfg.get('command', '')
    enabled = bool(args.command or polish_cfg.get('enabled', False))
    timeout_seconds = int(polish_cfg.get('timeout_seconds', 180) or 180)

    if not enabled or not str(command_template).strip():
        output_path.write_text(input_path.read_text(encoding='utf-8'), encoding='utf-8')
        print(json.dumps({
            "ok": True,
            "mode": "passthrough",
            "reason": "polish-disabled-or-command-missing",
            "input": str(input_path),
            "output": str(output_path),
        }, ensure_ascii=False, indent=2))
        return 0

    rendered = str(command_template).format(input=str(input_path), output=str(output_path))
    proc = subprocess.run(rendered, shell=True, capture_output=True, text=True, timeout=timeout_seconds)

    result = {
        "ok": proc.returncode == 0,
        "mode": "external-command",
        "input": str(input_path),
        "output": str(output_path),
        "command": rendered,
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }

    if proc.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if proc.returncode == 0 and (not output_path.exists() or output_path.stat().st_size == 0):
        result['ok'] = False
        result['error'] = '润色命令执行成功，但没有产出有效输出文件'
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1


if __name__ == '__main__':
    raise SystemExit(main())

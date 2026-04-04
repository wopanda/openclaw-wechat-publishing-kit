#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path


ENV_PROJECT_ROOT = 'WECHAT_ARTICLE_PROJECT_ROOT'
ENV_SKILL_ROOT = 'WECHAT_ARTICLE_SKILL_ROOT'


def resolve_skill_root(current_file: str) -> Path:
    env = os.environ.get(ENV_SKILL_ROOT, '').strip()
    if env:
        return Path(env).expanduser().resolve()
    return Path(current_file).resolve().parents[1]


def default_project_root(skill_root: Path) -> Path:
    return skill_root / 'project-template'


def resolve_project_root(current_file: str, cli_value: str = '') -> Path:
    if cli_value:
        return Path(cli_value).expanduser().resolve()
    env = os.environ.get(ENV_PROJECT_ROOT, '').strip()
    if env:
        return Path(env).expanduser().resolve()
    return default_project_root(resolve_skill_root(current_file)).resolve()


def resolve_output_dir(current_file: str, cli_value: str = '') -> Path:
    if cli_value:
        return Path(cli_value).expanduser().resolve()
    return resolve_skill_root(current_file) / 'output'

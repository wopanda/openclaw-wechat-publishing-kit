from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict


def _normalize(text: str) -> str:
    return (text or '').replace('\r\n', '\n').replace('\r', '\n').strip()


def _load_fallback_template(path_text: str | None, author: str) -> str:
    path_value = (path_text or '').strip()
    if not path_value:
        return ''
    path = Path(path_value).expanduser()
    if not path.exists() or not path.is_file():
        return ''
    raw = path.read_text(encoding='utf-8').strip()
    return raw.replace('{{author}}', author).strip() if raw else ''


def _detect_kind(title: str, body: str) -> str:
    text = f"{title}\n{body}"
    if any(token in text for token in ['怎么', '如何', '步骤', '清单', '技巧', '方法', '上手']):
        return 'practical'
    if any(token in text for token in ['案例', '复盘', '搭建', '系统', '过程', '项目', '踩坑']):
        return 'practice'
    if any(token in text for token in ['为什么', '机会', '判断', '未来', '会不会', '越来越', '不是']):
        return 'observation'
    return 'reflective'


def _detect_theme_clause(title: str, body: str) -> str:
    text = f"{title}\n{body}"
    if '判断' in text and '产品' in text:
        return '一个人的判断，怎么慢慢变成别人用得上的东西'
    if '判断' in text:
        return '一些判断，怎么慢慢长成真正有用的东西'
    if '内容' in text and '产品' in text:
        return '内容之外，真正能留下来的东西到底是什么'
    if any(token in text for token in ['自动化', '系统', '工作流']):
        return '一些想法，怎么一点点变成真的能跑起来的东西'
    if 'AI' in text and any(token in text for token in ['工作', '落地', '应用']):
        return 'AI 到底怎么真正走进具体工作里'
    if any(token in text for token in ['写作', '表达', '文章']):
        return '一些想法，怎么被更清楚地说出来'
    return '一些事情怎么慢慢想清楚'


def _render_variant(author: str, kind: str, clause: str) -> str:
    variants = {
        'observation': [
            f'我是{author}。',
            f'最近我常常在想，{clause}。',
            '写下这些，不是想急着给答案，只是想把一些还在发酵的想法先记下来。',
        ],
        'practical': [
            f'我是{author}。',
            '平时我会一边做，一边记，把那些真正有用、也真正容易卡住的地方写下来。',
            '如果刚好能帮你少走一点弯路，那就很好。',
        ],
        'practice': [
            f'我是{author}。',
            '有些事，只有自己做过一遍，才知道问题到底卡在哪里。',
            '所以我会把一路上的过程、卡点和体会，尽量写得具体一点。',
        ],
        'reflective': [
            f'我是{author}。',
            '有些东西，我会一边做，一边想，一边慢慢写下来。',
            '这不是标准答案，只是我当下的一些观察和体会。',
        ],
    }
    return '\n'.join(['**作者介绍**', '', *variants.get(kind, variants['reflective'])]).strip()


def build_signature_block(author: str, title: str, body: str, fallback_template_path: str | None = None) -> Dict[str, Any]:
    normalized_title = _normalize(title)
    normalized_body = _normalize(body)

    if not author.strip():
        fallback = _load_fallback_template(fallback_template_path, author)
        return {
            'text': fallback,
            'strategy': 'fallback-template' if fallback else 'empty',
            'variant': 'fallback',
            'source': (fallback_template_path or '').strip() or None,
        }

    if not normalized_title and not normalized_body:
        fallback = _load_fallback_template(fallback_template_path, author)
        return {
            'text': fallback,
            'strategy': 'fallback-template' if fallback else 'empty',
            'variant': 'fallback',
            'source': (fallback_template_path or '').strip() or None,
        }

    kind = _detect_kind(normalized_title, normalized_body)
    clause = _detect_theme_clause(normalized_title, normalized_body)
    rendered = _render_variant(author, kind, clause)
    if rendered:
        return {
            'text': rendered,
            'strategy': 'dynamic-heuristic',
            'variant': kind,
            'source': None,
        }

    fallback = _load_fallback_template(fallback_template_path, author)
    return {
        'text': fallback,
        'strategy': 'fallback-template' if fallback else 'empty',
        'variant': 'fallback',
        'source': (fallback_template_path or '').strip() or None,
    }

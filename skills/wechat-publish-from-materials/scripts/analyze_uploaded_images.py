#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
from pathlib import Path
from typing import Any

DEFAULT_TIMEOUT = 120.0
DEFAULT_MODEL = 'MiniMax-VL-01'
DEFAULT_BASE_URL = 'https://api.minimaxi.com'
OPENCLAW_CONFIG_PATHS = [
    Path.home() / '.openclaw' / 'openclaw.json',
    Path('/root/.openclaw/openclaw.json'),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def normalize_custom_images(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict):
        if isinstance(data.get('custom_images'), list):
            items = data['custom_images']
        elif isinstance(data.get('images'), list):
            items = data['images']
        else:
            items = []
    elif isinstance(data, list):
        items = data
    else:
        items = []

    out: list[dict[str, Any]] = []
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        image_path = str(item.get('image_path') or item.get('local_path') or '').strip()
        image_url = str(item.get('image_url') or item.get('url') or '').strip()
        if not image_path and not image_url:
            continue
        out.append({
            'image_id': str(item.get('image_id') or item.get('id') or f'image_{idx+1:03d}').strip(),
            'image_path': image_path,
            'image_url': image_url,
            'note': str(item.get('note') or item.get('description') or '').strip(),
        })
    return out


def resolve_minimax_config() -> dict[str, str]:
    for path in OPENCLAW_CONFIG_PATHS:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            continue
        provider = ((((data or {}).get('models') or {}).get('providers') or {}).get('minimax') or {})
        if isinstance(provider, dict):
            return {
                'api_key': str(provider.get('apiKey') or provider.get('api_key') or '').strip(),
                'base_url': str(provider.get('baseUrl') or provider.get('base_url') or '').strip(),
            }
    return {'api_key': '', 'base_url': ''}


def resolve_api_key(explicit: str) -> str:
    if explicit.strip():
        return explicit.strip()
    for env_name in ('MINIMAX_API_KEY', 'MINIMAX_APIKEY', 'ABAB_API_KEY'):
        value = os.environ.get(env_name, '').strip()
        if value:
            return value
    config = resolve_minimax_config()
    if config['api_key']:
        return config['api_key']
    raise RuntimeError('缺少 MiniMax 识图 API key；请传 --api-key 或配置 ~/.openclaw/openclaw.json 的 minimax provider')


def resolve_base_url(explicit: str) -> str:
    if explicit.strip():
        value = explicit.strip().rstrip('/')
    else:
        config = resolve_minimax_config()
        value = (config['base_url'] or DEFAULT_BASE_URL).rstrip('/')

    if value.endswith('/anthropic'):
        value = value[:-len('/anthropic')]
    return value


def guess_media_type(name: str) -> str:
    media_type = mimetypes.guess_type(name)[0] or 'image/jpeg'
    if media_type == 'image/jpg':
        media_type = 'image/jpeg'
    return media_type


def load_image_bytes(image_path: str, image_url: str) -> tuple[bytes, str, str]:
    if image_path:
        path = Path(image_path).expanduser().resolve()
        data = path.read_bytes()
        return data, guess_media_type(path.name), path.name
    from urllib import request as urllib_request

    req = urllib_request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib_request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
        content = resp.read()
        media_type = resp.headers.get('Content-Type', '').split(';', 1)[0].strip() or guess_media_type(image_url)
        return content, media_type, image_url.rsplit('/', 1)[-1] or 'image'


def extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r'\{.*\}', text, re.S)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except Exception:
        return {}


def infer_visual_type_from_text(text: str) -> tuple[str, str]:
    lowered = text.lower()
    rules = [
        (('封面', 'cover', 'hero', '主题视觉'), ('cover', '封面图')),
        (('对比', '差异', 'comparison', 'compare', 'before after'), ('comparison', '对比图')),
        (('流程', 'process', 'workflow', 'step', 'flowchart'), ('process', '流程图')),
        (('结构', 'framework', 'structure', 'architecture', 'mechanism'), ('structure', '结构图')),
        (('案例', '场景', 'case', 'scenario', 'scene'), ('case_scene', '案例场景图')),
        (('证据', '数据', 'evidence', 'proof'), ('evidence', '证据图')),
        (('总结', '收口', 'closing', 'summary'), ('summary', '收口图')),
        (('截图', 'screenshot', '界面', 'ui', 'interface'), ('screenshot', '截图')),
        (('照片', 'photo', '人物', 'portrait'), ('photo', '照片')),
        (('图表', 'chart', 'graph', 'infographic'), ('chart', '图表')),
    ]
    for keywords, result in rules:
        if any(keyword in lowered for keyword in keywords):
            return result
    return 'unknown', '未知'


def normalize_visual_type(value: Any, *fallback_texts: str) -> tuple[str, str]:
    raw = str(value or '').strip().lower()
    if raw:
        inferred_raw, inferred_zh = infer_visual_type_from_text(raw)
        if inferred_raw != 'unknown':
            return inferred_raw, inferred_zh
    combined = ' '.join(str(part or '') for part in fallback_texts if str(part or '').strip())
    inferred_raw, inferred_zh = infer_visual_type_from_text(combined)
    if inferred_raw != 'unknown':
        return inferred_raw, inferred_zh
    return 'unknown', '未知'


def normalize_bool(value: Any, fallback_text: str = '') -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value or '').strip().lower()
    if text in {'true', '1', 'yes', 'y', '有', '是'}:
        return True
    if text in {'false', '0', 'no', 'n', '无', '否', 'none', 'null'}:
        return False

    hint = fallback_text.lower()
    negative_patterns = [
        'without text', 'no text', 'text-free', 'no labels', 'without labels',
        '无文字', '没有文字', '无标题', '无标注',
    ]
    if any(token in hint for token in negative_patterns):
        return False

    positive_patterns = ['text', 'label', 'caption', 'poster', 'screenshot', 'ui', 'interface', '字幕', '标题', '文字', '标注']
    if any(token in hint for token in positive_patterns):
        return True

    return False


def _normalize_list_items(value: Any, *, max_items: int, lowercase: bool) -> list[str]:
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        items = re.split(r'[,;/\n]+', value)
    else:
        items = []

    out: list[str] = []
    for item in items:
        text = str(item or '').strip()
        if not text:
            continue
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\-\u4e00-\u9fff ]+', '', text)
        text = text.strip(' _-')
        if not text:
            continue
        if lowercase:
            text = text.lower()
        if text not in out:
            out.append(text)
        if len(out) >= max_items:
            break
    return out


def normalize_tags(value: Any, *, fallback_text: str) -> list[str]:
    tags = _normalize_list_items(value, max_items=8, lowercase=True)
    if tags:
        return tags
    fallback = _normalize_list_items(re.split(r'[,;/\n]+', fallback_text), max_items=6, lowercase=True)
    return fallback or ['unknown', 'article_illustration', 'wechat']


def normalize_subjects(value: Any, *, fallback_text: str, tags: list[str]) -> list[str]:
    subjects = _normalize_list_items(value, max_items=6, lowercase=False)
    if subjects:
        return subjects
    fallback = _normalize_list_items(re.split(r'[,;/\n]+', fallback_text), max_items=4, lowercase=False)
    if fallback:
        return fallback
    return tags[:3] or ['article illustration']


def apply_contains_text_post_rule(
    contains_text: bool,
    *,
    visual_type_raw: str,
    caption: str,
    recommended_usage: str,
    tags: list[str],
    dominant_subjects: list[str],
    note: str,
    file_name: str,
) -> bool:
    hint = ' '.join([
        visual_type_raw,
        caption,
        recommended_usage,
        ' '.join(tags),
        ' '.join(dominant_subjects),
        note,
        file_name,
    ]).lower()

    explicit_positive_tokens = [
        'poster', 'screenshot', 'screen', 'document', 'page', 'slide', 'subtitle', 'typography',
        'ocr', 'quoted text', 'paragraph', 'headline', '文字', '大段文字', '段落', '标题文字', '界面', '截图',
    ]
    weak_text_tokens = [
        'text', 'texts', 'label', 'labels', 'caption', 'captions', 'title', 'titles',
        'ui', 'interface', 'menu', 'button', '标注', '标题',
    ]
    explicit_negative_tokens = [
        'without text', 'no text', 'text-free', 'without labels', 'no labels',
        '无文字', '没有文字', '无标注', '无标题',
    ]
    abstract_diagram_tokens = [
        'abstract diagram', 'diagram', 'infographic', 'flowchart', 'process flow', 'process',
        'workflow', 'mapping', 'structure', 'architecture', 'data visualization', 'data flow',
        'nodes', 'connecting lines', 'flow lines', 'abstract icons', 'technical icons',
        'technical diagram', 'schematic', 'system architecture', 'network diagram',
        '逻辑', '流程', '结构', '图表', '架构', '数据流',
    ]

    if any(token in hint for token in explicit_negative_tokens):
        return False

    if visual_type_raw == 'screenshot':
        return True

    if visual_type_raw in {'cover', 'photo', 'case_scene', 'comparison', 'summary', 'evidence'}:
        return any(token in hint for token in explicit_positive_tokens)

    if visual_type_raw in {'process', 'structure', 'chart', 'unknown'}:
        if any(token in hint for token in explicit_positive_tokens):
            return True
        if any(token in hint for token in abstract_diagram_tokens):
            return False
        if any(token in hint for token in weak_text_tokens):
            return False
        return contains_text

    if any(token in hint for token in explicit_positive_tokens):
        return True
    if any(token in hint for token in weak_text_tokens):
        return contains_text

    return contains_text


def build_heuristic_analysis(image: dict[str, Any], *, file_name: str, model: str, base_url: str, reason: str) -> dict[str, Any]:
    note = str(image.get('note') or '').strip()
    image_path = str(image.get('image_path') or '')
    image_url = str(image.get('image_url') or '')
    basis_text = ' '.join(part for part in [note, file_name] if part).strip()
    visual_type_raw, visual_type = infer_visual_type_from_text(basis_text)

    subject_rules = [
        ('医生', 'doctor'), ('医疗', 'medical'), ('龙虾', 'lobster'), ('封面', 'cover'), ('流程', 'workflow'),
        ('比较', 'comparison'), ('对比', 'comparison'), ('结构', 'structure'), ('上下文', 'context'), ('文章', 'article'),
    ]
    dominant_subjects: list[str] = []
    lowered = basis_text.lower()
    for src, dst in subject_rules:
        if src in basis_text or dst in lowered:
            dominant_subjects.append(dst)
    if not dominant_subjects:
        dominant_subjects = ['article illustration']

    tags: list[str] = []
    for candidate in [visual_type_raw, *dominant_subjects]:
        normalized = str(candidate).strip().lower().replace(' ', '_')
        if normalized and normalized not in tags:
            tags.append(normalized)
    tags = tags[:6] or ['unknown', 'article_illustration', 'wechat']

    contains_text = any(token in lowered for token in ['text', '文字', '标题', 'screenshot', '截图'])
    caption_map = {
        'cover': 'Thematic cover illustration',
        'comparison': 'Context comparison illustration',
        'process': 'Workflow illustration',
        'structure': 'Structure explanation illustration',
        'case_scene': 'Case scene illustration',
        'evidence': 'Evidence supporting illustration',
        'summary': 'Closing summary illustration',
        'screenshot': 'Interface screenshot reference',
        'photo': 'Editorial photo reference',
        'chart': 'Chart reference illustration',
        'unknown': 'Article illustration candidate',
    }
    recommended_map = {
        'cover': '适合作为文章封面图位的候选图',
        'comparison': '适合作为对比说明段落的配图候选',
        'process': '适合作为流程说明段落的配图候选',
        'structure': '适合作为结构解释段落的配图候选',
        'case_scene': '适合作为案例场景段落的配图候选',
        'evidence': '适合作为证据支撑段落的配图候选',
        'summary': '适合作为结尾收束段落的配图候选',
        'screenshot': '更适合作为界面说明或截图引用',
        'photo': '可作为照片型素材候选，需要再确认风格一致性',
        'chart': '适合作为图表信息段落的配图候选',
        'unknown': '可先进入人工确认或仅作为推荐候选',
    }
    return {
        'image_id': str(image.get('image_id') or ''),
        'image_path': image_path,
        'image_url': image_url,
        'file_name': file_name,
        'status': 'fallback',
        'analysis_source': 'heuristic_fallback',
        'caption': caption_map.get(visual_type_raw, 'Article illustration candidate'),
        'visual_type': visual_type,
        'visual_type_raw': visual_type_raw,
        'tags': tags,
        'contains_text': contains_text,
        'recommended_usage': recommended_map.get(visual_type_raw, '可先进入人工确认或仅作为推荐候选'),
        'dominant_subjects': dominant_subjects,
        'reason': reason,
        'model': model,
        'base_url': base_url,
    }


def analyze_one(image: dict[str, Any], api_key: str, model: str, base_url: str) -> dict[str, Any]:
    image_id = image['image_id']
    image_path = image.get('image_path', '')
    image_url = image.get('image_url', '')
    note = image.get('note', '')

    file_name = Path(str(image_path or image_url or image_id)).name
    try:
        data, media_type, file_name = load_image_bytes(image_path, image_url)
    except Exception as exc:
        return build_heuristic_analysis(image, file_name=file_name, model=model, base_url=base_url, reason=f'load_image_failed: {exc}')

    b64 = base64.b64encode(data).decode('utf-8')
    prompt = (
        '请分析这张用户上传图片，目标是给微信公众号文章自动选图位。'
        '请只输出一个 JSON 对象，不要输出解释、不要加代码块。'
        'JSON 必须只包含这些键：caption, visual_type, tags, contains_text, recommended_usage, dominant_subjects。'
        '要求：caption 用简短英文；'
        'visual_type 只能是 cover/comparison/process/structure/case_scene/evidence/summary/screenshot/photo/chart/unknown 之一；'
        'tags 是 3 到 8 个小写英文短词数组；'
        'contains_text 是 true 或 false；'
        'recommended_usage 用简短中文；'
        'dominant_subjects 是数组。'
        f'用户补充说明：{note or "无"}。'
    )
    payload = {
        'prompt': prompt,
        'image_url': f'data:{media_type};base64,{b64}',
    }
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'MM-API-Source': 'OpenClaw',
    }
    url = f'{base_url.rstrip("/")}/v1/coding_plan/vlm'

    from urllib import error as urllib_error
    from urllib import request as urllib_request

    try:
        req = urllib_request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        with urllib_request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
            raw = json.loads(resp.read().decode('utf-8', 'ignore'))
    except urllib_error.HTTPError as exc:
        body = exc.read().decode('utf-8', 'ignore')
        return build_heuristic_analysis(image, file_name=file_name, model=model, base_url=base_url, reason=f'request_failed_http_{exc.code}: {body[:500]}')
    except Exception as exc:
        return build_heuristic_analysis(image, file_name=file_name, model=model, base_url=base_url, reason=f'request_failed: {exc}')

    base_resp = raw.get('base_resp') or {}
    if base_resp.get('status_code', 0) != 0:
        return build_heuristic_analysis(
            image,
            file_name=file_name,
            model=model,
            base_url=base_url,
            reason=f"api_error_{base_resp.get('status_code')}: {(base_resp.get('status_msg') or '').strip()}"
        )

    raw_text = str(raw.get('content') or '').strip()
    parsed = extract_json(raw_text)
    if not parsed:
        fallback = build_heuristic_analysis(image, file_name=file_name, model=model, base_url=base_url, reason='invalid_json_response')
        fallback['raw_text'] = raw_text[:2000]
        fallback['raw_response'] = json.dumps(raw, ensure_ascii=False)[:4000] if isinstance(raw, dict) else str(raw)[:4000]
        return fallback

    caption = str(parsed.get('caption') or '').strip()
    recommended_usage = str(parsed.get('recommended_usage') or '').strip()
    visual_type_raw, visual_type = normalize_visual_type(
        parsed.get('visual_type'),
        caption,
        recommended_usage,
        ' '.join(str(t) for t in (parsed.get('tags') or [])),
        ' '.join(str(t) for t in (parsed.get('dominant_subjects') or [])),
        note,
        file_name,
    )
    tag_fallback_text = ' '.join([
        visual_type_raw,
        caption,
        recommended_usage,
        ' '.join(str(t) for t in (parsed.get('dominant_subjects') or [])),
        note,
        file_name,
    ])
    tags = normalize_tags(parsed.get('tags'), fallback_text=tag_fallback_text)
    subject_fallback_text = ' '.join([
        caption,
        recommended_usage,
        ' '.join(tags),
        note,
    ])
    dominant_subjects = normalize_subjects(parsed.get('dominant_subjects'), fallback_text=subject_fallback_text, tags=tags)
    contains_text = normalize_bool(
        parsed.get('contains_text'),
        fallback_text=' '.join([
            caption,
            recommended_usage,
            ' '.join(tags),
            ' '.join(dominant_subjects),
            visual_type_raw,
        ])
    )
    contains_text = apply_contains_text_post_rule(
        contains_text,
        visual_type_raw=visual_type_raw,
        caption=caption,
        recommended_usage=recommended_usage,
        tags=tags,
        dominant_subjects=dominant_subjects,
        note=note,
        file_name=file_name,
    )
    if not caption:
        caption_map = {
            'cover': 'Thematic cover illustration',
            'comparison': 'Comparison illustration',
            'process': 'Process flow illustration',
            'structure': 'Structure explanation illustration',
            'case_scene': 'Case scene illustration',
            'evidence': 'Evidence supporting illustration',
            'summary': 'Closing summary illustration',
            'screenshot': 'Interface screenshot reference',
            'photo': 'Editorial photo reference',
            'chart': 'Chart reference illustration',
            'unknown': 'Article illustration candidate',
        }
        caption = caption_map.get(visual_type_raw, 'Article illustration candidate')
    if not recommended_usage:
        recommended_usage = build_heuristic_analysis(
            image,
            file_name=file_name,
            model=model,
            base_url=base_url,
            reason='normalize_usage',
        ).get('recommended_usage', '')
    return {
        'image_id': image_id,
        'image_path': image_path,
        'image_url': image_url,
        'file_name': file_name,
        'status': 'analyzed',
        'analysis_source': 'minimax_vision',
        'caption': caption,
        'visual_type': visual_type,
        'visual_type_raw': visual_type_raw,
        'tags': tags,
        'contains_text': contains_text,
        'recommended_usage': recommended_usage,
        'dominant_subjects': dominant_subjects,
        'model': model,
        'base_url': base_url,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Analyze uploaded images with MiniMax vision and export structured JSON')
    parser.add_argument('--custom-images', required=True, help='Custom image json file')
    parser.add_argument('--output', required=True, help='Analysis output json path')
    parser.add_argument('--api-key', default='', help='MiniMax vision api key')
    parser.add_argument('--model', default=os.environ.get('MINIMAX_VISION_MODEL', DEFAULT_MODEL))
    parser.add_argument('--base-url', default=os.environ.get('MINIMAX_VISION_BASE_URL', ''))
    args = parser.parse_args()

    custom_images = normalize_custom_images(load_json(Path(args.custom_images).expanduser().resolve()))
    if not custom_images:
        save_json(Path(args.output).expanduser().resolve(), {'images': []})
        print(json.dumps({'ok': True, 'images': [], 'output': str(Path(args.output).expanduser().resolve())}, ensure_ascii=False, indent=2))
        return 0

    warning = ''
    try:
        api_key = resolve_api_key(args.api_key)
    except Exception as exc:
        api_key = ''
        warning = str(exc)
    base_url = resolve_base_url(args.base_url)

    results = [analyze_one(item, api_key, args.model, base_url) for item in custom_images]
    payload = {'images': results}
    out = Path(args.output).expanduser().resolve()
    save_json(out, payload)
    print(json.dumps({'ok': True, 'output': str(out), 'images': results, 'warning': warning}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

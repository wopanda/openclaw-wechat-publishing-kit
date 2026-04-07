from __future__ import annotations

import re
from typing import Iterable

NEGATIVE_DEFAULT = (
    'watermark, random text, logo errors, blurry, low resolution, messy composition, '
    'cluttered background, unrelated people, cheap commercial advertising style, overdone sci-fi, '
    'neon cyberpunk, garish colors, too many visual elements'
)

NEGATIVE_DEFAULT_ZH = (
    '不要水印，不要中文文字，不要英文文字，不要数字，不要 logo，不要签名，不要标签，'
    '不要模糊，不要低清晰度，不要杂乱背景，不要无关人物，不要廉价广告感，不要赛博朋克霓虹，不要过度花哨'
)

PURPOSE_MAP = {
    '封面图': '建立主题感',
    '对比图': '展示变化或差异',
    '流程图': '解释步骤链路',
    '结构图': '解释结构关系',
    '证据图': '承接事实或数据',
    '案例场景图': '把抽象内容场景化',
    '收口图': '做结尾收束并固化判断',
}

PURPOSE_EN_MAP = {
    '封面图': 'establish the article theme',
    '对比图': 'show the contrast clearly',
    '流程图': 'explain the workflow clearly',
    '结构图': 'explain the structure clearly',
    '证据图': 'present evidence clearly',
    '案例场景图': 'ground the idea in a concrete scene',
    '收口图': 'land the conclusion strongly',
}

STYLE_MAP = {
    '封面图': 'premium editorial cover, business-tech visual, strong focal point, reserved title space',
    '对比图': 'business-tech editorial infographic, clean comparison layout, clear left-right contrast',
    '流程图': 'clean process illustration, editorial infographic, minimal clutter',
    '结构图': 'clean information architecture, modular editorial diagram, restrained palette',
    '证据图': 'report-style evidence cards, premium professional visual, readable hierarchy',
    '案例场景图': 'editorial scene illustration, grounded modern workplace visual, restrained colors',
    '收口图': 'restrained premium ending visual, calm strong finish, symbolic but clear',
}

STYLE_ZH_MAP = {
    '封面图': '编辑型封面感，商务科技气质，主体明确，预留标题空间，不要广告海报风',
    '对比图': '编辑型对比信息图，左右关系清楚，重点差异一眼可见，画面干净',
    '流程图': '步骤链路清楚，流程关系明确，像高质量编辑插图，不要复杂流程软件截图风',
    '结构图': '结构关系清楚，模块分层明确，信息架构感强，克制配色',
    '证据图': '像报告中的证据卡片，层级清楚，专业可信，不要花哨宣传风',
    '案例场景图': '真实工作场景感，现代办公室或数字工作台氛围，克制专业',
    '收口图': '结尾收束感强，克制、有判断感，适合作为文章最后一张图',
}

ASPECT_MAP = {
    '封面图': '16:9',
    '对比图': '4:3',
    '流程图': '4:3',
    '结构图': '4:3',
    '证据图': '1:1',
    '案例场景图': '4:3',
    '收口图': '16:9',
}

VISUAL_KEYWORDS = {
    '对比图': ['对比', '比较', '前后', '之前', '之后', '过去', '现在', '旧', '新', '变化', '差异', '转变'],
    '流程图': ['流程', '步骤', '链路', '路径', '怎么做', '如何做', '方法', '执行', '推进', '落地'],
    '结构图': ['结构', '框架', '组成', '模块', '系统', '层', '要素', '逻辑', '骨架'],
    '证据图': ['数据', '证据', '截图', '事实', '指标', '数字', '案例证明', '验证'],
    '案例场景图': ['案例', '场景', '用户', '团队', '客户', '办公室', '一天', '会议', '实操'],
    '收口图': ['总结', '结论', '最后', '意味着', '所以', '结果'],
}

SUPPORT_KEYWORDS = {
    '内容卡片': ['内容', '文章', '段落', '素材', '笔记', '卡片'],
    '流程箭头': ['流程', '步骤', '链路', '路径'],
    '数据卡片': ['数据', '指标', '证据', '事实'],
    '屏幕界面': ['系统', '界面', '后台', '面板', '工作台', '页面'],
    '人物协作': ['团队', '用户', '作者', '运营', '协作', '会议'],
    '模块结构': ['结构', '框架', '模块', '组成', '层级'],
}

SUPPORT_EN = {
    '内容卡片': 'content cards',
    '流程箭头': 'workflow arrows',
    '数据卡片': 'evidence cards',
    '屏幕界面': 'product interface panels',
    '人物协作': 'collaborative people silhouettes',
    '模块结构': 'modular blocks',
}

DOMAIN_MOTIFS = {
    'article content blocks': ['内容', '文章', '段落', '写作', '稿件'],
    'illustration slots': ['插图', '配图', '图片', '图位'],
    'workflow pipeline': ['流程', '链路', '步骤', '工作流'],
    'modular architecture': ['结构', '框架', '模块', '系统'],
    'evidence cards': ['数据', '证据', '事实', '截图'],
    'digital workspace': ['系统', '界面', '后台', '工作台', '页面'],
    'team collaboration': ['团队', '协作', '用户', '作者', '运营'],
}

DOMAIN_MOTIFS_ZH = {
    '内容卡片': ['内容', '文章', '段落', '写作', '稿件'],
    '插图区块': ['插图', '配图', '图片', '图位'],
    '流程链路': ['流程', '链路', '步骤', '工作流'],
    '模块结构': ['结构', '框架', '模块', '系统'],
    '证据卡片': ['数据', '证据', '事实', '截图'],
    '数字工作台': ['系统', '界面', '后台', '工作台', '页面'],
    '团队协作': ['团队', '协作', '用户', '作者', '运营'],
}


def clean_text(text: str) -> str:
    text = re.sub(r'```.*?```', ' ', text, flags=re.S)
    text = re.sub(r'`[^`]*`', ' ', text)
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', ' ', text)
    text = re.sub(r'\[[^\]]*\]\([^)]*\)', ' ', text)
    text = re.sub(r'[#>*_\-]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def summarize(text: str, limit: int = 80) -> str:
    return clean_text(text)[:limit]


def extract_title(markdown_text: str) -> str:
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('#'):
            return stripped.lstrip('#').strip()
        return stripped[:64]
    return '无标题'


def opening_paragraph(markdown_text: str, title: str) -> str:
    chunks = []
    started = False
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped.startswith('# '):
            started = True
            continue
        if stripped.startswith('## '):
            break
        if not started and not stripped:
            continue
        if stripped:
            chunks.append(stripped)
    text = clean_text(' '.join(chunks))
    if text.startswith(title):
        text = text[len(title):].strip(' ：:-')
    return text


def article_claim(markdown_text: str, title: str) -> str:
    intro = opening_paragraph(markdown_text, title)
    if intro:
        return intro[:72]
    clean = clean_text(markdown_text)
    if clean.startswith(title):
        clean = clean[len(title):].strip(' ：:-')
    return clean[:72] or title


def _extract_markdown_heading(stripped: str) -> tuple[str, int] | None:
    match = re.match(r'^(#{2,6})\s+(.+?)\s*$', stripped)
    if not match:
        return None
    return match.group(2).strip(), len(match.group(1))


def _extract_bold_heading(stripped: str) -> tuple[str, int] | None:
    match = re.match(r'^\*\*(.+?)\*\*$' , stripped)
    if not match:
        return None
    heading = clean_text(match.group(1))
    if not heading:
        return None
    if len(heading) > 40:
        return None
    return heading, 2


def split_sections(markdown_text: str) -> list[dict]:
    lines = markdown_text.splitlines()
    sections: list[dict] = []
    current_heading = '开头'
    buffer: list[str] = []
    level = 1
    seen_title = False

    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith('# '):
            seen_title = True
            continue

        heading_info = _extract_markdown_heading(stripped) or _extract_bold_heading(stripped)
        if heading_info:
            if clean_text('\n'.join(buffer)):
                sections.append({'heading': current_heading, 'content': '\n'.join(buffer).strip(), 'level': level})
            current_heading, level = heading_info
            buffer = []
            seen_title = True
            continue

        if not seen_title and not stripped:
            continue
        buffer.append(raw)

    if clean_text('\n'.join(buffer)):
        sections.append({'heading': current_heading, 'content': '\n'.join(buffer).strip(), 'level': level})

    return sections


def score_visual_types(heading: str, content: str, *, is_last: bool = False) -> dict[str, int]:
    text = f'{heading} {content}'
    scores = {name: 0 for name in VISUAL_KEYWORDS}
    for name, keywords in VISUAL_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[name] += 2 if kw in heading else 1

    if any(k in heading for k in ['为什么', '问题', '痛点']):
        scores['流程图'] += 1
        scores['案例场景图'] += 1
    if any(k in heading for k in ['怎么做', '方法', '步骤', '打法']):
        scores['流程图'] += 2
    if any(k in heading for k in ['框架', '结构', '组成', '系统']):
        scores['结构图'] += 2
    if is_last:
        scores['收口图'] += 2
    return scores


def pick_visual_type(heading: str, content: str, *, is_cover: bool = False, is_last: bool = False) -> str:
    if is_cover:
        return '封面图'
    scores = score_visual_types(heading, content, is_last=is_last)
    order = ['对比图', '流程图', '结构图', '证据图', '收口图', '案例场景图']
    best = max(order, key=lambda name: (scores[name], -order.index(name)))
    if scores[best] <= 0:
        return '收口图' if is_last else '案例场景图'
    return best


def supporting_elements(text: str, limit: int = 3) -> list[str]:
    found: list[str] = []
    for label, keywords in SUPPORT_KEYWORDS.items():
        if any(k in text for k in keywords):
            found.append(label)
    return found[:limit]


def supporting_elements_en(labels: Iterable[str]) -> list[str]:
    return [SUPPORT_EN.get(label, label) for label in labels]


def infer_motifs(text: str, limit: int = 3) -> list[str]:
    found: list[str] = []
    for label, keywords in DOMAIN_MOTIFS.items():
        if any(k in text for k in keywords):
            found.append(label)
    return found[:limit] or ['editorial composition']


def infer_motifs_zh(text: str, limit: int = 3) -> list[str]:
    found: list[str] = []
    for label, keywords in DOMAIN_MOTIFS_ZH.items():
        if any(k in text for k in keywords):
            found.append(label)
    return found[:limit] or ['编辑型构图']


def hero_scene_for_cover(title: str, claim: str) -> str:
    return f'{title} 的主题画面，核心判断：{claim[:40]}'


def hero_scene_for_section(heading: str, content: str, visual_type: str) -> str:
    snippet = summarize(content, 70) or heading
    if visual_type == '对比图':
        return f'围绕“{heading}”的对比画面：{snippet}'
    if visual_type == '流程图':
        return f'围绕“{heading}”的步骤链路画面：{snippet}'
    if visual_type == '结构图':
        return f'围绕“{heading}”的结构关系画面：{snippet}'
    if visual_type == '证据图':
        return f'围绕“{heading}”的证据承接画面：{snippet}'
    if visual_type == '收口图':
        return f'围绕“{heading}”的结论收束画面：{snippet}'
    return f'围绕“{heading}”的场景化画面：{snippet}'


def scene_hint_en(title: str, content: str, visual_type: str, *, is_cover: bool = False) -> str:
    motifs = infer_motifs(f'{title} {content}')
    motif_text = ', '.join(motifs)
    if is_cover:
        return f'central editorial theme scene with {motif_text}'
    if visual_type == '对比图':
        return f'side-by-side contrast between an old state and a new state, using {motif_text}'
    if visual_type == '流程图':
        return f'step-by-step workflow scene, using {motif_text}'
    if visual_type == '结构图':
        return f'modular structure scene, using {motif_text}'
    if visual_type == '证据图':
        return f'evidence-focused scene, using {motif_text}'
    if visual_type == '收口图':
        return f'ending summary scene, using {motif_text}'
    return f'grounded editorial scene, using {motif_text}'


def scene_hint_zh(title: str, content: str, visual_type: str, *, is_cover: bool = False) -> str:
    motifs = infer_motifs_zh(f'{title} {content}')
    motif_text = '、'.join(motifs)
    if is_cover:
        return f'围绕文章主题做一张编辑型核心画面，包含 {motif_text}'
    if visual_type == '对比图':
        return f'围绕“{title}”做新旧状态或前后差异对比，包含 {motif_text}'
    if visual_type == '流程图':
        return f'围绕“{title}”做步骤链路表达，包含 {motif_text}'
    if visual_type == '结构图':
        return f'围绕“{title}”做模块结构关系表达，包含 {motif_text}'
    if visual_type == '证据图':
        return f'围绕“{title}”做证据承接表达，包含 {motif_text}'
    if visual_type == '收口图':
        return f'围绕“{title}”做结尾收束表达，包含 {motif_text}'
    return f'围绕“{title}”做真实场景化表达，包含 {motif_text}'


def default_aspect(visual_type: str, density: str = 'medium') -> str:
    if density == 'heavy' and visual_type in {'证据图', '案例场景图'}:
        return '1:1'
    return ASPECT_MAP.get(visual_type, '4:3')


def purpose_text(heading: str, visual_type: str, *, is_cover: bool = False) -> str:
    prefix = PURPOSE_MAP.get(visual_type, '服务正文推进')
    if is_cover:
        return prefix
    return f'{prefix}，服务“{heading}”这一段'


def purpose_en(visual_type: str) -> str:
    return PURPOSE_EN_MAP.get(visual_type, 'support the article progression')


def purpose_zh(visual_type: str) -> str:
    return PURPOSE_MAP.get(visual_type, '服务正文推进')


def style_goal(visual_type: str) -> str:
    return STYLE_MAP.get(visual_type, 'business-tech editorial illustration, restrained palette')


def style_goal_zh(visual_type: str) -> str:
    return STYLE_ZH_MAP.get(visual_type, '编辑型配图，克制专业，避免广告感和杂乱背景')


def compose_prompt(visual_type: str, scene_hint: str, purpose_hint: str, style: str, aspect: str, elements: Iterable[str]) -> str:
    extras = ', '.join(elements) if elements else 'minimal supporting elements'
    base = f'{scene_hint}, {extras}, {style}, conveying {purpose_hint}'
    if visual_type == '封面图':
        return f'{base}, strong focal point, negative space for title, {aspect}'
    if visual_type == '对比图':
        return f'{base}, clear left-right split, strong visual hierarchy, {aspect}'
    if visual_type == '流程图':
        return f'{base}, directional flow, clean layout, {aspect}'
    if visual_type == '结构图':
        return f'{base}, clean information architecture, {aspect}'
    if visual_type == '证据图':
        return f'{base}, readable hierarchy, {aspect}'
    if visual_type == '收口图':
        return f'{base}, calm strong ending image, {aspect}'
    return f'{base}, clean composition, {aspect}'


def compose_prompt_zh(visual_type: str, scene_hint: str, purpose_hint: str, style: str, aspect: str, elements: Iterable[str]) -> str:
    extras = '、'.join(elements) if elements else '少量必要辅助元素'
    base = f'{scene_hint}；辅助元素：{extras}；风格要求：{style}；用途：{purpose_hint}；画幅：{aspect}'
    if visual_type == '封面图':
        return f'{base}；主体聚焦明确，预留标题空间，画面不要出现英文或中文文字。'
    if visual_type == '对比图':
        return f'{base}；画面左右对照清楚，差异一眼可见，不要做成广告海报。'
    if visual_type == '流程图':
        return f'{base}；步骤关系清楚，流向明确，不要出现复杂 UI 截图或英文标签。'
    if visual_type == '结构图':
        return f'{base}；模块层级清楚，结构关系明确，不要堆太多元素。'
    if visual_type == '证据图':
        return f'{base}；强调可信、专业、层级清楚，不要做成营销宣传图。'
    if visual_type == '收口图':
        return f'{base}；强调结尾收束感和判断感，画面克制，不要花哨。'
    return f'{base}；真实、克制、专业，不要文字水印，不要杂乱背景。'


def section_priority(heading: str, content: str, visual_type: str, index: int, total: int) -> int:
    score = 1
    merged = f'{heading} {content}'
    if visual_type in {'对比图', '流程图', '结构图'}:
        score += 2
    if visual_type in {'证据图', '收口图'}:
        score += 1
    if any(k in heading for k in ['为什么', '怎么做', '结论', '总结', '变化']):
        score += 2
    if len(clean_text(content)) > 160:
        score += 1
    if index == total - 1:
        score += 1
    if any(k in merged for k in ['图', '示意', '框架', '流程', '对比']):
        score += 1
    return score


def default_body_limit(density: str) -> int:
    if density == 'light':
        return 1
    if density == 'medium':
        return 3
    return 6

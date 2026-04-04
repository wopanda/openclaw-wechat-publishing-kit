#!/usr/bin/env python3
"""Generate topic pick + explicit angle menu from workflow manifest.

This version adds:
1. lightweight expression-enhancement plans by article type
2. topic-aware brief generation to reduce stale generic skeletons
3. explicit extraction of "为什么重要 / 你该怎么用" seeds from user input
"""
import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def slugify(text: str) -> str:
    text = re.sub(r'[^\w\-\u4e00-\u9fff]+', '-', text.strip())
    text = re.sub(r'-{2,}', '-', text).strip('-')
    return text[:40] or 'workflow'


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def save_json(path: Path, obj: dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def normalize_text(text: str) -> str:
    return re.sub(r'\s+', ' ', (text or '').strip())


def extract_marker_section(text: str, markers: list[str], next_markers: list[str]) -> str:
    raw = normalize_text(text)
    if not raw:
        return ''
    lower = raw
    start = -1
    used_marker = ''
    for marker in markers:
        idx = lower.find(marker)
        if idx != -1 and (start == -1 or idx < start):
            start = idx
            used_marker = marker
    if start == -1:
        return ''
    start += len(used_marker)
    segment = lower[start:]
    end = len(segment)
    for marker in next_markers:
        idx = segment.find(marker)
        if idx != -1:
            end = min(end, idx)
    cleaned = segment[:end].strip(' ：:;；，,。.')
    return cleaned


def build_seed_profile(topic: str, input_text: str) -> dict[str, Any]:
    text = normalize_text(f'{topic} {input_text}')
    why_important = extract_marker_section(
        input_text,
        markers=['为什么重要：', '为什么重要:', '为什么重要'],
        next_markers=['你该怎么用：', '你该怎么用:', '你该怎么用', '来源：', '来源1：', '来源1:', '来源2：', '来源2:'],
    )
    how_to_use = extract_marker_section(
        input_text,
        markers=['你该怎么用：', '你该怎么用:', '你该怎么用'],
        next_markers=['来源：', '来源1：', '来源1:', '来源2：', '来源2:'],
    )

    has_enterprise = any(k in text for k in ['企业', '组织', '团队'])
    has_context = any(k in text for k in ['上下文', '知识', '权限', '系统权限', '接入'])
    has_model = any(k in text for k in ['模型', 'model'])
    has_agent = any(k in text for k in ['agent', '智能体', '数字员工'])
    has_automation = any(k in text for k in ['自动化', 'workflow', '工作流'])

    if has_enterprise and has_context and has_model:
        contradiction = '大家以为企业自动化卡在模型能力，真正卡住落地的，往往是上下文、知识和系统权限怎么接进去。'
        info_gain = [
            '把企业 agent 的竞争点，从“模型强不强”拉回到“上下文接得深不深”。',
            '解释为什么企业自动化一进真实场景，就开始被知识接入、系统权限和上下文结构卡住。',
            '给出一个更实用的判断框架：以后看企业 agent，优先看上下文怎么接。',
        ]
        audience = [
            '在做企业 AI / agent 落地的人',
            '在判断企业自动化方案值不值得上的决策者',
            '关心数字员工怎么真正进工作现场的人',
        ]
        focus_title = '企业自动化真正开始卡住的，不是模型，而是上下文接入'
    elif has_context and has_agent:
        contradiction = '大家以为 agent 的问题主要在模型，真正难的是能不能拿到对的上下文和系统权限。'
        info_gain = [
            '把判断重心从模型能力，挪到上下文接入能力。',
            '解释为什么很多 agent demo 很顺，一接企业现场就卡住。',
            '给出一个更贴近落地的评估视角。',
        ]
        audience = [
            '在做 agent 产品或工作流的人',
            '想把 AI 从 demo 推到真实工作场景的人',
        ]
        focus_title = 'Agent 真正开始卡住的，是上下文接入'
    else:
        contradiction = '大家以为问题出在工具或模型本身，真正卡住落地的，往往是没有接进真实工作流。'
        info_gain = [
            '不是再讲工具能力，而是解释为什么 demo 和上岗之间差很多层。',
            '不把问题归因成“模型不够强”，而是回到流程、分工、上下文和门禁。',
            '强调真实工作现场里的接入成本和组织成本。',
        ]
        audience = ['关心 AI 工作流、数字员工、真实落地的人']
        focus_title = topic or '数字员工为什么不是装上就能用'

    return {
        'why_important': why_important,
        'how_to_use': how_to_use,
        'contradiction': contradiction,
        'info_gain': info_gain,
        'audience': audience,
        'focus_title': focus_title,
        'flags': {
            'enterprise': has_enterprise,
            'context': has_context,
            'model': has_model,
            'agent': has_agent,
            'automation': has_automation,
        },
    }


def classify_article_type(option: dict[str, Any]) -> str:
    article_type = option.get('article_type', '')
    text = f"{option.get('name', '')} {article_type} {' '.join(option.get('outline', []))}"
    if '经验' in text:
        return '经验判断型'
    if '热点' in text:
        return '热点评论型'
    if '教程' in text or '说明' in text:
        return '教程型'
    if '方法' in text:
        return '方法型'
    return '判断型'


def build_expression_enhancement(article_kind: str) -> dict[str, Any]:
    configs = {
        '判断型': {
            'strength': 'strong',
            'headline': '标题优先抓误解、冲突、代价或反常识。',
            'lede': '开头前 120~180 字内尽快亮判断，不先做大段背景铺垫。',
            'analogy': '中段允许打 1 个强类比，帮助把抽象问题讲清。',
            'ending': '结尾收成 1 句可被转述的判断句。',
        },
        '热点评论型': {
            'strength': 'strong',
            'headline': '标题先抓争议点，再落到更大的判断。',
            'lede': '开头先抓事件张力，再迅速指出这件事真正值得看的地方。',
            'analogy': '如需类比，只打 1 个，不要把热点评论写散。',
            'ending': '结尾从事件收回到底层问题，不停在吃瓜层。',
        },
        '经验判断型': {
            'strength': 'medium-strong',
            'headline': '标题可用“我后来越来越确定”式判断句，但不要写成感悟鸡汤。',
            'lede': '开头优先从误判、踩坑或改看法切入。',
            'analogy': '类比可用，但优先让真实经历先站住。',
            'ending': '结尾收成更稳的经验判断，而不是空泛成长感想。',
        },
        '方法型': {
            'strength': 'medium',
            'headline': '标题抓问题和方法边界，不夸大效果。',
            'lede': '开头先说清这篇到底在解决什么问题。',
            'analogy': '可以用 1 个轻类比解释方法，不要压过步骤清晰度。',
            'ending': '结尾给更稳的理解，不喊口号。',
        },
        '教程型': {
            'strength': 'light',
            'headline': '标题优先清楚，不强行追求戏剧张力。',
            'lede': '开头先说这是什么、适合谁、解决什么。',
            'analogy': '类比只作辅助，不影响步骤可执行性。',
            'ending': '结尾回到注意事项或适用边界。',
        },
    }
    base = configs.get(article_kind, configs['判断型'])
    return {
        'article_kind': article_kind,
        'enabled': True,
        **base,
        'guardrails': [
            '只借表达能力，不照搬外部作者腔调。',
            '不抄金句，不抄口头禅，不做夸张震撼体。',
            '表达增强不能盖过用户自己的主线、经历和判断。',
        ],
    }


def build_topic_pick(manifest: dict[str, Any]) -> str:
    topic = manifest.get('topic') or '（未提供主题）'
    input_mode = manifest.get('input_mode', 'unknown')
    input_text = (manifest.get('input_text') or '').strip()
    preview = input_text[:300] + ('...' if len(input_text) > 300 else '') if input_text else '（无额外输入文本）'
    stage1 = ((manifest.get('progressive_context') or {}).get('stage1_core') or {}).get('path', '')
    profile = build_seed_profile(topic, input_text)
    why_important = profile['why_important'] or '这条输入已经明确指出了一个新的落地瓶颈，具备表达价值。'
    how_to_use = profile['how_to_use'] or '可以把它转成一个新的判断框架，帮助后续判断类似问题。'
    audience_block = '\n'.join([f'- {x}' for x in profile['audience']])
    info_gain_block = '\n'.join([f'- {x}' for x in profile['info_gain']])
    return f"""# 选题卡

## 当前选中的点
{topic}

## 为什么先收这个点
- 当前输入入口：{input_mode}
- {why_important}
- 先把点收住，再让用户在几个观点方向里选一个继续写

## 适合写给谁
{audience_block}

## 最抓人的矛盾 / 变化 / 冲突
- {profile['contradiction']}

## 这篇的信息增量是什么
{info_gain_block}

## 读者可以怎么用
- {how_to_use}

## 与长期主线的关系
- 这篇仍然贴近“数字员工怎么进入真实工作现场、怎么一步步上岗”这条长期主线。
- 只是这次把焦点更明确地落在：上下文、知识和系统权限怎么接进真实工作流。

## 当前输入摘录
{preview}

## 当前阶段上下文
- 当前默认只应先使用 Stage 1 最小上下文定方向
- stage1_core: {stage1 or '（未生成）'}

## 当前状态
- [x] 点已收住
- [ ] 等用户选观点方向
"""


def build_context_access_options(topic: str, profile: dict[str, Any]) -> list[dict[str, Any]]:
    focus = topic
    return [
        {
            'id': 'A',
            'name': '误解拆解型',
            'fit': '适合先破“模型越强，企业自动化越容易落地”这个误解。',
            'core_claim': f'{focus}，真正卡的不是模型能力不够，而是上下文、知识和系统权限没有接进真实工作流。',
            'title_line': '为什么企业自动化真正开始卡住的，不是模型，而是上下文接入？',
            'article_type': '判断型 + 解释型',
            'outline': [
                '先破一个误解：模型更强，不等于企业 agent 就能上岗',
                '再拆三层真实卡点：知识接入、系统权限、上下文结构',
                '最后收回判断：企业自动化的瓶颈正在从模型转向上下文接入',
            ],
            'must_keep': [
                '模型能力不再是唯一短板',
                'agent 必须拿到对的上下文、知识和权限',
                '以后判断企业 agent，优先看上下文怎么接',
            ],
            'boundaries': [
                '不要写成泛泛的企业数字化空话',
                '不要把上下文接入写成单一技术接口问题',
            ],
        },
        {
            'id': 'B',
            'name': '经验判断型',
            'fit': '适合写成“我后来怎么把判断重心从模型挪到上下文接入”。',
            'core_claim': f'我后来越来越确定，{focus} 这件事，真正拉开差距的不是模型能力，而是你有没有把上下文和系统权限接进现场。',
            'title_line': '我后来越来越确定：企业 agent 真正的难点，不在模型，而在上下文接入',
            'article_type': '经验型 + 判断型',
            'outline': [
                '从一开始把希望全压在模型能力上写起',
                '再写为什么一进企业现场，就开始被上下文和权限卡住',
                '最后收成一个更稳的判断框架',
            ],
            'must_keep': [
                '误判来自把模型当成唯一变量',
                '真正落地时，知识、权限、系统接入决定可用性',
                '企业 agent 的评估标准要升级',
            ],
            'boundaries': [
                '不要写成空泛的个人感悟',
                '不要只有态度没有真实判断框架',
            ],
        },
        {
            'id': 'C',
            'name': '评估框架型',
            'fit': '适合直接给读者一个新的企业 agent 判断框架。',
            'core_claim': f'{focus}，很多时候不是工具问题，而是评估框架错了：不该只看模型，要看上下文、知识和权限怎么接。',
            'title_line': '以后看企业 agent，别只看模型了，先看上下文怎么接',
            'article_type': '判断型 + 方法型',
            'outline': [
                '先指出旧评估方式为什么会误判企业 agent',
                '再给出 3 个该优先看的维度：上下文、知识、权限',
                '最后收回到为什么这会成为新的竞争点',
            ],
            'must_keep': [
                '模型强不等于企业可用',
                '上下文接入能力会变成新的分水岭',
                '读者能直接拿这套框架去判断项目',
            ],
            'boundaries': [
                '不要写成 checklist 堆砌',
                '不要把框架写得太抽象',
            ],
        },
    ]


def build_generic_options(topic: str) -> list[dict[str, Any]]:
    return [
        {
            'id': 'A',
            'name': '误解拆解型',
            'fit': '适合先破误解，再层层拆卡点。',
            'core_claim': f'{topic}，真正卡的不是工具有没有装上，而是有没有接进真实工作流。',
            'title_line': f'为什么很多人以为“{topic}”是技术问题，其实更像流程问题？',
            'article_type': '判断型 + 解释型',
            'outline': [
                '先破一个误解：能跑起来，不等于能上岗',
                '再拆三层真实卡点：接入、分工、门禁',
                '最后收回判断：真正值钱的是稳定进入现场'
            ],
            'must_keep': [
                'demo 和上岗之间差很多层',
                '单点能力不等于系统成立',
                '真实工作现场的约束决定成败'
            ],
            'boundaries': [
                '不要写成安装教程',
                '不要写成空泛趋势文'
            ]
        },
        {
            'id': 'B',
            'name': '经验判断型',
            'fit': '适合更像亲历者复盘，强调“我后来为什么改看法”。',
            'core_claim': f'我后来越来越确定，{topic} 这件事，真正拉开差距的不是模型能力，而是你有没有把它接进真实工作现场。',
            'title_line': f'我后来越来越确定：{topic}，难点根本不在“装上”',
            'article_type': '经验型 + 判断型',
            'outline': [
                '从自己原来的误判写起',
                '写清后来踩过的坑和改掉的看法',
                '收成更稳的经验判断'
            ],
            'must_keep': [
                '真实项目感',
                '真实弯路和修正过程',
                '最后形成的稳定判断'
            ],
            'boundaries': [
                '不要写成成功学复盘',
                '不要只有观点没有现场感'
            ]
        },
        {
            'id': 'C',
            'name': '分工边界型',
            'fit': '适合强调“人和 Agent 到底该怎么分工”。',
            'core_claim': f'{topic}，往往不是因为 AI 不够强，而是因为人和 Agent 的分工没定住。',
            'title_line': f'{topic}，很多时候不是工具问题，而是分工问题',
            'article_type': '判断型 + 方法型',
            'outline': [
                '先点出很多系统失败不是因为不会做，而是边界不清',
                '再拆哪些该人拍板，哪些适合交给系统',
                '最后收回到“先分工，后自动化”'
            ],
            'must_keep': [
                '人负责判断，系统负责体力活和组织活',
                '没有门禁的自动化很难稳定',
                '分工清楚，系统才可能上岗'
            ],
            'boundaries': [
                '不要写成抽象组织学',
                '不要脱离真实工作流'
            ]
        }
    ]


def build_angle_options(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    topic = manifest.get('topic') or '（未提供主题）'
    input_text = manifest.get('input_text') or ''
    profile = build_seed_profile(topic, input_text)
    if profile['flags']['enterprise'] and profile['flags']['context']:
        options = build_context_access_options(topic, profile)
    else:
        options = build_generic_options(topic)
    for opt in options:
        article_kind = classify_article_type(opt)
        opt['expression_enhancement'] = build_expression_enhancement(article_kind)
    return options


def build_angle_menu(manifest: dict[str, Any], options: list[dict[str, Any]]) -> str:
    topic = manifest.get('topic') or '（未提供主题）'
    blocks = [
        '# 观点菜单',
        '',
        '## 当前选中的点',
        topic,
        '',
        '## 现在不要直接起草正文',
        '先在下面 3 个观点方向里选 1 个。',
        '',
        '## 可选方向',
    ]
    for opt in options:
        enhance = opt['expression_enhancement']
        blocks.extend([
            '',
            f"### {opt['id']}. {opt['name']}",
            f"- 适合：{opt['fit']}",
            f"- 核心主张：{opt['core_claim']}",
            f"- 更像的标题句：{opt['title_line']}",
            f"- 表达增强强度：{enhance['strength']}",
            f"- 标题增强：{enhance['headline']}",
            f"- 开头增强：{enhance['lede']}",
            '- 结构骨架：',
        ])
        for item in opt['outline']:
            blocks.append(f'  - {item}')
    blocks.extend([
        '',
        '## 用户下一步怎么选',
        '- 回复 A / B / C 其一',
        '- 如果都不满意，可以直接说“重出 3 个观点方向”'
    ])
    return '\n'.join(blocks)


def main():
    parser = argparse.ArgumentParser(description='Generate topic pick and explicit angle menu from workflow manifest')
    parser.add_argument('--manifest', required=True)
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    manifest = load_json(manifest_path)
    output_dir = manifest_path.parent
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base = slugify(manifest.get('topic') or manifest.get('input_mode') or 'workflow')

    topic_pick_path = output_dir / f'{timestamp}_{base}_topic_pick.md'
    angle_menu_path = output_dir / f'{timestamp}_{base}_angle_menu.md'
    angle_options_path = output_dir / f'{timestamp}_{base}_angle_options.json'

    options = build_angle_options(manifest)

    topic_pick_path.write_text(build_topic_pick(manifest), encoding='utf-8')
    angle_menu_path.write_text(build_angle_menu(manifest, options), encoding='utf-8')
    angle_options_path.write_text(json.dumps(options, ensure_ascii=False, indent=2), encoding='utf-8')

    manifest.setdefault('stages', {})
    manifest['stages']['topic_pick'] = str(topic_pick_path)
    manifest['stages']['angle_menu'] = str(angle_menu_path)
    manifest['stages']['angle_options'] = str(angle_options_path)
    manifest['angle_options'] = options
    manifest['current_context_stage'] = 'stage2_samples'
    manifest['next_stage'] = 'user_select_angle'
    save_json(manifest_path, manifest)

    print(str(topic_pick_path))
    print(str(angle_menu_path))
    print(str(angle_options_path))


if __name__ == '__main__':
    main()

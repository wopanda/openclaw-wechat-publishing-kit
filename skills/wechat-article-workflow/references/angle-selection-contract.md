# Angle Selection Contract

## 目标
在正文起草前，把“用户选点 → 系统给观点菜单 → 用户选观点”这一步显式化。

## 当前规则
1. 先生成 `topic_pick.md`
2. 再生成 `angle_menu.md` + `angle_options.json`
3. 用户必须先选 A / B / C 之一
4. 只有选定观点方向后，才允许生成 `draft_handoff.md`

## 前台展示要求
在聊天里必须直接展示：
- 当前选中的点
- 2~4 个可选观点方向
- 每个方向更像什么写法
- 用户下一步怎么选

## 禁止
- 不要跳过观点菜单直接起草正文
- 不要只把 angle menu 写成后台文件，不在前台展示

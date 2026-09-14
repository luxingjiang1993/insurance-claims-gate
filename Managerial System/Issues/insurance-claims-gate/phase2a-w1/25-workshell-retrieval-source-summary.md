# 25: 作业壳 AI 区展示检索来源摘要

**github_issue:** #12

**Status:** resolved

**Blocked by:** 20, 24

**wave:** W1

**spec_id:** SPEC-02A-W1-PILOT-COMPLETE

**ref_id:** REF-MISSIONS, REF-CASE-HYBRID

**Rewrote from:** REF-MISSIONS, REF-CASE-HYBRID

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | W0 作业壳 AI 辅助区（票 20 交付） | 既有辅助 vs 草案分标签 |
| 2 | `CASE-投顾AI助手（混合式）/` | 可解释来源展示外形 |

## What to build

在作业壳 AI 辅助建议区展示检索来源摘要（如 doc / 条款项 / 版本等 API 已返回字段），使辅助建议可解释。壳不持有门禁权威；不可采纳引用须诚实展示，不得伪装成已过三联门的合法 citation。

## Acceptance criteria

- [x] AI 辅助区可见检索来源摘要（至少 doc 与条款项级信息，以 API 为准）
- [x] 可采纳 vs 不可采纳引用在 UI 上可区分或诚实标注
- [x] 不静默改写裁决草案；采纳仍走既有规则路径
- [x] 无秒赔/终裁误导文案
- [x] handoff 含 `Rewrote from: REF-MISSIONS`

## Answer / Handoff

**Rewrote from:** REF-MISSIONS, REF-CASE-HYBRID

**Delivered:**
- `workshell/src/components/retrievalSourceSummary.ts` — 纯函数归一化 assist citations（doc / 条款项 / 版本 + adoptable 标注）
- `workshell/src/components/RetrievalSourcesPanel.tsx` — AI 辅助区来源摘要表；可采纳 / 不可采纳 / 未知诚实标注
- `AiAssistPanel` 挂载摘要面板；采纳路径未改（仍 `assist/adopt`→evaluate）
- 接缝测：`retrievalSourceSummary.test.ts`；用户手册 / Changelog Unreleased 已同步

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w1/`。
- 2026-09-14：同步 GitHub Issue #12。
- 2026-09-15：agent 实现完成；Windows 下组件文件命名避免与纯模块大小写冲突。

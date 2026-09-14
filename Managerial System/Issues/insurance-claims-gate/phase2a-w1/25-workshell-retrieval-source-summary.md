# 25: 作业壳 AI 区展示检索来源摘要

**github_issue:** #12

**Status:** ready-for-agent

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

- [ ] AI 辅助区可见检索来源摘要（至少 doc 与条款项级信息，以 API 为准）
- [ ] 可采纳 vs 不可采纳引用在 UI 上可区分或诚实标注
- [ ] 不静默改写裁决草案；采纳仍走既有规则路径
- [ ] 无秒赔/终裁误导文案
- [ ] handoff 含 `Rewrote from: REF-MISSIONS`

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w1/`。
- 2026-09-14：同步 GitHub Issue #12。

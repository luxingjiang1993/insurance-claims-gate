# 39: 辅助拒答 disposition + 作业壳可见；abstain 禁用采纳

**github_issue:** #26

**Status:** resolved

**Blocked by:** 37

**wave:** 2b-P-α

**spec_id:** SPEC-02B-P-ASSIST-QUALITY

**ref_id:** REF-MISSIONS

**Rewrote from:** 现有 rules↔RAG 冲突；CONTEXT 辅助拒答

## 优先打开（只读参考）

路径相对于 \历史项目代码供参考/\。交付只写入 \本项目代码/claims-gate/\。

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | 见 ref_id | 加深缺口，勿平行重切 2a 主路径 |
| 2 | \docs/agents/phase2b-depth-planning-backlog.DRAFT.md\ | 已决议 registry |
| 3 | \Managerial System/SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md\ | DoD / 接缝 |

## What to build

实现 assist_disposition=draft|abstain 与原因枚举 conflict|handbook_alone|low_confidence|citation_unfaithful。abstain 时禁用采纳；可 CTA 走人闸但不自动发令牌。α 作业壳用户可见原因。负例进 S2。

## Acceptance criteria

- [x] disposition + 枚举字段在 API
- [x] abstain 禁用采纳（S1）
- [x] 壳可见拒答/忠实失败原因
- [x] 不自动签发 human_latch_token
- [x] handoff 含 Rewrote from:

## Answer

- 契约：`assist_disposition` / `abstain_reason` / `human_latch_suggested`；Schema 必填 disposition；assist 永不签发 `human_latch_token`。
- 决议：`missions/assist_disposition.py`（conflict > handbook_alone > citation_unfaithful > low_confidence）；pipeline 接入；service 从轨 A 裁决推导 `rules_conclusion`；按 `assist_invocation_id` 禁 abstain 采纳。
- S1：`tests/test_assist_abstain_disposition.py`；S2 负例仍在 Demo 检索种子 `abstain_conflict` 桶。
- 作业壳：拒答横幅 + 原因文案；`canAdoptAssistSuggestion` 禁用采纳按钮。
- 手册：`USER_GUIDE` / `CHANGELOG` Unreleased 已同步。
- Rewrote from: REF-MISSIONS（现有 rules↔RAG 冲突加深）

## Comments

- 2026-09-15：\/to-spec\ 切票；Status=ready-for-agent。
- 2026-09-15：同步 GitHub Issue #26。
- 2026-09-16：实现合入；Status=resolved。

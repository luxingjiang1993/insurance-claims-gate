# 37: assist JSON Schema citation 槽 + 三联门；非法不可采纳

**github_issue:** #24

**Status:** resolved

**Blocked by:** —

**wave:** 2b-P-α

**spec_id:** SPEC-02B-P-ASSIST-QUALITY

**ref_id:** REF-COURSE-03

**Rewrote from:** REF-COURSE-03

## 优先打开（只读参考）

路径相对于 \历史项目代码供参考/\。交付只写入 \本项目代码/claims-gate/\。

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | 见 ref_id | 加深缺口，勿平行重切 2a 主路径 |
| 2 | \docs/agents/phase2b-depth-planning-backlog.DRAFT.md\ | 已决议 registry |
| 3 | \Managerial System/SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md\ | DoD / 接缝 |

## What to build

AI 辅助建议结构化输出含 citation 槽；须过 doc_id+clause_item+version 三联门方可采纳；非法不可采纳；采纳后仍走 evaluate。对齐决策 17。

## Acceptance criteria

- [x] Schema 槽存在；非法 citation 无法采纳（H3）
- [x] 采纳路径仍 evaluate
- [x] S1 负例可测
- [x] handoff 含 Rewrote from:

## Answer

- Schema：`schemas/assist_suggestion.schema.json` + `missions/assist_schema.py`；citation 槽必填 `doc_id`+`clause_item`+`doc_version`（及 chunk_id/clause_id/quote/score）。
- 采纳：`AssistAdoptIn.citations` → `_assert_assist_citations_adoptable`（Schema 后 KB 三联门）→ 再 `evaluate`；非法 → `CITATION_NOT_IN_KB` / `VALIDATION_FAILED`，H3=0。
- S1：`tests/test_assist_citation_schema_adopt.py`（Schema 负例、幻觉采纳拒绝、合法仍 deterministic）。
- 作业壳：采纳只送 `adoptable` citations；无可采纳时禁用按钮。
- 手册：`USER_GUIDE` / `CHANGELOG` Unreleased 已同步。
- Rewrote from: REF-COURSE-03

## Comments

- 2026-09-15：\/to-spec\ 切票；Status=ready-for-agent。
- 2026-09-15：同步 GitHub Issue #24。
- 2026-09-15：\/implement\ 落地；Status=resolved。

# 38: 金标薄切片协议 + 导入导出加深（n≥10）

**github_issue:** #25

**Status:** resolved

**Blocked by:** —

**wave:** 2b-P-α

**spec_id:** SPEC-02B-P-ASSIST-QUALITY

**ref_id:** REF-CASE-OPENEVALS

**Rewrote from:** REF-CASE-OPENEVALS, REF-MISSIONS

## 优先打开（只读参考）

路径相对于 \历史项目代码供参考/\。交付只写入 \本项目代码/claims-gate/\。

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | 见 ref_id | 加深缺口，勿平行重切 2a 主路径 |
| 2 | \docs/agents/phase2b-depth-planning-backlog.DRAFT.md\ | 已决议 registry |
| 3 | \Managerial System/SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md\ | DoD / 接缝 |

## What to build

在 W2 金标 IO 钩子上交付金标薄切片协议：外聘核赔顾问双标 + 第三人裁决（角色占位，人名不进仓）。α 目标 n≥10；不足则 H4 标 deferred、禁止宣称 grounded。禁止宣称 ≥300。

## Acceptance criteria

- [x] 导入导出 + case_id 可用
- [x] 双标+第三人协议写入验收/手册
- [x] n≥10 或诚实 deferred H4
- [x] 不得宣称 ≥300 运营
- [x] handoff 含 Rewrote from:

## Answer

- 加深 `missions/gold_label_io.py`：schema `claims-gate-gold-thin-slice-v1`；`annotation` 双标+第三人角色占位（人名拒绝）；`assess_h4_status` / `h4_status`（n&lt;10 → `deferred`）；禁止 grounded / ≥300 正面宣称。
- SQLite 补列 `annotation_json` / `is_gold_thin_slice`；HTTP import/export 回执含 `h4_status`。
- 外形样例：`artifacts/gold_thin_slice/gold_thin_slice.v1.example.json`（n=1，非真双标运营）。
- 验收：`docs/acceptance/gold-thin-slice.md`；手册 §7.1a / CHANGELOG Unreleased。
- 测：`tests/eval/test_gold_thin_slice.py`（S0）；HTTP：`pytest -m eval_bypass`。
- **诚实：** 当前无真外聘 n≥10 → **H4=`deferred`**，禁止宣称 grounded。

`Rewrote from: REF-CASE-OPENEVALS, REF-MISSIONS`

## Comments

- 2026-09-15：\/to-spec\ 切票；Status=ready-for-agent。
- 2026-09-15：同步 GitHub Issue #25。
- 2026-09-16：\/implement\ 落地；Status=resolved；H4 诚实 deferred。

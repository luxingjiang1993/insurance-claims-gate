# 32: 金标运营接口预留（导入/导出 + case_id）

**github_issue:** #19

**Status:** resolved

**Blocked by:** 29

**wave:** W2

**spec_id:** SPEC-02A-W2-EVAL-OPS

**ref_id:** REF-MISSIONS, REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR

**Rewrote from:** REF-CASE-OPENEVALS, REF-MISSIONS

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | Phase 1 票 11 合成抽检占位 | 金标/抽检字段延续思路 |
| 2 | `CASE-openevals使用/` | 数据集外形 |

## What to build

为未来人工金标运营预留数据集导入/导出钩子，并支持关联 `case_id`（或等价案件键）。本票只做接口/字段/最小外形，**不**实现双人标注全量工作流，**不**关闭 PRD ≥300 金标运营项。任何用户可见文案不得宣称「金标已达标」或「≥300 已完成」。

## Acceptance criteria

- [x] 存在数据集导入与/或导出钩子（API 或约定脚本入口），可携带/关联 `case_id`
- [x] 不实现双人标注全量运营；不把 ≥300 写成已交付
- [x] 用户可见文案无「金标已达标」类宣称
- [x] 不进入默认 `pytest -q` 必过条件
- [x] handoff 含 `Rewrote from:` 所用 REF

## Answer

**落地：**
- `src/missions/gold_label_io.py` — 解析/导入/导出；每条须 `case_id`；拒绝 `gold_ops_complete=true` 与双人全量标志
- SQLite `gold_label_records`；HTTP `POST /eval/gold-labels/import`、`GET /eval/gold-labels/export`
- 脚本：`python -m missions.gold_label_io import|export --file ...`
- 作业壳评测台金标钩子面板（诚实文案）
- 默认测：`tests/eval/test_gold_label_io_hooks.py`（S0）；HTTP：`pytest -m eval_bypass`
- 用户手册 §7.1a Preview 同步；手册收口仍属票 33

`Rewrote from: REF-CASE-OPENEVALS, REF-MISSIONS`

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w2/`。
- 2026-09-14：同步 GitHub Issue #19。
- 2026-09-15：实现关闭；默认 `pytest -q` 159 passed；金标 HTTP 测隔离于 `eval_bypass`。

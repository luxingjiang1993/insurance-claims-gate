# 30: 排行榜：实验名 / 主指标 / 时间 / 提交者 + 可排序

**github_issue:** #17

**Status:** resolved

**Blocked by:** 28, 29

**wave:** W2

**spec_id:** SPEC-02A-W2-EVAL-OPS

**ref_id:** REF-MISSIONS, REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR

**Rewrote from:** REF-CASE-EVAL-ADVISOR, REF-CASE-OPENEVALS, REF-MISSIONS

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `CASE-投顾AI助手（效果评估）/` | LangSmith 实验/对比外形 |
| 2 | `CASE-openevals使用/` | 指标字段来源 |

## What to build

交付评测实验结果排行榜：至少展示实验名、主指标、时间、提交者；可按主指标排序（排序稳定）。**在本票选定并文档化单一数据真源**（LangSmith 实验 API **或** 本地评测结果表/SQLite，二选一）。榜上分数不得成为 S0 `machine_check` 条件；不实现 Braintrust/Phoenix 换栈。

## Acceptance criteria

- [x] 排行榜至少含实验名、主指标、时间、提交者
- [x] 可按主指标排序；两用户两条跑次在榜上均可观察（契约可测）
- [x] 单一数据真源已选定并写入票内 Answer/文档；不双源打架
- [x] 排行榜/分数断言不进入默认 `pytest -q` / S0
- [x] handoff 含 `Rewrote from:` 所用 REF

## Answer

**单一数据真源：** 本地 SQLite 表 `eval_runs`（与票 29 一致）。**不**读 LangSmith 实验 API 作为排行榜驱动源，避免双源打架。LangSmith 仅作跑次旁路上报/`langsmith_degraded` 字段。

**主指标：** `pass_rate = summary.passed / summary.total`（`total<=0` → `0.0`）。

**落地：**
- `src/missions/eval_leaderboard.py` — 构建榜行 + 稳定排序（先 `created_at`/`run_id`，再按主指标）
- `GET /eval/leaderboard?order=desc|asc` — 已登录可读（含 `viewer`）；响应含 `data_source=local_sqlite_eval_runs`
- 测试：`tests/eval/test_eval_leaderboard_sort.py`（默认 S0：字段/排序/两用户种子可见；`pytest -m eval_bypass` 两用户 HTTP）
- 用户手册：`docs/user/` Unreleased + §7.1a Preview；作业壳入口仍 Deferred（31）

`Rewrote from: REF-CASE-EVAL-ADVISOR, REF-CASE-OPENEVALS, REF-MISSIONS`

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w2/`。真源（LangSmith API vs 本地表）实现时选定并文档化。
- 2026-09-14：同步 GitHub Issue #17。
- 2026-09-15：实现关闭；真源选定本地 SQLite `eval_runs`；默认 pytest 绿；榜分不进 machine_check。

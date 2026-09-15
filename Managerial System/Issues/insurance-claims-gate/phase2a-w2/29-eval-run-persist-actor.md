# 29: 评测跑次持久化 + actor 归因（复用 W0 用户）

**github_issue:** #16

**Status:** resolved

**Blocked by:** 28

**wave:** W2

**spec_id:** SPEC-02A-W2-EVAL-OPS

**ref_id:** REF-MISSIONS, REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR

**Rewrote from:** REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR, REF-MISSIONS

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `CASE-openevals使用/` | OpenEval 旁路跑法 |
| 2 | `CASE-投顾AI助手（效果评估）/` | 实验/跑次外形 |
| 3 | W0 RBAC 用户（票 14/15） | 复用本地用户，不做企业租户 |

## What to build

在 W1 OpenEval↔LangSmith 历史对比之上，持久化评测跑次并记录 `actor_user_id`（复用 W0 演示用户）。≥2 个演示用户可分别触发评测跑次，结果可隔离或可按用户过滤。跑次仍经 OpenEval 旁路（及 W1 约定的 LangSmith 路径或明确降级说明）；**永不**写入默认 `pytest -q` 必过条件。须声明 W1 DoD（票 28）已关闭。

## Acceptance criteria

- [x] 评测跑次可持久化；每条含 `actor_user_id`（或等价提交者字段）
- [x] ≥2 演示用户可分别触发跑次；结果可隔离或可过滤，互不覆盖
- [x] 仍走 OpenEval 旁路；失败跑次不导致默认 CI 红
- [x] 票内或 handoff 声明 W1（28）已满足
- [x] handoff 含 `Rewrote from:` 所用 REF

## Answer

**W1（票 28）已满足：** Pilot Complete / Package L 已关闭；本票在其上增量，不回退 W1。

**协作模型（本票）：** 复用 W0 RBAC 种子用户（`adjuster` / `supervisor` 可触发；`viewer` 只读列表）。跑次写入本地 SQLite `eval_runs`，字段含 `actor_user_id`（= 会话 `username`）。默认 `GET /eval/runs` 列出全部；`?actor_user_id=` 过滤后互不覆盖。不做企业租户；不做认领队列（Spec「认领」外形留给后续票）。

**落地：**
- `src/missions/eval_run_persist.py` — OpenEval 旁路触发 + 持久化；无 LangSmith → `langsmith_degraded=true`
- `sqlite_store.eval_runs` + `POST|GET /eval/runs`
- 测试：`tests/eval/test_eval_run_persist_actor.py`（S0 隔离默认绿；两用户：`pytest -m eval_bypass`）
- 用户手册：`docs/user/` Unreleased + §7.1a Preview；排行榜/作业壳入口仍 Deferred（30/31）

`Rewrote from: REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR, REF-MISSIONS`

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w2/`。
- 2026-09-14：同步 GitHub Issue #16。
- 2026-09-15：实现关闭；默认 `pytest -q` 146 passed / eval_bypass 隔离。

# 53: Q-A2 Schema-bound Orchestrator（契约硬停 + goal 必用）

**github_issue:** #40

**Status:** resolved

**Blocked by:** 44

**wave:** 2b-Q

**spec_id:** SPEC-02B-Q-RELAY-A2A3

**ref_id:** REF-MISSIONS, REF-COURSE-03

**Rewrote from:** REF-MISSIONS（契约入账）；REF-COURSE-03（Schema 外形）

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | `project 多agent`（REF-MISSIONS） | validation contract / 入账硬停 |
| 2 | `03_单次模型请求与结构化输出控制`（REF-COURSE-03） | JSON Schema 外形 |
| 3 | `Managerial System/SPEC/insurance-claims-gate/spec-2b-q-relay-a2a3.md` | DoD / Q-S0-A |

## What to build

把 Orchestrator 规划升到宪法 **A2**：validation contract 入账前 JSON Schema 硬停；`goal` 必填且进入可观察契约/handoff；去掉以字符串 if/elif 为主规划源的诚实性漏洞。非法契约不得创建 implement feature。不含 Worker 真 patch（票 54）。

## Acceptance criteria

- [x] 缺 `goal` / 非法结构 → 入账前失败，不开工（Q-S0-A）
- [x] 合法契约可入账；`goal` 可在 contract 或 handoff 观察
- [x] 规划主路径不以字符串匹配冒充 Schema-bound 契约源
- [x] 默认 `pytest -q` 仍绿；handoff 含 `Rewrote from:`
- [x] 不改流 P assist 包；不宣称 A3

## Answer

- 新增 `schemas/mission_plan_request.schema.json` + `plan_schema.validate_plan_request`：缺/空白 `goal`、未知 `template_id` 入账前 `PlanSchemaError`。
- 契约源改为 `plan_templates.PLAN_TEMPLATES[template_id]` 精确查找；`Orchestrator.plan` / `MissionRunner.new_mission(..., template_id=)` 去掉 goal 子串 if/elif 主规划。
- 合法 plan：`contract.goal` + handoff/events 可观察 goal；handoff `Rewrote from: REF-MISSIONS, REF-COURSE-03`。
- 测：`tests/test_schema_bound_orchestrator.py`（Q-S0-A）；默认 `pytest -q` 299 passed。未改 `track_llm_optional`；未做 A3 patch。

## Comments

- 2026-09-16：`/to-spec` 切票；Status=ready-for-agent。
- 2026-09-16：同步 GitHub Issue #40。
- 2026-09-16：`/implement` 落地 Schema-bound 规划；Status=resolved。

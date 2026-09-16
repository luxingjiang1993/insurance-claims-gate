# 49: assist 步数≤4：retrieve→gate→draft→self-check

**github_issue:** #36

**Status:** resolved

**Blocked by:** 44, 40

**wave:** 2b-P-β

**spec_id:** SPEC-02B-P-ASSIST-QUALITY

**ref_id:** REF-CASE-DELIBERATIVE

**Rewrote from:** REF-CASE-DELIBERATIVE

## 优先打开（只读参考）

路径相对于 \历史项目代码供参考/\。交付只写入 \本项目代码/claims-gate/\。

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | 见 ref_id | 加深缺口，勿平行重切 2a 主路径 |
| 2 | \docs/agents/phase2b-depth-planning-backlog.DRAFT.md\ | 已决议 registry |
| 3 | \Managerial System/SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md\ | DoD / 接缝 |

## What to build

收紧 assist 步数外形≤4；实现可用图库但架构 app-owned；口头不卖 LangGraph/第二套 Agent 平台。

## Acceptance criteria

- [x] 步数预算可强制或可测
- [x] 架构声明 app-owned
- [x] handoff 含 Rewrote from:

## Answer

**交付（2026-09-16）：**

- `missions/assist_step_budget.py`：`AssistStepBudget`；预算=4；有序 `retrieve→gate→draft→self-check`；未知/乱序/超步强制失败；`orchestration_owner=app-owned`
- `track_llm_optional/pipeline.draft_assist`：四步编排；`gate` 走工具环 `validate_citation`；`draft` 含 `draft_slots`；`self-check` 为 disposition；响应字段 `orchestration_*`
- 测：`tests/test_assist_step_budget.py`（S0 强制 + S1 draft_assist / HTTP）
- 验收：`docs/acceptance/assist-four-step-budget.md`；手册 §3.9 + CHANGELOG Unreleased

**复现：** `pytest -q tests/test_assist_step_budget.py`  
**Rewrote from:** REF-CASE-DELIBERATIVE

## Comments

- 2026-09-15：\/to-spec\ 切票；Status=ready-for-agent。
- 2026-09-15：同步 GitHub Issue #36。
- 2026-09-16：实现并关闭；步数预算可强制/可测；架构 app-owned。

# Acceptance — Issue 49 / P-A4：assist 步数≤4

**Status:** accepted  
**Rewrote from:** REF-CASE-DELIBERATIVE  
**SPEC：** `SPEC-02B-P-ASSIST-QUALITY` β DoD · assist 步数≤4（决策 10 / P-A4）

## 范围

| 能力 | 行为 |
|------|------|
| 步数预算 | `ASSIST_STEP_BUDGET=4`；外形 `retrieve→gate→draft→self-check` |
| 可强制 | 未知步 / 乱序 / 第 5 步 → `AssistStepBudgetError` |
| 可测 | `draft_assist` / HTTP assist 含 `orchestration_steps` / `orchestration_step_budget` / `orchestration_owner` |
| 工具对齐 | `gate`=`validate_citation`；`draft` 含 `draft_slots`；均经 app-owned 工具环 |
| 架构 | `orchestration_owner=app-owned`；可用图库实现，口头不卖 LangGraph / 第二套 Agent 平台 |

## 复现命令

```text
cd 本项目代码/claims-gate
pytest -q tests/test_assist_step_budget.py
```

## 诚实边界

- 本验收证明编排预算外形可强制/可测且 app 拥有；不宣称已上线独立 Agent 平台或 LangGraph 产品面。
- 观测 span 树（retrieve→fuse→gate→llm→…）可更细；本票约束的是编排预算≤4。
- 不实现 γ（rerank / MultiQuery / fan-out）。

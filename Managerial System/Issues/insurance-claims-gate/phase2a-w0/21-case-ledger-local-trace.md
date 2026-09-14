# 21: 本案流水 + 本地 trace 导出

**github_issue:** #8

**Status:** resolved

**Blocked by:** 14

**wave:** W0

**spec_id:** SPEC-02A-W0-DEV-COMPLETE

**ref_id:** REF-MISSIONS

**Rewrote from:** REF-MISSIONS

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `project 多agent/` ledger / 审计相关外形（若有） | 事件摘要与可回放字段 |
| 2 | （可选协议阅读）LangSmith span 概念 | 仅预留配置位，不要求真 Key |

## What to build

提供本案操作流水可查询（评估/人闸/AI 等关键动作可回放），以及本地 JSONL/文件 span 导出，便于无 LangSmith 排障。配置位可预留 LangSmith，但不作为 W0 完工条件；默认 CI 不要求真 LangSmith。

## Acceptance criteria

- [x] 本案流水 API（及/或壳可读面）可浏览关键操作
- [x] 本地 trace 文件/JSONL 可导出 evaluate / assist / latch 等关键 span（至少可配置开启）
- [x] LangSmith 仅配置位预留；无 Key 不阻塞 W0
- [x] 默认 `pytest` 不要求 LangSmith
- [x] handoff 含 `Rewrote from: REF-MISSIONS`

## Answer

**Rewrote from: REF-MISSIONS**

- `GET /claims/{id}/ledger`：人闸批准/驳回亦写入 ledger（`human_latch_approve` / `human_latch_reject`），与 evaluate / assist 一并可回放。
- `claims_api/local_trace.py`：`CLAIMS_GATE_LOCAL_TRACE=1` + 可选 `CLAIMS_GATE_LOCAL_TRACE_PATH` 导出 JSONL span；默认关闭。
- `.env.example`：本地 trace + LangSmith 配置位；无 Key 不阻塞。
- 作业壳 `CaseLedgerPanel`：ledger + 人闸事件只读浏览。
- 测试：`tests/test_case_ledger_local_trace.py`；默认 `pytest -q` 绿且不要求 LangSmith。

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w0/`。
- 2026-09-14：同步 GitHub Issue #8。
- 2026-09-14：实现落地并 resolved。

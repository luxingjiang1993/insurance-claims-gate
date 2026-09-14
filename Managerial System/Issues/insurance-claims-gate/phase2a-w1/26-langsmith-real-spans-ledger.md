# 26: 真 LangSmith：evaluate / assist / latch + ledger 对齐

**github_issue:** #13

**Status:** resolved

**Blocked by:** 22

**wave:** W1

**spec_id:** SPEC-02A-W1-PILOT-COMPLETE

**ref_id:** REF-MISSIONS, REF-CASE-EVAL-ADVISOR, REF-CASE-LANGFUSE

**Rewrote from:** REF-CASE-EVAL-ADVISOR, REF-MISSIONS

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `CASE-投顾AI助手（效果评估）/` | 评测/追踪挂接外形 |
| 2 | `CASE-langfuse使用/` | 可观测对照（协议阅读级） |
| 3 | W0 本地 trace（票 21） | 保留本地 exporter 作降级 |

## What to build

在配置真实 LangSmith Key 后，对 evaluate / assist / latch 等关键操作成功上报可验证的 trace。ledger（或等价流水）含 `retrieval_profile` 与 `trace_id`（若有），便于事后对齐 LangSmith。W0 本地文件 exporter 可保留。默认 CI / `pytest -q` 不要求 LangSmith Key；真上报测放在 S2（真实 Key 或票内写明的官方 mock 策略——mock 不得冒充 Pilot Complete 宣称）。

## Acceptance criteria

- [x] LangSmith Key 配置后，evaluate / assist / latch 关键 span 可在 LangSmith 验证存在
- [x] ledger/流水含 `retrieval_profile` 与 `trace_id`（有上报时）
- [x] 本地 trace exporter 仍可用；无 Key 时不阻断规则路径
- [x] 默认 `pytest -q` 不要求 LangSmith；S2 标记隔离真上报/mock 策略并在票内写明
- [x] 不得用 LangSmith UI 替代 `machine_check` 合门禁
- [x] handoff 含 `Rewrote from:` 所用 REF

## Answer

**交付：**
- `claims_api/langsmith_trace.py`：真上报 `create_run`/`update_run`；无 Key/失败不阻断；可注入 Fake Client
- `LedgerEntry.trace_id` + SQLite `ledger_summary.trace_id`；`_append_ledger` 写本地 span 并可选 LangSmith
- 作业壳 ledger 表展示 `trace_id`
- 默认测：`tests/test_langsmith_spans_ledger.py`（FakeLangSmithClient，不打外网）
- S2：`tests/langsmith_integration/` + marker `langsmith_integration`（默认 CI 排除）；真 Key 时 `read_run` 校验

**S2 / mock 策略（写明）：**
1. **默认/S0：** 注入 `FakeLangSmithClient`（记录 `create_run`，无网络）。**不得**用 mock 冒充 Pilot Complete。
2. **真上报：** `pytest -m langsmith_integration`，需真实 `LANGCHAIN_API_KEY`/`LANGSMITH_API_KEY`；缺 Key 则 skip。
3. LangSmith UI **不**替代 `machine_check`。

`Rewrote from: REF-CASE-EVAL-ADVISOR, REF-MISSIONS`

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w1/`。
- 2026-09-14：同步 GitHub Issue #13。
- 2026-09-15：实现合入；S0 Fake Client 覆盖三路径；S2 真 Key `pytest tests/langsmith_integration/ -m langsmith_integration -o addopts=` **PASSED**（evaluate/assist/latch + read_run 校验）。

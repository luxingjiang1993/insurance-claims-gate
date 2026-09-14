# 26: 真 LangSmith：evaluate / assist / latch + ledger 对齐

**github_issue:** #13

**Status:** ready-for-agent

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

- [ ] LangSmith Key 配置后，evaluate / assist / latch 关键 span 可在 LangSmith 验证存在
- [ ] ledger/流水含 `retrieval_profile` 与 `trace_id`（有上报时）
- [ ] 本地 trace exporter 仍可用；无 Key 时不阻断规则路径
- [ ] 默认 `pytest -q` 不要求 LangSmith；S2 标记隔离真上报/mock 策略并在票内写明
- [ ] 不得用 LangSmith UI 替代 `machine_check` 合门禁
- [ ] handoff 含 `Rewrote from:` 所用 REF

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w1/`。
- 2026-09-14：同步 GitHub Issue #13。

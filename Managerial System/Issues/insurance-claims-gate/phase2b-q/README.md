# Phase 2b-Q — Missions Relay Honesty（A2/A3）

SPEC：[`spec-2b-q-relay-a2a3.md`](../../../SPEC/insurance-claims-gate/spec-2b-q-relay-a2a3.md)（`SPEC-02B-Q-RELAY-A2A3`）。

前置：P-α DoD（本地 44 / GitHub #31）已 resolved。  
完成旗：仅 H8 + 本夹 DoD；**禁止**与流 P 共用深度完成旗。  
Deferred：Q-A7（pause/resume / credential proxy）不切票。

| NN | 标题 | Blocked by | Status |
|----|------|------------|--------|
| 53 | Q-A2 Schema-bound Orchestrator | 44 | resolved |
| 54 | Q-A3 Patch Worker + F-Q-DEMO-01 | 53 | resolved |
| 55 | Q-A6 Validator 独立 profile | 54 | ready-for-agent |
| 56 | Q DoD 收口（H8） | 53, 54, 55 | ready-for-agent |

```text
44 (P-α DoD, resolved)
 └── 53 Q-A2 ── 54 Q-A3 ── 55 Q-A6
                     └── 56 Q DoD
```

Frontier：55（54 已 resolved）。实现只写入 `本项目代码/claims-gate/`。

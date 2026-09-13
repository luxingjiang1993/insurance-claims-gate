# 08: L2 出款就绪回写模拟（无人闸禁放行）

**Status:** done

**Blocked by:** 04, 06

**ref_id:** REF-MISSIONS, REF-CASE-FC

**Backlog:** （REQ-S-01；SPEC 决策 4/8/13）

**Rewrote from:** REF-MISSIONS, REF-CASE-FC

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `project 多agent/src/transfer_api/api.py` | HTTP 状态变更接口外形（换为 L2 回写模拟） |
| 2 | `project 多agent/src/transfer_api/service.py` | 成功路径写记录；拒绝时状态不变 |
| 3 | `project 多agent/src/transfer_api/audit.py` | 审计轨迹（回写事件可记 ledger） |
| 4 | `project 多agent/src/missions/runner.py` | 人闸通过后才允许 promote / 进入下一相位 |
| 5 | `project 多agent/src/missions/checks.py` | 「无人闸写出款就绪失败」「主数据不一致」类检查 |
| 6 | `CASE-Function Calling/assistant_ticket_bot-1.py` | 工具注册与最小权限外形（**对照**：本切片支付工具默认无权限） |
| 7 | `CASE-Function Calling/assistant_ticket_bot-3.py` | 多工具 ACL 演进参考（只借外形，不接入真实支付） |

禁止：实现任何银企/支付适配器；`PAYOUT_READY` ≠ 自动出款。

## What to build

模拟核心 L2 状态回写：仅在持有有效人闸令牌后可将门禁态置为出款就绪，且不触发银企支付。主数据（保单/批单/案件）不一致时禁止进入出款就绪。结案回写不含自动支付指令；CLOSED 与出款解耦。工具 ACL 保持支付类默认无权限。现网枚举字段位可保留但不阻塞 Demo。

## Acceptance criteria

- [x] 人闸后可通过 API 将状态置为 `PAYOUT_READY`（或规范态等价），且无银企/支付适配器调用
- [x] 无人闸令牌时写入出款就绪失败；`payout_ready` 保持 false
- [x] 主数据不一致夹具触发 `MASTER_DATA_MISMATCH`（或等价），禁止出款就绪
- [x] 结案回写可达 `CLOSED` 且载荷不含自动支付指令
- [x] 支付类工具在 ACL 下默认拒绝
- [x] handoff 含 `Rewrote from: REF-MISSIONS, REF-CASE-FC`

## Comments

- 2026-09-13：to-tickets 批准 defaults 后落盘。
- 2026-09-13：实现完成 — HTTP `l2/payout-ready` + `l2/close`；夹具 `CLM-MISMATCH-001`；machine_check 两类型。

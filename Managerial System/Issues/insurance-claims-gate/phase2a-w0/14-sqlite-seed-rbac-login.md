# 14: SQLite 持久化 + 种子三角色 + 登录会话

**Status:** resolved

**Blocked by:** None (can start immediately)

**wave:** W0

**spec_id:** SPEC-02A-W0-DEV-COMPLETE

**ref_id:** REF-MISSIONS, REF-COURSE-04

**Rewrote from:** REF-MISSIONS

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `project 多agent/src/transfer_api/` | HTTP 外壳与域服务边界 |
| 2 | `04_多步流程编排与条件分支/` | 作业态与多步状态外形 |

## What to build

把案件域（案件、材料、裁决草案、人闸事件、ledger 摘要）落到 SQLite，并种子 viewer / adjuster / supervisor 三用户。提供登录会话，使后续 API 能识别角色。重启进程后演示案件仍可续，无需云账号。

## Acceptance criteria

- [x] SQLite 持久化案件、材料、草案、人闸事件、ledger 摘要、用户与角色
- [x] 种子三角色可登录；会话可识别当前用户角色
- [x] 进程重启后既有案件仍可读
- [x] 不引入 L3/支付；不修改 `spec.md`
- [x] handoff 含 `Rewrote from: REF-MISSIONS`

## Answer

交付位于 `本项目代码/claims-gate/`：

- `sqlite_store.py`：案件 JSON + `ledger_summary` + `latch_events`（表权威）+ users/sessions
- `auth.py`：种子 `viewer`/`adjuster`/`supervisor`（密码=用户名），`POST /auth/login`、`GET /auth/me`、`POST /auth/logout`
- `ClaimsService` 经 store 读写；`reset_service(db_path=)` 支持隔离与重启续读
- 持久演示：`CLAIMS_GATE_DB=<path>`；默认 import 用临时库，不污染 `data/`
- 测试：`tests/test_sqlite_auth_login.py`；全仓 `pytest -q`：103 passed

**Rewrote from: REF-MISSIONS**

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w0/`。
- 2026-09-14：实现完成并 Resolve；人闸 RBAC 硬门留给票 15。

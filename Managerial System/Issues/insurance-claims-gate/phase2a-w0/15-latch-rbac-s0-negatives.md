# 15: 人闸 RBAC 硬门 + S0 负例机检

**github_issue:** #2

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
| 1 | `project 多agent/src/missions/checks.py` | `machine_check` 按 type 分发 |
| 2 | `project 多agent/src/transfer_api/` | 权限拒绝与 `error_code` 外形 |

## What to build

在 HTTP 面落实人闸 RBAC：仅 supervisor 可批准对外通知 / 出款就绪类人闸；adjuster 与 viewer 被拒绝且不得签发人闸令牌。S0 增加 RBAC 负例机检，默认 `pytest` 在无 LLM 下仍绿。

## Acceptance criteria

- [x] 仅 supervisor 可批对外通知 / 出款就绪类人闸并获令牌
- [x] adjuster / viewer 批闸被 API 拒绝；不得签发令牌
- [x] viewer 写操作（若触及本票范围）被拒绝或保持只读语义
- [x] S0/`machine_check` 含 RBAC 负例；默认 `pytest -q` 无 LLM 绿
- [x] handoff 含 `Rewrote from: REF-MISSIONS`

## Answer

交付位于 `本项目代码/claims-gate/`：

- `tools_acl.assert_role_allowed`：人闸仅 `supervisor`；`viewer` 只读
- `api._authorize`：Bearer 会话角色硬门；`PERMISSION_DENIED` / 无人闸会话 `AUTH_FAILED`
- `machine_check(type="latch_rbac_negatives")`；既有批闸机检经 supervisor 登录
- 测试：`tests/test_latch_rbac_s0.py`；全仓 `pytest -q`：109 passed（无 LLM）

**Rewrote from: REF-MISSIONS**

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w0/`。
- 2026-09-14：同步 GitHub Issue #2。
- 2026-09-14：实现完成并 Resolve。

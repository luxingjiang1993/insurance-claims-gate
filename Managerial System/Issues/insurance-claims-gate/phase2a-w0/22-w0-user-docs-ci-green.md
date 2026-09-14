# 22: W0 用户手册 + 默认 CI 无 LLM 绿确认

**github_issue:** #9

**Status:** resolved

**Blocked by:** 18, 20, 21

**wave:** W0

**spec_id:** SPEC-02A-W0-DEV-COMPLETE

**ref_id:** REF-MISSIONS

**Rewrote from:** REF-MISSIONS

## 优先打开（只读参考）

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `docs/user/MAINTENANCE.md` | 手册与 Changelog 更新义务 |
| 2 | `docs/user/USER_GUIDE.md` / `CHANGELOG.md` | 既有 Phase 1 口径；W0 须诚实 Preview |

## What to build

在 W0 用户可见能力合入后，按维护约定更新 `docs/user/`：启动说明、作业壳/RBAC/AI 降级与非终裁标注、Developer Preview 诚实边界。确认默认 `pytest -q` 在无 LLM / 无 LangSmith 下全绿，使 W0 DoD 可勾选关闭（不含 Chroma/真 LangSmith/OpenEval）。

## Acceptance criteria

- [x] `USER_GUIDE.md` 写明 W0 启动、登录角色、规则路径、AI 降级与非终裁；不把 W1/W2 写成已上线
- [x] `CHANGELOG.md` Unreleased（或对应节）记录 W0 用户可见变更
- [x] 默认 `pytest -q` 无 LLM、无 LangSmith 全绿（含 S0 RBAC 负例）
- [x] 可对照 `spec-2a-w0-dev-complete.md` DoD Checklist 勾选关闭 W0（实现侧）
- [x] handoff 含 `Rewrote from: REF-MISSIONS`

## Answer

**Rewrote from: REF-MISSIONS**

- `docs/user/USER_GUIDE.md`：页眉标 Phase 2a W0 Dev Complete；§1 诚实边界区分 Phase 1 / W0 / 未上线 W1·W2；§2.3 成熟度表 W0 Preview + W1/W2 Deferred；§3.1 写明启动、三角色、规则路径、AI 降级与非终裁、本案流水。
- `docs/user/CHANGELOG.md`：Unreleased 折叠为「Phase 2a · W0 — Dev Complete」；W1/W2 标明未启动实现主路径。
- 默认 `pytest -q`：`123 passed, 8 deselected`（无 LLM / 无 LangSmith Key；含 `tests/test_latch_rbac_s0.py`）。
- `spec-2a-w0-dev-complete.md` DoD Checklist 全部勾选；SPEC Status=`closed`；Issues 任务图 frontier 切到 W1（23、26）。

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w0/`。
- 2026-09-14：同步 GitHub Issue #9。
- 2026-09-14：实现落地并 resolved。

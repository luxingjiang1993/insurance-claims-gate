# 33: Eval Ops 手册 + 分数≠合门禁文案 + S0 仍绿

**github_issue:** #20

**Status:** resolved

**Blocked by:** 30, 31, 32

**wave:** W2

**spec_id:** SPEC-02A-W2-EVAL-OPS

**ref_id:** REF-MISSIONS

**Rewrote from:** REF-MISSIONS

## 优先打开（只读参考）

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `docs/user/MAINTENANCE.md` | 手册与 Changelog 更新义务 |
| 2 | `docs/user/USER_GUIDE.md` / `CHANGELOG.md` | Preview 诚实标注口径 |
| 3 | `spec-2a-w2-eval-ops.md` DoD | 关闭条件与金标延后边界 |

## What to build

收口 W2 Eval Ops：更新 `docs/user/` 增加 Eval Ops 操作说明（Preview），明确排行榜/评测分数 ≠ 条款门禁合门禁、`machine_check` 仍是合规主缝；金标全量运营标为延后。确认默认 `pytest -q` / S0 全绿，故意失败的评测跑次不影响轨 A。Phase 2a 可称「Eval Ops 已交付」时仍须诚实标注金标运营未关闭。

## Acceptance criteria

- [x] `USER_GUIDE.md` 含 Eval Ops Preview 操作说明；与门禁主路径区分
- [x] 文案明确：排行榜分数 ≠ `machine_check` 通过；不宣称 ≥300 金标已达标
- [x] `CHANGELOG.md` 标明 Eval Ops Preview
- [x] 默认 `pytest -q` 仍绿；评测失败不进 S0 必过
- [x] 可对照 `spec-2a-w2-eval-ops.md` DoD Checklist 勾选关闭 W2（实现侧）
- [x] handoff 含 `Rewrote from: REF-MISSIONS`

## Answer

**Rewrote from: REF-MISSIONS**

- `docs/user/USER_GUIDE.md`：页眉标 **W2 / Eval Ops（Developer Preview）**；§1 诚实边界；§2.3 成熟度表 Issues 29–33 Preview + ≥300 Deferred；§3.3 Eval Ops 操作说明（两账号协作跑榜、与门禁主路径对照表）；§7.1a 收口；明确排行榜分数 ≠ `machine_check` / 合门禁。
- `docs/user/CHANGELOG.md`：Unreleased 折叠为「Phase 2a · W2 — Eval Ops（Developer Preview）」；标明金标运营延后。
- `docs/user/README.md`：成熟度同步为 W2 Eval Ops Preview。
- 默认 `pytest -q`：`160 passed, 18 deselected`（无 LLM / 无 LangSmith Key；`eval_bypass` 等不进必过）。
- `spec-2a-w2-eval-ops.md` DoD Checklist 全部勾选；SPEC Status=`closed`。

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w2/`。
- 2026-09-14：同步 GitHub Issue #20。
- 2026-09-15：实现落地并 resolved。

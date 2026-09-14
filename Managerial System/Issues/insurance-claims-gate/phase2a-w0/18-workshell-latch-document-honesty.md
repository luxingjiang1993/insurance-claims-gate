# 18: 作业壳：人闸 + 文书分态诚实展示

**github_issue:** #5

**Status:** resolved

**Blocked by:** 15, 17

**wave:** W0

**spec_id:** SPEC-02A-W0-DEV-COMPLETE

**ref_id:** REF-MISSIONS

**Rewrote from:** REF-MISSIONS

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `project 多agent/src/missions/` | 人闸阻塞相位与令牌外形 |
| 2 | 本仓已落地文书分态 / EXTERNAL_NOTIFY 行为 | DRAFT vs EXTERNAL 分态不得被 UI 抹平 |

## What to build

在作业壳内完成人闸批准/驳回与文书分态诚实展示：supervisor 可批/驳并获令牌；adjuster 批闸被拒且可见；拒赔 DRAFT 可预览；EXTERNAL_NOTIFY 无人闸时 API 失败且 UI 不假成功。

## Acceptance criteria

- [x] supervisor 可在壳内批准/驳回应闸类型并获人闸令牌（成功路径）
- [x] adjuster 批闸被拒绝且 UI 诚实展示
- [x] 拒赔 DRAFT_EXPORT（或等价）可预览
- [x] EXTERNAL_NOTIFY 无人闸失败时 UI 不假成功
- [x] handoff 含 `Rewrote from: REF-MISSIONS`

## Answer

作业壳详情页增加人闸批准/驳回与文书分态区，直连既有 `POST .../human-latch/approve|reject` 与 `POST .../documents/export`。令牌只展示 API 返回值；adjuster 可点批准以观察 `PERMISSION_DENIED`，失败不点亮成功。`DRAFT_EXPORT` 与 `EXTERNAL_NOTIFY` 分选提交，无人闸升对外时拒绝体原样展示且不把草稿标成已对外。

`Rewrote from: REF-MISSIONS`

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w0/`。
- 2026-09-14：同步 GitHub Issue #5。

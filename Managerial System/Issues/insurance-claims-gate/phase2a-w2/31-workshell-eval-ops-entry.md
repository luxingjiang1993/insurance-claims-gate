# 31: 作业壳「评测」独立入口 + 两账号协作跑榜演示

**github_issue:** #18

**Status:** resolved

**Blocked by:** 20, 29, 30

**wave:** W2

**spec_id:** SPEC-02A-W2-EVAL-OPS

**ref_id:** REF-MISSIONS, REF-CASE-EVAL-ADVISOR

**Rewrote from:** REF-MISSIONS, REF-CASE-EVAL-ADVISOR

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | W0 作业壳（票 16/20） | 导航与主路径布局 |
| 2 | `CASE-投顾AI助手（效果评估）/` | 评测台与作业台分离叙事 |

## What to build

在作业壳增加独立「评测」导航或子路由：可触发/查看评测跑次与排行榜。禁止把跑榜藏在条款门禁 evaluate 主按钮背后。评测台与门禁主路径视觉分离，避免被理解成核赔终裁台。支持用 ≥2 个演示账号演示协作跑榜（分别触发、查看他人结果且不互相覆盖）。

## Acceptance criteria

- [x] 存在独立「评测」入口（导航或子路由），不挂在 evaluate 主按钮背后
- [x] 评测台与门禁作业主路径视觉可区分；无终裁/秒赔误导
- [x] ≥2 账号可演示：各自触发跑次、查看榜/他人结果（隔离或可过滤）
- [x] API 拒绝或跑次失败时 UI 不假成功
- [x] handoff 含 `Rewrote from: REF-MISSIONS`

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w2/`。
- 2026-09-14：同步 GitHub Issue #18。
- 2026-09-15：作业壳主导航「评测」+ EvalOpsPage；client 契约与纯逻辑测；用户手册 Preview 同步；手册收口仍属票 33。

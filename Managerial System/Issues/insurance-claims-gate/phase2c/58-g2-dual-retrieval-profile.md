# 58: G2 检索双剖面 demo_seed_eval + pilot_cloud_embed

**github_issue:** #45

**Status:** resolved

**Blocked by:** 57

**wave:** 2c

**spec_id:** SPEC-02C-LIVE-HONEST-SEAMS

**ref_id:** REF-CASE-RECALL, REF-CASE-KB

**Rewrote from:** REF-CASE-RECALL（召回脚本）；REF-CASE-KB（种子边界）

## 优先打开（只读参考）

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | SPEC-02C G2 / γ 附录 | 双剖面与失败停堆 |
| 2 | `本项目代码/claims-gate/docs/acceptance/recall-metrics-s2.md` | 既有 S2 验收 |
| 3 | Demo 检索种子与 H1/H2 门槛（SPEC-02B-P） | 门槛不变，允许多剖面数字 |

## What to build

并列报告 `demo_seed_eval` 与 `pilot_cloud_embed`（向量开）。指标脚本/产物必须带剖面标签；面试与手册强制「先剖面后数字」。evaluate 仍零向量/零 LLM。γ 仅当 pilot 剖面 H2 失败才允许另议，本票不实现 rerank。

## Acceptance criteria

- [x] 可生成两份剖面报告（或同一报告内明确分节），含剖面名
- [x] `pilot_cloud_embed`：`vector_enabled=true` 路径可跑（有 embedding Key 时）
- [x] 禁止验收/演示只甩无剖面标签的短路 1.00 冒充语义满分
- [x] H1/H2 门槛语义继承 02B-P；数字可低于 1.0
- [x] evaluate 路径无向量/LLM 依赖回归
- [x] 默认 `pytest -q` 仍绿（真云测旁路）

## Answer

`Rewrote from: REF-CASE-RECALL；REF-CASE-KB`

- 注册 `pilot_cloud_embed`；默认脚本并列双剖面报告（`report_kind=dual_retrieval_profile`）
- `vector_leg_active` + 缺搜索器诚实跳过；禁止关键词满分冒充语义
- 面试卡 / USER_GUIDE §3.6 / 验收件强制「先剖面后数字」
- S0：`321 passed, 26 deselected`（2026-09-16）

## Comments

- 2026-09-16：`/to-spec` 切票；Status=ready-for-agent。
- 2026-09-16：同步 GitHub Issue #45。
- 2026-09-16：实现合入；Status=resolved。

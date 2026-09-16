# 51: P-CFG β：只读连接状态（无 Key 回显）

**github_issue:** #38

**Status:** resolved

**Blocked by:** 44, 43

**wave:** 2b-P-β

**spec_id:** SPEC-02B-P-ASSIST-QUALITY

**ref_id:** REF-MISSIONS

**Rewrote from:** 质询 P-CFG

## 优先打开（只读参考）

路径相对于 \历史项目代码供参考/\。交付只写入 \本项目代码/claims-gate/\。

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | 见 ref_id | 加深缺口，勿平行重切 2a 主路径 |
| 2 | \docs/agents/phase2b-depth-planning-backlog.DRAFT.md\ | 已决议 registry |
| 3 | \Managerial System/SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md\ | DoD / 接缝 |

## What to build

只读 API 与/或作业壳区块：展示 LLM/Embedding/LangSmith 是否已配置、是否降级、当前模型名；永不回显 Key。

## Acceptance criteria

- [x] 连接状态只读可达
- [x] 响应/UI 无 Key 泄漏
- [x] 手册已说明
- [x] handoff 含 Rewrote from:

## Answer

`missions/provider_connection_status.py` 聚合 LLM/Embedding/LangSmith 肖像（configured / degraded / model|project；无 Key 字段）。LangSmith 仅在「想开但未可用」时 degraded。`GET /provider/connection-status`（须登录；ACL `read_provider_connection_status`，viewer 可读）。作业壳主导航「连接状态」页只渲染 API 字段。手册 `USER_GUIDE` §3.11 + CHANGELOG Unreleased；`.env.example` 指针。`Rewrote from: REF-MISSIONS`（质询 P-CFG β）。

## Comments

- 2026-09-15：\/to-spec\ 切票；Status=ready-for-agent。
- 2026-09-15：同步 GitHub Issue #38。
- 2026-09-16：\/implement\ 落地；Status=resolved；只读可达；无 Key 回显；手册已同步。

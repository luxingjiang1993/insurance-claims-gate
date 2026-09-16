# 43: P-CFG α：Provider 清单 + .env.example 分区 + USER_GUIDE

**github_issue:** #30

**Status:** resolved

**Blocked by:** —

**wave:** 2b-P-α

**spec_id:** SPEC-02B-P-ASSIST-QUALITY

**ref_id:** REF-MISSIONS

**Rewrote from:** REF-MISSIONS（质询 P-CFG）

## 优先打开（只读参考）

路径相对于 \历史项目代码供参考/\。交付只写入 \本项目代码/claims-gate/\。

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | 见 ref_id | 加深缺口，勿平行重切 2a 主路径 |
| 2 | \docs/agents/phase2b-depth-planning-backlog.DRAFT.md\ | 已决议 registry |
| 3 | \Managerial System/SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md\ | DoD / 接缝 |

## What to build

将 LLM/Embedding/LangSmith/本地 trace 等 Provider 清单写入 USER_GUIDE 与 .env.example 分区；强调密钥仅 claims-gate/.env、分 Key、OpenAI-compatible、换模检查单指针。不含连接状态 UI（β）。

## Acceptance criteria

- [x] USER_GUIDE Provider 表
- [x] .env.example 分区清晰
- [x] CHANGELOG Unreleased 同步
- [x] handoff 含 Rewrote from:

## Answer

`Rewrote from: REF-MISSIONS`（P-CFG α 文档半；Issue 43 / GitHub #30）

- `USER_GUIDE` 新增 §3.4 Provider 清单表（LLM / Embedding / LangSmith / 本地 trace / Chroma）；硬规则：密钥仅 `claims-gate/.env`、分 Key、OpenAI-compatible、换模检查单指针；明确连接状态 UI 属 β
- `.env.example` 分区 `[A]`–`[G]`（LLM / Embedding / Chroma / 检索 / 本地 trace / LangSmith）与手册对齐
- `CHANGELOG` Unreleased 同步；成熟度表增 Provider 行
- 无连接状态 UI/API 代码（β 票 51）

## Comments

- 2026-09-15：\/to-spec\ 切票；Status=ready-for-agent。
- 2026-09-15：同步 GitHub Issue #30。
- 2026-09-16：实现合入；Status=resolved。

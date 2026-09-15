# 34: Pilot 默认 cloud embedding；local 哈希仅 CI

**github_issue:** #21

**Status:** resolved

**Blocked by:** —

**wave:** 2b-P-α

**spec_id:** SPEC-02B-P-ASSIST-QUALITY

**ref_id:** REF-MISSIONS

**Rewrote from:** 现有 chroma_index（REF-MISSIONS 加深；非平行重切 2a）

## 优先打开（只读参考）

路径相对于 \历史项目代码供参考/\。交付只写入 \本项目代码/claims-gate/\。

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | 见 ref_id | 加深缺口，勿平行重切 2a 主路径 |
| 2 | \docs/agents/phase2b-depth-planning-backlog.DRAFT.md\ | 已决议 registry |
| 3 | \Managerial System/SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md\ | DoD / 接缝 |

## What to build

将 Pilot 推荐/文档默认改为 EMBEDDING_PROVIDER=cloud（独立 embedding Key）；local 哈希路径保留给 CI/rebuild，文案与降级提示必须标明非语义。evaluate 仍零向量依赖。缺 embedding Key 不得静默复用 OPENAI_API_KEY。

## Acceptance criteria

- [x] Pilot 文档与 .env.example 推荐 cloud 语义 embedding
- [x] local 路径标明非语义；CI/rebuild 可用
- [x] 分 Key；无静默 fallback
- [x] S0 默认 pytest 不因缺 cloud Key 变红
- [x] handoff 含 Rewrote from:

## Answer

`Rewrote from: REF-MISSIONS`（加深现有 `missions/chroma_index`；Issue 34 / GitHub #21）

- 默认 `EMBEDDING_PROVIDER=cloud`（dataclass + `from_env`）；独立 `CLAIMS_GATE_EMBEDDING_API_KEY` / `EMBEDDING_API_KEY`；**不**读 `OPENAI_API_KEY`
- `local` 显式配置；标签 `deterministic_local_non_semantic`；rebuild 脚本与 USER_GUIDE / `.env.example` 标明非语义
- 检索画像：`embedding_semantic=false` + notes 中文非语义提示
- S0：`pytest -q` 无 cloud Key 全绿
- 复审跟进：retrieve 画像测覆盖 local 非语义；换 provider 须 rebuild 写入手册/`.env.example`；cloud 缺 Key 时 rebuild 清晰退出码 2

Commits: `5a23cd7`, `bc0d6a2`

## Comments

- 2026-09-15：\/to-spec\ 切票；Status=ready-for-agent。
- 2026-09-15：同步 GitHub Issue #21。
- 2026-09-15：实现合入；Status=resolved。

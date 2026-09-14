# 24: 混合检索挂 assist：硬过滤 / 条款号短路 / 加权融合 / 三联门 / 向量降级

**github_issue:** #11

**Status:** ready-for-agent

**Blocked by:** 22, 23

**wave:** W1

**spec_id:** SPEC-02A-W1-PILOT-COMPLETE

**ref_id:** REF-MISSIONS, REF-CASE-RECALL, REF-RAG-CY, REF-CASE-HYBRID

**Rewrote from:** REF-CASE-RECALL, REF-RAG-CY, REF-CASE-HYBRID, REF-MISSIONS

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `CASE-高效召回/` | 混合召回与权重融合 |
| 2 | `RAG-cy/` | 检索+生成边界（本票只改 assist 检索） |
| 3 | 本仓既有 citation 三联门 | 提名≠合法引用 |

## What to build

仅在 AI 辅助（assist）路径挂载混合检索：效力栈/版本硬过滤 → 含条款号则关键词短路，否则并行关键词+向量 → 可配置线性加权（默认 keyword 0.7 / vector 0.3）→ 提名须过 doc_id+clause_item+version 三联门才可作为可采纳引用。向量不可用时自动关键词降级且可测。evaluate 确定性逻辑不变。S2 可用假 embedding；默认 CI 不要求真向量云。

## Acceptance criteria

- [ ] 混合检索仅挂 assist；规则 evaluate 不调用向量
- [ ] `keyword_weight` / `vector_weight` 可配置，默认 0.7/0.3；写入 `.env.example`
- [ ] 含明确条款号/clause_item 的查询走关键词短路（优先于加权融合）
- [ ] 提名过 citation 三联门方可标为可采纳引用；否则标记不可采纳或拒绝
- [ ] 向量故障/关闭时自动关键词降级可测（S2；可用假 embedding）
- [ ] 默认 `pytest -q` 不要求 Chroma/LLM/LangSmith
- [ ] handoff 含 `Rewrote from:` 所用 REF

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w1/`。
- 2026-09-14：同步 GitHub Issue #11。

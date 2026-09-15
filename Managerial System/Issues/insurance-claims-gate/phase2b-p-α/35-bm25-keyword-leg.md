# 35: 关键词腿 Jaccard 改为 BM25（jieba）；保留条款号短路

**github_issue:** #22

**Status:** resolved

**Blocked by:** —

**wave:** 2b-P-α

**spec_id:** SPEC-02B-P-ASSIST-QUALITY

**ref_id:** REF-CASE-RECALL, REF-CASE-KB

**Rewrote from:** REF-CASE-RECALL; REF-CASE-KB BM25

## 优先打开（只读参考）

路径相对于 \历史项目代码供参考/\。交付只写入 \本项目代码/claims-gate/\。

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | 见 ref_id | 加深缺口，勿平行重切 2a 主路径 |
| 2 | \docs/agents/phase2b-depth-planning-backlog.DRAFT.md\ | 已决议 registry |
| 3 | \Managerial System/SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md\ | DoD / 接缝 |

## What to build

assist 混检关键词腿由 Jaccard 换为 BM25（jieba 中文分词）；保留条款号/clause 短路与效力栈硬过滤；evaluate 不调用检索。

## Acceptance criteria

- [x] BM25 关键词腿可回归
- [x] 条款号短路行为保留
- [x] evaluate 零检索依赖
- [x] S1/S2 测覆盖；不进默认绿的真依赖保持标记
- [x] handoff 含 Rewrote from:

## Answer

`Rewrote from: REF-CASE-RECALL; REF-CASE-KB BM25`

- 交付：`本项目代码/claims-gate/src/missions/track_llm_optional/hybrid_retrieval.py` 关键词腿改为 BM25Okapi + jieba；portrait 暴露 `keyword_leg=bm25`。
- 条款号短路 / 效力栈硬过滤 / 线性融合权重未改；依赖：`jieba`、`rank-bm25`。
- 测试：S1 `tests/test_hybrid_retrieval.py`（含 BM25 回归、短路、evaluate 零依赖）；S2 `tests/track_llm_optional/test_hybrid_retrieval_fusion.py`（`track_llm_optional`）。
- 默认 `pytest -q`：166 passed。

## Comments

- 2026-09-15：\/to-spec\ 切票；Status=ready-for-agent。
- 2026-09-15：同步 GitHub Issue #22。
- 2026-09-15：claimed → implemented → resolved。

# 23: Chroma 索引 + 本地/云 embedding + 可重建

**github_issue:** #10

**Status:** resolved

**Blocked by:** 22

**wave:** W1

**spec_id:** SPEC-02A-W1-PILOT-COMPLETE

**ref_id:** REF-MISSIONS, REF-CASE-RECALL, REF-RAG-CY

**Rewrote from:** REF-CASE-RECALL, REF-RAG-CY, REF-MISSIONS

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `CASE-高效召回/` | 向量/召回索引与重建外形 |
| 2 | `RAG-cy/` | RAG 骨架与 KB 挂接 |
| 3 | Chroma 官方文档（依赖级） | 持久目录与 collection 约定 |

## What to build

为条款 KB（或约定子集）建立可重建的 Chroma 向量索引：默认本地 embedding，并支持可选云 embedding API。索引落在项目数据区；提供 rebuild 命令/脚本。规则 evaluate 路径不得依赖 Chroma。须声明 W0 DoD（票 22）已关闭或列出豁免。

## Acceptance criteria

- [x] Chroma 可索引约定条款子集并持久化；提供可重复执行的 rebuild 入口
- [x] 默认本地 embedding 可用；云 embedding 可通过配置切换（写入 `.env.example`）
- [x] 规则 evaluate 零向量/Chroma 依赖（S0 不因本票变红）
- [x] 票内或 handoff 声明 W0（22）已满足或豁免列表
- [x] handoff 含 `Rewrote from:` 所用 REF

## Answer

**Rewrote from: REF-CASE-RECALL, REF-RAG-CY, REF-MISSIONS**

**W0（票 22）声明：** 已 `resolved`；本票在 W0 DoD 关闭后实现，无豁免项。

- `src/missions/chroma_index/`：`rebuild_index` 将 `knowledge_base/` 全部条款块写入持久 Chroma（默认 `data/chroma`，collection `clauses_v1`）
- 默认 `EMBEDDING_PROVIDER=local`（确定性本地向量，无模型下载）；`cloud` 使用独立 `CLAIMS_GATE_EMBEDDING_API_KEY` / `EMBEDDING_*`
- 重建入口：`python scripts/rebuild_chroma_index.py`（可重复执行；KB 非空校验后再删同名 collection 全量写入）
- `.env.example` / `requirements.txt`（chromadb）已更新；规则 evaluate 源码零 chroma 依赖
- 测试：`tests/test_chroma_index_rebuild.py`（含 reopen 计数与 mock 云重建）；默认 `pytest -q`：`126 passed, 8 deselected`

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w1/`。
- 2026-09-14：同步 GitHub Issue #10。
- 2026-09-14：实现落地并 resolved。

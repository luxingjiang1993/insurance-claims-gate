# 12: 轨 B 最小检索起草（RAG-CY · llm_optional）

**Status:** resolved

**Blocked by:** 09

**ref_id:** REF-RAG-CY, REF-MISSIONS, REF-CASE-HYBRID

**Backlog:** P2-4（最小前置；完整方差预算可仍 open）

**Rewrote from:** REF-RAG-CY, REF-MISSIONS, REF-CASE-HYBRID

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `RAG-cy/src/retrieval.py` | 检索入口外形 |
| 2 | `RAG-cy/src/pipeline.py` | 管线编排（只借结构，换保险 KB） |
| 3 | `RAG-cy/docs/src_modules_overview.md` | 模块边界 |
| 4 | `本项目代码/claims-gate/src/missions/track_llm_optional/` | Issue 09 已有隔离占位 |
| 5 | `本项目代码/claims-gate/src/missions/retrieval_profiles.py` | 效力栈画像；轨 B 不得破坏 endorsement_priority 语义 |

## What to build

在 **轨 B 隔离目录**内落地最小「检索 → 辅助起草」能力：基于现有条款 KB（或只读切块），产出带 `inference_track=llm_optional` 的草稿辅助结果。  
允许确定性假检索（无真实 LLM key 时）以便本地跑通；若调用 LLM 必须可关闭且默认 CI 不依赖。

**硬约束：**

- 不得并入默认 `pytest` 合门禁；仅 `-m track_llm_optional`
- 规则 vs RAG 冲突仍 fail-closed 进人闸（与轨 A 一致）
- `handbook_ops` 不得单独支撑对外拒赔
- 禁止支付工具；禁止用本轨替代 Orchestrator 契约先行

## Acceptance criteria

- [x] `track_llm_optional` 下有可调用的最小检索/起草函数或 API 旁路
- [x] 响应或产物含 `inference_track=llm_optional`
- [x] `pytest -m track_llm_optional` 至少 1 条正向用例；失败不阻断 `pytest -q` 轨 A
- [x] 文档声明：完整方差预算 / 金标门槛数值化仍属 P2-4，本票只做最小可跑
- [x] handoff 含 `Rewrote from: REF-RAG-CY, REF-MISSIONS`（可含 HYBRID）

## Answer

轨 B 最小检索起草已落地：`missions/track_llm_optional/{retrieval,pipeline}.py` 提供 `retrieve_chunks` / `draft_assist`；产物固定 `inference_track=llm_optional`；默认确定性假检索（`enable_llm=False`）；规则 vs RAG 冲突 fail-closed 进人闸；`handbook_ops` 不可独撑对外拒赔。测试在 `tests/track_llm_optional/`，仅 `-m track_llm_optional`。完整方差预算仍属 P2-4。Rewrote from: REF-RAG-CY, REF-MISSIONS, REF-CASE-HYBRID。

## Comments

- 2026-09-13：current-phase-remaining 切票；吃清单一 `REF-RAG-CY`。
- 2026-09-14：实现完成；`draft_assist` + 隔离测试；Rewrote from: REF-RAG-CY, REF-MISSIONS, REF-CASE-HYBRID。
- 2026-09-16：修复 hybrid 融合只按分数排序冲掉 `endorsement_priority` 的问题；融合后保留 `type_rank`（与轨 A `rag.retrieve` 一致）；旁路测 `test_endorsement_priority_profile_preserved` + 默认合门禁 `test_endorsement_priority_survives_fusion_score_sort`。

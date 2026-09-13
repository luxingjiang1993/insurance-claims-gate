# 02: 条款 KB 最小集 + citation 条款项落库门

**Status:** resolved

**Blocked by:** 01

**ref_id:** REF-CASE-KB, REF-MISSIONS

**Backlog:** P0-2

**Rewrote from:** REF-CASE-KB, REF-MISSIONS

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `project 多agent/src/missions/rag.py` | `KnowledgeBase` 切块、`clause_id`/`doc_version`、检索与 `get_clause` |
| 2 | `project 多agent/src/missions/validator.py` | 独立检索 + `policy_clause_id` 不在库则失败 |
| 3 | `project 多agent/schemas/citation.schema.json` | citation 必填字段外形（换域时升为条款项级） |
| 4 | `project 多agent/knowledge_base/policies/` | 版本化政策 md 样例形态 |
| 5 | `CASE-知识库处理/4-知识库版本管理与性能比较.py` | 版本化 KB 思路 |
| 6 | `CASE-知识库处理/3-知识库健康度检查.py` | KB 健康/完整性检查 |

说明：Missions 现有 citation 以 `clause_id` 为主；本票须升到 SPEC 的 `doc_id` + `clause_item` + `doc_version` 三联校验，勿只抄「文档存在即过」。

## What to build

交付版本化主险/附加险/批单样例条款库，以及对外可用 citation 的条款项级落库门：校验必须同时命中 `doc_id`、`clause_item`、`doc_version`（或等价生效日键）。仅文档存在、条款项缺失、版本不匹配或摘录无法对应库内条目时失败关闭。可用 machine_check 独立验收「幻觉条款不过门」。不得用全文最大相似代替本校验。

## Acceptance criteria

- [x] KB 含至少支撑 SC-02/SC-03 的主险与批单样例，带版本/生效日
- [x] 合法 citation（doc_id + clause_item + doc_version）可通过存在性门
- [x] 库外 doc、错 clause_item、版本不匹配 → machine_check 失败，并映射 `CITATION_NOT_IN_KB`（或等价）
- [x] 校验粒度到条款项，不以「文档存在」或「全文最大相似」冒充通过
- [x] retrieval_profile 至少可区分 `clause_v_current` 与 `endorsement_priority` 的配置位（内容可在后续票消费）
- [x] handoff 含 `Rewrote from: REF-CASE-KB, REF-MISSIONS`

## Answer

- 主险/附加险/批单样例入库：`knowledge_base/policies|riders|endorsements/`，带 `doc_version` / 生效日。
- `KnowledgeBase.resolve_clause` / `validate_citation` 三联命中；HTTP `POST /kb/citations/validate`；`machine_check` type=`citation_in_kb`。
- 失败映射 `CITATION_NOT_IN_KB`；不以文档存在或最大相似冒充通过。
- `retrieval_profiles.py` 配置位：`clause_v_current`、`endorsement_priority`。
- 验收：`tests/test_citation_kb_gate.py`（7 passed）。

## Comments

- 2026-09-13：to-tickets 批准 defaults 后落盘。
- 2026-09-13：Issue 02 实现完成；Rewrote from: REF-CASE-KB, REF-MISSIONS；Status → done。
- 2026-09-13：关闭本票 Status → resolved；代码已在 main（`5dc6d0d` / `5d8b422`）。

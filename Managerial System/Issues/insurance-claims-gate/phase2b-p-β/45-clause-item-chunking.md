# 45: 条款项级切块 + 父条款回填

**github_issue:** #32

**Status:** resolved

**Blocked by:** 44, 34

**wave:** 2b-P-β

**spec_id:** SPEC-02B-P-ASSIST-QUALITY

**ref_id:** REF-CASE-KB

**Rewrote from:** RAGFlow 模板切块协议；REF-CASE-KB

## 优先打开（只读参考）

路径相对于 \历史项目代码供参考/\。交付只写入 \本项目代码/claims-gate/\。

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | 见 ref_id | 加深缺口，勿平行重切 2a 主路径 |
| 2 | \docs/agents/phase2b-depth-planning-backlog.DRAFT.md\ | 已决议 registry |
| 3 | \Managerial System/SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md\ | DoD / 接缝 |

## What to build

条款项级切块与父条款回填；人可改 chunk 后重建索引；citation 仍三联门。默认：一 clause_item 一块，过长按段切并回填父 id。

## Acceptance criteria

- [x] 切块+回填可重建
- [x] citation 三联门仍成立
- [x] handoff 含 Rewrote from:

## Answer

`Rewrote from: RAGFlow 模板切块协议；REF-CASE-KB` · Issue 45 / GitHub #32

- **切块模块：** `missions/clause_chunking.py` — 默认一 `clause_item` 一块；`len > DEFAULT_MAX_CHUNK_CHARS` 时按空行分段并回填 `parent_clause_item`；单块 `chunk_id` 保持 `doc::item::v`，多段加 `::p{n}`。
- **KB 加载：** `missions/rag.py` 接入切块；`resolve_clause_parts` + 摘录跨子块校验；citation 仍 `doc_id`+`clause_item`+`doc_version`。
- **重建：** `chroma_index/rebuild.py` 写入 `parent_clause_item` / `part_*` 元数据；人改 KB markdown 后 `python scripts/rebuild_chroma_index.py`。
- **检索：** `hybrid_retrieval` 的 `current_effective` 按版本保留全部子块（不再折叠成一块）。
- **测：** `tests/test_clause_item_chunking.py`（切块 / 改后重建 / 三联门 / 元数据）。
- **手册：** USER_GUIDE §3.4 重建说明 + CHANGELOG Unreleased；SPEC β 首项勾选。

## Comments

- 2026-09-15：\/to-spec\ 切票；Status=ready-for-agent。
- 2026-09-15：同步 GitHub Issue #32。
- 2026-09-16：实现落地；Status=resolved。

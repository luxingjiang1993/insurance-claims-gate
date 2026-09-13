"""轨 B 检索入口外形（借 RAG-cy retrieval 结构，换保险 KB）。

默认走确定性假检索（复用轨 A KnowledgeBase.retrieve），不依赖 LLM key。
Rewrote from: REF-RAG-CY, REF-MISSIONS
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from missions.models import RoleName
from missions.rag import KnowledgeBase
from missions.retrieval_profiles import RETRIEVAL_PROFILES


def default_kb_root() -> Path:
    """claims-gate/knowledge_base（相对本包向上四级）。"""
    return Path(__file__).resolve().parents[3] / "knowledge_base"


def retrieve_chunks(
    query: str,
    *,
    kb_root: Path | None = None,
    retrieval_profile: str = "clause_v_current",
    top_k: int = 3,
    clause_hint: str | None = None,
) -> list[dict[str, Any]]:
    """最小检索：返回可序列化 citation 字典列表。

    保留 endorsement_priority / clause_v_current / handbook_ops 配置位语义，
    不得另起一套效力栈。
    """
    if retrieval_profile not in RETRIEVAL_PROFILES:
        raise ValueError(f"未知 retrieval_profile: {retrieval_profile}")

    root = kb_root or default_kb_root()
    kb = KnowledgeBase(root)
    citations = kb.retrieve(
        query,
        role=RoleName.ORCHESTRATOR,
        profile=retrieval_profile,
        top_k=top_k,
        clause_hint=clause_hint,
    )

    # 附带 doc_type，便于轨 B 校验 handbook / endorsement 语义
    by_chunk: dict[str, str] = {c.chunk_id: c.doc_type for c in kb.chunks}
    out: list[dict[str, Any]] = []
    for c in citations:
        item = c.model_dump()
        item["doc_type"] = by_chunk.get(c.chunk_id, "")
        out.append(item)
    return out

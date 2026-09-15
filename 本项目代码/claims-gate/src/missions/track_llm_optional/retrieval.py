"""轨 B 检索入口：挂载混合检索（仅 assist）；evaluate 不得调用。

默认向量不可用时自动关键词降级；不要求默认 CI 有 Chroma / cloud Key。
Rewrote from: REF-MISSIONS（加深现有 chroma_index；Issue 34）
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, overload

from missions.retrieval_profiles import RETRIEVAL_PROFILES

from .hybrid_retrieval import HybridRetrievalConfig, hybrid_retrieve


def default_kb_root() -> Path:
    """claims-gate/knowledge_base（相对本包向上四级）。"""
    return Path(__file__).resolve().parents[3] / "knowledge_base"


def _try_build_vector_searcher():
    """尽力构建 Chroma 搜索器；失败返回 None（由 hybrid 降级）。"""
    try:
        from missions.chroma_index import ChromaIndexConfig

        from .chroma_search import ChromaVectorSearcher

        cfg = ChromaIndexConfig.from_env(kb_root=None)
        if not cfg.persist_dir.exists():
            return None, None
        return ChromaVectorSearcher(cfg), cfg
    except Exception:
        return None, None


@overload
def retrieve_chunks(
    query: str,
    *,
    kb_root: Path | None = None,
    retrieval_profile: str = "clause_v_current",
    top_k: int = 3,
    clause_hint: str | None = None,
    cfg: HybridRetrievalConfig | None = None,
    vector_searcher: Any | None = None,
    return_portrait: Literal[False] = False,
) -> list[dict[str, Any]]: ...


@overload
def retrieve_chunks(
    query: str,
    *,
    kb_root: Path | None = None,
    retrieval_profile: str = "clause_v_current",
    top_k: int = 3,
    clause_hint: str | None = None,
    cfg: HybridRetrievalConfig | None = None,
    vector_searcher: Any | None = None,
    return_portrait: Literal[True],
) -> tuple[list[dict[str, Any]], dict[str, Any]]: ...


def retrieve_chunks(
    query: str,
    *,
    kb_root: Path | None = None,
    retrieval_profile: str = "clause_v_current",
    top_k: int = 3,
    clause_hint: str | None = None,
    cfg: HybridRetrievalConfig | None = None,
    vector_searcher: Any | None = None,
    return_portrait: bool = False,
) -> list[dict[str, Any]] | tuple[list[dict[str, Any]], dict[str, Any]]:
    """混合检索：返回可序列化 citation 字典列表（含 adoptable）。

    clause_hint 若传入且 query 本身无条款号，会拼入查询以触发短路语义。
    """
    if retrieval_profile not in RETRIEVAL_PROFILES:
        raise ValueError(f"未知 retrieval_profile: {retrieval_profile}")

    q = query
    if clause_hint and clause_hint not in (query or ""):
        q = f"{query} 条款项:{clause_hint}"

    hybrid_cfg = cfg or HybridRetrievalConfig.from_env()
    searcher = vector_searcher
    chroma_cfg = None
    if searcher is None and hybrid_cfg.vector_enabled:
        searcher, chroma_cfg = _try_build_vector_searcher()
    # 注入的 ChromaVectorSearcher 也带 cfg，须同样写入诚实画像
    if chroma_cfg is None and searcher is not None:
        chroma_cfg = getattr(searcher, "cfg", None)

    citations, portrait = hybrid_retrieve(
        q,
        kb_root=kb_root or default_kb_root(),
        retrieval_profile=retrieval_profile,
        top_k=top_k,
        cfg=hybrid_cfg,
        vector_searcher=searcher,
    )
    if chroma_cfg is not None and portrait.get("vector_enabled"):
        portrait["chroma_collection"] = chroma_cfg.collection_name
        if chroma_cfg.embedding_provider == "cloud":
            portrait["embedding_model"] = chroma_cfg.embedding_model
            portrait["embedding_semantic"] = True
        else:
            from missions.chroma_index.embeddings import LOCAL_EMBEDDING_LABEL

            # local 哈希路径：画像明确标明非语义
            portrait["embedding_model"] = LOCAL_EMBEDDING_LABEL
            portrait["embedding_semantic"] = False
            notes = list(portrait.get("notes") or [])
            notes.append("embedding=local 哈希（非语义）；仅 CI/rebuild，不宣称语义质量")
            portrait["notes"] = notes
    if return_portrait:
        return citations, portrait
    return citations

"""S2：混合检索加权融合（假 embedding / 可注入向量腿）。

默认 CI 排除；需 `pytest -m track_llm_optional`。
Rewrote from: REF-CASE-RECALL, REF-RAG-CY, REF-CASE-HYBRID, REF-MISSIONS
"""

from __future__ import annotations

from pathlib import Path

import pytest

from missions.chroma_index import ChromaIndexConfig, rebuild_index
from missions.rag import KnowledgeBase
from missions.track_llm_optional.chroma_search import ChromaVectorSearcher
from missions.track_llm_optional.hybrid_retrieval import (
    HybridRetrievalConfig,
    hybrid_retrieve,
)

pytestmark = pytest.mark.track_llm_optional

ROOT = Path(__file__).resolve().parents[2]
KB_ROOT = ROOT / "knowledge_base"


def test_weighted_fusion_uses_keyword_and_vector_legs(tmp_path: Path) -> None:
    """假 embedding 重建 Chroma 后，混合模式 portrait 为 hybrid，且引用可采纳。"""
    persist = tmp_path / "chroma"
    cfg = ChromaIndexConfig(
        kb_root=KB_ROOT,
        persist_dir=persist,
        collection_name="clauses_v1",
        embedding_provider="local",
    )
    rebuild_index(cfg)
    searcher = ChromaVectorSearcher(cfg)

    citations, portrait = hybrid_retrieve(
        "疾病导致的摔伤是否属于责任免除",
        kb_root=KB_ROOT,
        top_k=3,
        cfg=HybridRetrievalConfig(
            keyword_weight=0.7, vector_weight=0.3, vector_enabled=True
        ),
        vector_searcher=searcher,
    )
    assert portrait["mode"] == "hybrid"
    assert portrait["vector_enabled"] is True
    assert portrait["keyword_weight"] == pytest.approx(0.7)
    assert portrait["vector_weight"] == pytest.approx(0.3)
    assert portrait["clause_short_circuit"] is False
    assert len(citations) >= 1
    assert all("adoptable" in c for c in citations)
    # 至少一条可采纳（落库门通过）
    assert any(c.get("adoptable") is True for c in citations)


def test_injected_vector_scores_affect_fusion_ranking() -> None:
    """注入向量腿抬高低关键词命中块时，融合排序应体现向量权重。"""
    kb = KnowledgeBase(KB_ROOT)
    # 选两个 main_policy 块：一个强关键词命中，一个弱命中但向量高分
    main = [c for c in kb.chunks if c.doc_type == "main_policy"]
    assert len(main) >= 2
    strong = next(c for c in main if c.clause_item == "ART-5-EXCL")
    weak = next(c for c in main if c.clause_item == "ART-2-COVER")

    class _BoostWeak:
        def search(self, query: str, *, top_k: int, where=None):  # noqa: ANN001
            return [
                {"chunk_id": weak.chunk_id, "score": 1.0},
                {"chunk_id": strong.chunk_id, "score": 0.01},
            ]

    # 极高向量权重：弱关键词块应排到前面
    cites, portrait = hybrid_retrieve(
        "疾病摔伤除外",
        kb_root=KB_ROOT,
        top_k=2,
        cfg=HybridRetrievalConfig(
            keyword_weight=0.1, vector_weight=0.9, vector_enabled=True
        ),
        vector_searcher=_BoostWeak(),
    )
    assert portrait["mode"] == "hybrid"
    assert cites[0]["chunk_id"] == weak.chunk_id

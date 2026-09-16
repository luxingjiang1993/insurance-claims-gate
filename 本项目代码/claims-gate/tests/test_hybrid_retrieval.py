"""接缝：混合检索（仅 assist）— BM25 关键词腿 / 条款号短路 / 三联门 / 向量降级。

Rewrote from: REF-CASE-RECALL, REF-CASE-KB, REF-RAG-CY, REF-CASE-HYBRID, REF-MISSIONS
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
KB_ROOT = ROOT / "knowledge_base"


def test_hybrid_weights_default_and_configurable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """接缝：keyword_weight/vector_weight 默认 0.7/0.3，可经环境变量覆盖。"""
    from missions.track_llm_optional.hybrid_retrieval import HybridRetrievalConfig

    default = HybridRetrievalConfig.from_env(env={})
    assert default.keyword_weight == pytest.approx(0.7)
    assert default.vector_weight == pytest.approx(0.3)

    overridden = HybridRetrievalConfig.from_env(
        env={"KEYWORD_WEIGHT": "0.55", "VECTOR_WEIGHT": "0.45"}
    )
    assert overridden.keyword_weight == pytest.approx(0.55)
    assert overridden.vector_weight == pytest.approx(0.45)


def test_env_example_documents_hybrid_weights() -> None:
    """接缝：.env.example 写入 keyword/vector 权重配置项。"""
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "KEYWORD_WEIGHT" in text
    assert "VECTOR_WEIGHT" in text
    assert "0.7" in text
    assert "0.3" in text


def test_keyword_leg_is_bm25_with_jieba() -> None:
    """接缝（S1）：assist 关键词腿为 BM25（jieba），中文自由文本可召回相关条款。"""
    from missions.track_llm_optional.hybrid_retrieval import (
        HybridRetrievalConfig,
        hybrid_retrieve,
    )

    citations, portrait = hybrid_retrieve(
        "疾病导致的摔伤是否属于责任免除",
        kb_root=KB_ROOT,
        retrieval_profile="clause_v_current",
        top_k=5,
        cfg=HybridRetrievalConfig(vector_enabled=False),
        vector_searcher=None,
    )
    assert portrait.get("keyword_leg") == "bm25"
    assert portrait["clause_short_circuit"] is False
    assert len(citations) >= 1
    # 语义难例：BM25+jieba 应把除外责任条款提到前列
    top_items = [c.get("clause_item") for c in citations]
    assert "ART-5-EXCL" in top_items


def test_clause_item_query_short_circuits_keyword() -> None:
    """接缝：含明确条款号的查询走关键词短路，不走加权融合。"""
    from missions.track_llm_optional.hybrid_retrieval import (
        HybridRetrievalConfig,
        hybrid_retrieve,
    )

    class _MustNotCallVector:
        def search(self, query: str, *, top_k: int, where=None):  # noqa: ANN001
            raise AssertionError("条款号短路不得调用向量腿")

    citations, portrait = hybrid_retrieve(
        "请核对条款项 ART-5-EXCL 是否适用疾病摔伤",
        kb_root=KB_ROOT,
        retrieval_profile="clause_v_current",
        top_k=3,
        cfg=HybridRetrievalConfig(keyword_weight=0.7, vector_weight=0.3, vector_enabled=True),
        vector_searcher=_MustNotCallVector(),
    )
    assert portrait["clause_short_circuit"] is True
    assert portrait["mode"] == "keyword_short_circuit"
    assert portrait.get("keyword_leg") == "bm25"
    assert len(citations) >= 1
    assert any(c.get("clause_item") == "ART-5-EXCL" for c in citations)
    # 短路时条款号命中应排第一
    assert citations[0].get("clause_item") == "ART-5-EXCL"


def test_clause_short_circuit_exact_hit_beats_prefer_doc_type_order() -> None:
    """接缝（S0）：条款号精确命中优先于 prefer_doc_types 类型序（手册/批单不被主险淹没）。"""
    from missions.track_llm_optional.hybrid_retrieval import (
        HybridRetrievalConfig,
        hybrid_retrieve,
    )

    cfg = HybridRetrievalConfig(vector_enabled=False)
    citations, portrait = hybrid_retrieve(
        "材料受理状态依据 POL-CLAIM-001",
        kb_root=KB_ROOT,
        retrieval_profile="demo_seed_eval",
        top_k=3,
        cfg=cfg,
        vector_searcher=None,
    )
    assert portrait["clause_short_circuit"] is True
    assert citations[0].get("clause_item") == "POL-CLAIM-001"


def test_nominations_marked_adoptable_via_citation_gate() -> None:
    """接缝：过三联门标 adoptable=True；伪造提名标不可采纳。"""
    from missions.track_llm_optional.hybrid_retrieval import (
        HybridRetrievalConfig,
        apply_citation_gate,
        hybrid_retrieve,
    )
    from missions.rag import KnowledgeBase

    citations, _portrait = hybrid_retrieve(
        "疾病导致的摔伤是否属于责任免除",
        kb_root=KB_ROOT,
        cfg=HybridRetrievalConfig(vector_enabled=False),
        vector_searcher=None,
    )
    assert citations, "应有关键词提名"
    for c in citations:
        assert "adoptable" in c
        if c["adoptable"]:
            assert c.get("doc_id") and c.get("clause_item") and c.get("doc_version")
        else:
            assert c.get("reject_reason")

    # 伪造库外提名：必须不可采纳
    kb = KnowledgeBase(KB_ROOT)
    fake = [
        {
            "doc_id": "NO-SUCH-DOC",
            "clause_item": "ART-X",
            "doc_version": "9.9",
            "quote": "幻觉条款",
            "chunk_id": "fake",
            "score": 0.9,
        }
    ]
    gated = apply_citation_gate(kb, fake)
    assert gated[0]["adoptable"] is False
    assert gated[0].get("reject_reason")


def test_vector_disabled_or_failure_degrades_to_keyword() -> None:
    """接缝：向量关闭或故障时自动关键词降级且可测。"""
    from missions.track_llm_optional.hybrid_retrieval import (
        HybridRetrievalConfig,
        hybrid_retrieve,
    )

    # 关闭向量
    cites_off, portrait_off = hybrid_retrieve(
        "疾病摔伤除外责任",
        kb_root=KB_ROOT,
        cfg=HybridRetrievalConfig(vector_enabled=False),
        vector_searcher=None,
    )
    assert len(cites_off) >= 1
    assert portrait_off["mode"] in ("keyword", "keyword_degraded")
    assert portrait_off["vector_enabled"] is False

    class _FailingVector:
        def search(self, query: str, *, top_k: int, where=None):  # noqa: ANN001
            raise RuntimeError("chroma_down")

    cites_fail, portrait_fail = hybrid_retrieve(
        "疾病摔伤除外责任",
        kb_root=KB_ROOT,
        cfg=HybridRetrievalConfig(vector_enabled=True),
        vector_searcher=_FailingVector(),
    )
    assert len(cites_fail) >= 1
    assert portrait_fail["vector_degraded"] is True
    assert portrait_fail["mode"] == "keyword_degraded"
    assert "vector_error" in str(portrait_fail.get("degrade_reason") or "")


def test_endorsement_priority_survives_fusion_score_sort() -> None:
    """接缝：endorsement_priority 融合后仍先批单后主险（不得被 BM25 高分主险冲掉）。"""
    from missions.track_llm_optional.hybrid_retrieval import (
        HybridRetrievalConfig,
        hybrid_retrieve,
    )

    citations, portrait = hybrid_retrieve(
        "免赔额批单覆盖主险",
        kb_root=KB_ROOT,
        retrieval_profile="endorsement_priority",
        top_k=5,
        cfg=HybridRetrievalConfig(vector_enabled=False),
        vector_searcher=None,
    )
    assert portrait.get("profile_type_order") is True
    assert citations, "应召回批单与主险候选"
    types_in_order = [str(c.get("doc_type") or "") for c in citations]
    assert "endorsement" in types_in_order
    assert "main_policy" in types_in_order
    assert types_in_order.index("endorsement") < types_in_order.index("main_policy")
    first = citations[0]
    assert first.get("doc_type") in {"endorsement", "special_agreement"} or "END" in str(
        first.get("doc_id") or ""
    ).upper()


def test_evaluate_modules_still_zero_chroma_dependency() -> None:
    """接缝（S0）：规则 evaluate 相关模块不得导入检索 / BM25 / chroma。"""
    forbidden = (
        "chromadb",
        "chroma_index",
        "missions.chroma_index",
        "hybrid_retrieval",
        "jieba",
        "rank_bm25",
    )
    evaluate_modules = [
        SRC / "claims_api" / "service.py",
        SRC / "claims_api" / "api.py",
        SRC / "claims_api" / "latch_matrix.py",
        SRC / "missions" / "rag.py",
        SRC / "missions" / "router.py",
        SRC / "missions" / "checks.py",
    ]
    for path in evaluate_modules:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    assert not any(f in name for f in forbidden), f"{path.name} imports {name}"
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert not any(f in mod for f in forbidden), f"{path.name} from-imports {mod}"

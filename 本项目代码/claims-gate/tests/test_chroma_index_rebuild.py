"""接缝：Chroma 索引重建 + Pilot cloud 默认 + evaluate 零向量依赖。

Rewrote from: REF-MISSIONS（加深现有 chroma_index；Issue 34）
"""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import MagicMock

import chromadb
import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
KB_ROOT = ROOT / "knowledge_base"


def _collection_count(persist_dir: Path, name: str) -> int:
    """重新打开持久客户端，核对 collection 条数。"""
    client = chromadb.PersistentClient(path=str(persist_dir))
    return int(client.get_collection(name).count())


def test_rebuild_index_persists_and_is_idempotent(tmp_path: Path) -> None:
    """接缝 1：rebuild_index 索引 KB 条款子集并持久化；可重复执行。"""
    from missions.chroma_index import ChromaIndexConfig, rebuild_index
    from missions.rag import KnowledgeBase

    persist_dir = tmp_path / "chroma"
    cfg = ChromaIndexConfig(
        kb_root=KB_ROOT,
        persist_dir=persist_dir,
        collection_name="clauses_v1",
        embedding_provider="local",
    )
    kb = KnowledgeBase(KB_ROOT)
    assert kb.chunks, "约定子集须非空"

    first = rebuild_index(cfg)
    assert first.chunk_count == len(kb.chunks)
    assert first.collection_name == "clauses_v1"
    assert persist_dir.is_dir()
    assert _collection_count(persist_dir, "clauses_v1") == first.chunk_count

    second = rebuild_index(cfg)
    assert second.chunk_count == first.chunk_count
    assert second.collection_name == first.collection_name
    assert _collection_count(persist_dir, "clauses_v1") == second.chunk_count


def test_pilot_default_embedding_provider_is_cloud() -> None:
    """接缝 2a：Pilot 默认 EMBEDDING_PROVIDER=cloud（空 env / 未设置）。"""
    from missions.chroma_index import ChromaIndexConfig

    cfg = ChromaIndexConfig.from_env(
        kb_root=KB_ROOT,
        persist_dir=Path("/tmp/chroma_unused"),
        env={},
    )
    assert cfg.embedding_provider == "cloud"
    assert ChromaIndexConfig(
        kb_root=KB_ROOT,
        persist_dir=Path("/tmp/chroma_unused"),
    ).embedding_provider == "cloud"


def test_local_embedding_explicit_and_labeled_non_semantic() -> None:
    """接缝 2b：local 须显式配置；画像/标签标明非语义（供 CI/rebuild）。"""
    from missions.chroma_index import (
        ChromaIndexConfig,
        resolve_embedding_provider,
    )
    from missions.chroma_index.embeddings import (
        LOCAL_EMBEDDING_LABEL,
        DeterministicLocalEmbedding,
    )

    cfg = ChromaIndexConfig.from_env(
        kb_root=KB_ROOT,
        persist_dir=Path("/tmp/chroma_local"),
        env={"EMBEDDING_PROVIDER": "local"},
    )
    assert cfg.embedding_provider == "local"
    emb = resolve_embedding_provider(cfg)
    assert isinstance(emb, DeterministicLocalEmbedding)
    assert "non_semantic" in LOCAL_EMBEDDING_LABEL
    assert LOCAL_EMBEDDING_LABEL == "deterministic_local_non_semantic"
    # 中文「非语义」出现在类文档与 rebuild/降级文案，而非机器标签字面量
    assert "非语义" in (DeterministicLocalEmbedding.__doc__ or "")


def test_retrieve_portrait_labels_local_embedding_non_semantic(
    tmp_path: Path,
) -> None:
    """接缝 2b-portrait：local 索引下 retrieve 画像标明非语义。"""
    from missions.chroma_index import (
        ChromaIndexConfig,
        LOCAL_EMBEDDING_LABEL,
        rebuild_index,
    )
    from missions.track_llm_optional.chroma_search import ChromaVectorSearcher
    from missions.track_llm_optional.hybrid_retrieval import HybridRetrievalConfig
    from missions.track_llm_optional.retrieval import retrieve_chunks

    persist = tmp_path / "chroma_local"
    cfg = ChromaIndexConfig(
        kb_root=KB_ROOT,
        persist_dir=persist,
        embedding_provider="local",
    )
    rebuild_index(cfg)
    searcher = ChromaVectorSearcher(cfg)
    _citations, portrait = retrieve_chunks(
        "意外医疗费用",
        kb_root=KB_ROOT,
        vector_searcher=searcher,
        cfg=HybridRetrievalConfig(
            keyword_weight=0.7, vector_weight=0.3, vector_enabled=True
        ),
        return_portrait=True,
    )
    assert portrait.get("vector_enabled") is True
    assert portrait.get("embedding_model") == LOCAL_EMBEDDING_LABEL
    assert portrait.get("embedding_semantic") is False
    notes = " ".join(str(n) for n in (portrait.get("notes") or []))
    assert "非语义" in notes


def test_cloud_embedding_never_silently_reuses_openai_api_key() -> None:
    """接缝 2c：缺 embedding Key 时不得静默复用 OPENAI_API_KEY。"""
    from missions.chroma_index import (
        ChromaIndexConfig,
        resolve_embedding_provider,
    )

    cfg = ChromaIndexConfig.from_env(
        kb_root=KB_ROOT,
        persist_dir=Path("/tmp/chroma_cloud"),
        env={
            "EMBEDDING_PROVIDER": "cloud",
            "OPENAI_API_KEY": "sk-llm-only-must-not-be-reused",
        },
    )
    assert cfg.embedding_api_key == ""
    with pytest.raises(ValueError, match="CLAIMS_GATE_EMBEDDING_API_KEY|EMBEDDING_API_KEY"):
        resolve_embedding_provider(cfg)


def test_embedding_provider_cloud_rebuild_with_dedicated_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """接缝 2d：独立 embedding Key 下 cloud 可重建索引。"""
    from missions.chroma_index import (
        ChromaIndexConfig,
        rebuild_index,
        resolve_embedding_provider,
    )
    from missions.chroma_index.embeddings import CloudEmbedding
    from missions.rag import KnowledgeBase

    monkeypatch.setenv("EMBEDDING_PROVIDER", "cloud")
    monkeypatch.setenv("CLAIMS_GATE_EMBEDDING_API_KEY", "test-key")
    monkeypatch.setenv("EMBEDDING_BASE_URL", "https://example.invalid/v1")
    monkeypatch.setenv("EMBEDDING_MODEL", "text-embedding-3-small")
    cloud_cfg = ChromaIndexConfig.from_env(
        kb_root=KB_ROOT,
        persist_dir=tmp_path / "chroma_cloud",
    )
    assert cloud_cfg.embedding_provider == "cloud"
    cloud_emb = resolve_embedding_provider(cloud_cfg)
    assert isinstance(cloud_emb, CloudEmbedding)
    assert cloud_emb.api_key == "test-key"
    assert cloud_emb.base_url.rstrip("/") == "https://example.invalid/v1"
    assert cloud_emb.model == "text-embedding-3-small"

    kb = KnowledgeBase(KB_ROOT)
    dim = 8

    def fake_post(url: str, headers=None, json=None):  # noqa: ANN001
        assert url.endswith("/embeddings")
        assert headers["Authorization"] == "Bearer test-key"
        texts = json["input"]
        body = {
            "data": [
                {"index": i, "embedding": [float((i + 1) % dim) / dim] * dim}
                for i in range(len(texts))
            ]
        }
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json = MagicMock(return_value=body)
        return resp

    monkeypatch.setattr(httpx.Client, "post", lambda self, *a, **k: fake_post(*a, **k))
    cloud_result = rebuild_index(cloud_cfg)
    assert cloud_result.chunk_count == len(kb.chunks)
    assert cloud_result.embedding_provider == "cloud"
    assert _collection_count(tmp_path / "chroma_cloud", "clauses_v1") == cloud_result.chunk_count


def test_env_example_recommends_cloud_and_separates_keys() -> None:
    """接缝 2e：.env.example Pilot 推荐 cloud；分 Key；local 标明非语义。"""
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "EMBEDDING_PROVIDER=cloud" in text
    assert "CLAIMS_GATE_EMBEDDING_API_KEY" in text
    assert "非语义" in text
    # 不得暗示缺 embedding Key 时可复用 OPENAI_API_KEY
    assert "不得静默" in text or "不得复用" in text or "禁止复用" in text


def test_evaluate_path_has_zero_chroma_dependency() -> None:
    """接缝 3：规则 evaluate 路径源码不得依赖 chromadb / chroma_index。"""
    forbidden = ("chromadb", "chroma_index", "missions.chroma_index")
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

"""接缝：Chroma 索引重建 + embedding 切换 + evaluate 零向量依赖。

Rewrote from: REF-CASE-RECALL, REF-RAG-CY, REF-MISSIONS
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


def test_embedding_provider_switch_local_vs_cloud(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """接缝 2：默认 local；云 embedding 可由 EMBEDDING_PROVIDER=cloud 切换并重建。"""
    from missions.chroma_index import (
        ChromaIndexConfig,
        rebuild_index,
        resolve_embedding_provider,
    )
    from missions.chroma_index.embeddings import CloudEmbedding, DeterministicLocalEmbedding
    from missions.rag import KnowledgeBase

    local_cfg = ChromaIndexConfig.from_env(
        kb_root=KB_ROOT,
        persist_dir=tmp_path / "chroma_local",
        env={},
    )
    assert local_cfg.embedding_provider == "local"
    local_emb = resolve_embedding_provider(local_cfg)
    assert isinstance(local_emb, DeterministicLocalEmbedding)

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

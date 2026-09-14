"""条款 KB → Chroma 可重建向量索引。

Rewrote from: REF-CASE-RECALL, REF-RAG-CY, REF-MISSIONS
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import chromadb

from missions.rag import KnowledgeBase

from .config import ChromaIndexConfig
from .embeddings import (
    CloudEmbedding,
    DeterministicLocalEmbedding,
    EmbeddingProvider,
)


@dataclass(frozen=True)
class RebuildResult:
    """重建结果摘要（对外接缝）。"""

    chunk_count: int
    collection_name: str
    persist_dir: str
    embedding_provider: str


def resolve_embedding_provider(cfg: ChromaIndexConfig) -> EmbeddingProvider:
    """按配置解析 embedding 实现。"""
    if cfg.embedding_provider == "local":
        return DeterministicLocalEmbedding(dim=cfg.embedding_dim)
    if cfg.embedding_provider == "cloud":
        return CloudEmbedding(
            api_key=cfg.embedding_api_key,
            base_url=cfg.embedding_base_url,
            model=cfg.embedding_model,
        )
    raise ValueError(f"未知 embedding_provider: {cfg.embedding_provider}")


def _open_collection(cfg: ChromaIndexConfig) -> Any:
    cfg.persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(cfg.persist_dir))
    # 可重复重建：先删同名 collection 再创建
    existing = {c.name for c in client.list_collections()}
    if cfg.collection_name in existing:
        client.delete_collection(cfg.collection_name)
    return client.create_collection(
        name=cfg.collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def rebuild_index(
    cfg: ChromaIndexConfig,
    *,
    embedding: EmbeddingProvider | None = None,
) -> RebuildResult:
    """索引 KnowledgeBase 全部条款块到 Chroma 并持久化。

    可重复执行：每次清空同名 collection 后全量写入。
    KB 为空时直接失败，避免误删已有索引。
    规则 evaluate 不得调用本函数。
    """
    kb = KnowledgeBase(cfg.kb_root)
    chunks = list(kb.chunks)
    if not chunks:
        raise ValueError(f"知识库无条款块可索引: {cfg.kb_root}")

    emb = embedding or resolve_embedding_provider(cfg)
    collection = _open_collection(cfg)

    ids = [c.chunk_id for c in chunks]
    documents = [c.text for c in chunks]
    metadatas: list[dict[str, Any]] = [
        {
            "doc_id": c.doc_id,
            "clause_id": c.clause_id,
            "clause_item": c.clause_item,
            "doc_version": c.doc_version,
            "effective_date": c.effective_date,
            "doc_type": c.doc_type,
            "authority_rank": c.authority_rank,
            "title": c.title,
        }
        for c in chunks
    ]
    vectors = emb.embed_documents(documents)
    # Chroma 批量上限保守分片
    batch = 64
    for i in range(0, len(ids), batch):
        collection.add(
            ids=ids[i : i + batch],
            documents=documents[i : i + batch],
            metadatas=metadatas[i : i + batch],
            embeddings=vectors[i : i + batch],
        )

    return RebuildResult(
        chunk_count=len(chunks),
        collection_name=cfg.collection_name,
        persist_dir=str(cfg.persist_dir),
        embedding_provider=cfg.embedding_provider,
    )

"""Chroma 向量检索适配（仅 assist；失败由 hybrid 降级）。

Rewrote from: REF-CASE-RECALL, REF-RAG-CY, REF-MISSIONS
"""

from __future__ import annotations

from typing import Any

import chromadb

from missions.chroma_index.config import ChromaIndexConfig
from missions.chroma_index.embeddings import EmbeddingProvider
from missions.chroma_index.rebuild import resolve_embedding_provider


class ChromaVectorSearcher:
    """对已重建的 Chroma collection 做 query；供 hybrid_retrieve 注入。"""

    def __init__(
        self,
        cfg: ChromaIndexConfig,
        *,
        embedding: EmbeddingProvider | None = None,
    ) -> None:
        self.cfg = cfg
        self._embedding = embedding or resolve_embedding_provider(cfg)

    def search(
        self,
        query: str,
        *,
        top_k: int,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        client = chromadb.PersistentClient(path=str(self.cfg.persist_dir))
        collection = client.get_collection(self.cfg.collection_name)
        q_emb = self._embedding.embed_documents([query])[0]
        kwargs: dict[str, Any] = {
            "query_embeddings": [q_emb],
            "n_results": max(1, top_k),
            "include": ["metadatas", "distances", "documents"],
        }
        if where:
            kwargs["where"] = where
        raw = collection.query(**kwargs)
        ids = (raw.get("ids") or [[]])[0]
        distances = (raw.get("distances") or [[]])[0]
        metadatas = (raw.get("metadatas") or [[]])[0]
        out: list[dict[str, Any]] = []
        for i, cid in enumerate(ids):
            dist = float(distances[i]) if i < len(distances) else 1.0
            # cosine distance → 相似度分数（越大越好）
            score = max(0.0, 1.0 - dist)
            meta = metadatas[i] if i < len(metadatas) and metadatas[i] else {}
            out.append(
                {
                    "chunk_id": cid,
                    "score": score,
                    "metadata": dict(meta),
                    "doc_id": meta.get("doc_id"),
                    "clause_item": meta.get("clause_item"),
                    "doc_version": meta.get("doc_version"),
                }
            )
        return out

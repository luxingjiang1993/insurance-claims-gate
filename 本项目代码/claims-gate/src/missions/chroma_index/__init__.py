"""Chroma 条款向量索引（仅 AI 辅助路径；规则 evaluate 不得依赖）。

Pilot 默认 cloud；local 哈希（非语义）仅 CI/rebuild。
Rewrote from: REF-MISSIONS（加深现有 chroma_index；Issue 34）
"""

from .config import ChromaIndexConfig
from .embeddings import (
    LOCAL_EMBEDDING_LABEL,
    CloudEmbedding,
    DeterministicLocalEmbedding,
)
from .rebuild import RebuildResult, rebuild_index, resolve_embedding_provider

__all__ = [
    "ChromaIndexConfig",
    "CloudEmbedding",
    "DeterministicLocalEmbedding",
    "LOCAL_EMBEDDING_LABEL",
    "RebuildResult",
    "rebuild_index",
    "resolve_embedding_provider",
]

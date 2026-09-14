"""Chroma 条款向量索引（仅 AI 辅助路径；规则 evaluate 不得依赖）。

Rewrote from: REF-CASE-RECALL, REF-RAG-CY, REF-MISSIONS
"""

from .config import ChromaIndexConfig
from .embeddings import CloudEmbedding, DeterministicLocalEmbedding
from .rebuild import RebuildResult, rebuild_index, resolve_embedding_provider

__all__ = [
    "ChromaIndexConfig",
    "CloudEmbedding",
    "DeterministicLocalEmbedding",
    "RebuildResult",
    "rebuild_index",
    "resolve_embedding_provider",
]

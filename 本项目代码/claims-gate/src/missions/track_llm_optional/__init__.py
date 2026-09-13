"""轨 B（llm_optional）隔离包：最小检索起草；禁止并入默认 CI 绿门。

Rewrote from: REF-RAG-CY, REF-MISSIONS, REF-CASE-HYBRID
"""

from .config import TrackBConfig
from .pipeline import DraftAssistResult, draft_assist
from .retrieval import retrieve_chunks

__all__ = [
    "TrackBConfig",
    "DraftAssistResult",
    "draft_assist",
    "retrieve_chunks",
]

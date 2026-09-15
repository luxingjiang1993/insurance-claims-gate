"""Chroma 索引配置：持久目录与 embedding 切换。

Pilot 默认 cloud 语义 embedding；local 哈希仅 CI/rebuild（非语义）。
缺 embedding Key 不得静默复用 OPENAI_API_KEY。

Rewrote from: REF-MISSIONS（加深现有 chroma_index；Issue 34）
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


def _default_persist_dir() -> Path:
    """项目数据区：claims-gate/data/chroma。"""
    return Path(__file__).resolve().parents[3] / "data" / "chroma"


def _default_kb_root() -> Path:
    return Path(__file__).resolve().parents[3] / "knowledge_base"


@dataclass(frozen=True)
class ChromaIndexConfig:
    """重建索引配置。embedding_provider: local | cloud。

    Pilot 推荐/默认 = cloud；local = 确定性哈希（非语义），供 CI/rebuild。
    """

    kb_root: Path
    persist_dir: Path
    collection_name: str = "clauses_v1"
    embedding_provider: str = "cloud"
    embedding_dim: int = 64
    # 云端（与 LLM Key 分离；禁止回落到 OPENAI_API_KEY）
    embedding_api_key: str = ""
    embedding_base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"

    @classmethod
    def from_env(
        cls,
        *,
        kb_root: Path | None = None,
        persist_dir: Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> ChromaIndexConfig:
        e = dict(os.environ) if env is None else dict(env)
        provider = (e.get("EMBEDDING_PROVIDER") or "cloud").strip().lower()
        if provider not in ("local", "cloud"):
            raise ValueError(f"不支持的 EMBEDDING_PROVIDER: {provider}")
        # 仅认独立 embedding Key；刻意不读取 OPENAI_API_KEY / CLAIMS_GATE_LLM_API_KEY
        api_key = (
            e.get("CLAIMS_GATE_EMBEDDING_API_KEY")
            or e.get("EMBEDDING_API_KEY")
            or ""
        ).strip()
        base_url = (
            e.get("EMBEDDING_BASE_URL") or "https://api.openai.com/v1"
        ).strip()
        model = (e.get("EMBEDDING_MODEL") or "text-embedding-3-small").strip()
        collection = (e.get("CHROMA_COLLECTION") or "clauses_v1").strip()
        persist_raw = e.get("CHROMA_PERSIST_DIR")
        persist = (
            Path(persist_raw)
            if persist_raw
            else (persist_dir or _default_persist_dir())
        )
        return cls(
            kb_root=kb_root or _default_kb_root(),
            persist_dir=persist,
            collection_name=collection,
            embedding_provider=provider,
            embedding_api_key=api_key,
            embedding_base_url=base_url,
            embedding_model=model,
        )

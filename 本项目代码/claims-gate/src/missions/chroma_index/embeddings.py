"""Embedding 提供方：默认本地确定性向量；可选云 API。

Rewrote from: REF-RAG-CY, REF-CASE-RECALL
"""

from __future__ import annotations

import hashlib
import math
from typing import Protocol

import httpx


class EmbeddingProvider(Protocol):
    """对外接缝：批量文档嵌入。"""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...


class DeterministicLocalEmbedding:
    """默认本地 embedding：纯哈希确定性向量，无云、无模型下载。

    供重建/CI 使用；不冒充语义质量模型。
    """

    def __init__(self, dim: int = 64) -> None:
        if dim <= 0:
            raise ValueError("dim 必须为正整数")
        self.dim = dim

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        # 扩展到 dim 个字节再归一化
        raw: list[float] = []
        seed = digest
        while len(raw) < self.dim:
            for b in seed:
                raw.append((b / 255.0) * 2.0 - 1.0)
                if len(raw) >= self.dim:
                    break
            seed = hashlib.sha256(seed).digest()
        norm = math.sqrt(sum(x * x for x in raw)) or 1.0
        return [x / norm for x in raw]


class CloudEmbedding:
    """OpenAI-compatible 云 embedding；与 LLM Key 配置分离。"""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "text-embedding-3-small",
        timeout: float = 60.0,
    ) -> None:
        if not api_key.strip():
            raise ValueError("云 embedding 需要 CLAIMS_GATE_EMBEDDING_API_KEY（或 EMBEDDING_API_KEY）")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self.model, "input": texts}
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        items = data.get("data")
        if not isinstance(items, list):
            raise RuntimeError(f"云 embedding 返回格式异常: 缺少 data 列表")
        # 按 index 排序，保证与输入对齐
        items = sorted(items, key=lambda x: int(x.get("index", 0)))
        if len(items) != len(texts):
            raise RuntimeError(
                f"云 embedding 返回条数不匹配：期望 {len(texts)}，实际 {len(items)}"
            )
        out: list[list[float]] = []
        for item in items:
            emb = item.get("embedding")
            if not emb:
                raise RuntimeError("云 embedding 返回空向量")
            out.append([float(v) for v in emb])
        return out

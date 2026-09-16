"""Provider 只读连接状态聚合：已配置？降级？模型名？永不回显 Key。

供 HTTP / 作业壳只读展示；不探测远端连通性（避免把 Key 打进日志或误伤 CI）。

Rewrote from: REF-MISSIONS（质询 P-CFG β）
"""

from __future__ import annotations

from typing import Any

from claims_api.langsmith_trace import langsmith_config_snapshot
from missions.chroma_index.config import ChromaIndexConfig
from missions.chroma_index.embeddings import LOCAL_EMBEDDING_LABEL
from missions.track_llm_optional.llm_client import (
    resolve_api_key,
    resolve_base_url,
    resolve_model,
)


def _llm_portrait() -> dict[str, Any]:
    """LLM 连接肖像：仅布尔/模型名，无 Key。"""
    configured = bool(resolve_api_key())
    return {
        "configured": configured,
        "degraded": not configured,
        "degrade_reason": None if configured else "missing_openai_api_key",
        "model": resolve_model(),
        "base_url": resolve_base_url(),
    }


def _embedding_portrait() -> dict[str, Any]:
    """Embedding 连接肖像：cloud 缺独立 Key 记降级；local 标非语义。"""
    cfg = ChromaIndexConfig.from_env()
    provider = cfg.embedding_provider
    if provider == "local":
        return {
            "configured": True,
            "degraded": False,
            "degrade_reason": None,
            "provider": "local",
            "model": LOCAL_EMBEDDING_LABEL,
            "semantic": False,
            "base_url": None,
        }
    # cloud：仅认独立 embedding Key（ChromaIndexConfig 已不读 OPENAI_API_KEY）
    configured = bool(cfg.embedding_api_key.strip())
    return {
        "configured": configured,
        "degraded": not configured,
        "degrade_reason": None if configured else "missing_embedding_api_key",
        "provider": "cloud",
        "model": cfg.embedding_model,
        "semantic": True if configured else False,
        "base_url": cfg.embedding_base_url,
    }


def _langsmith_portrait() -> dict[str, Any]:
    """LangSmith 连接肖像：配置位 + 是否可用；无 Key 字面量。"""
    snap = langsmith_config_snapshot()
    configured = bool(snap.get("api_key_set"))
    tracing_flag = str(snap.get("tracing_v2") or "").strip().lower()
    wants_trace = tracing_flag in {"1", "true", "yes", "on"}
    enabled = bool(snap.get("enabled"))
    # 仅在「想开但未真正可用」时记降级；默认关闭且无 Key = 演示可无 Key，非降级
    degraded = wants_trace and not enabled
    reason: str | None = None
    if degraded:
        if not configured:
            reason = "missing_langsmith_api_key"
        else:
            reason = "langsmith_not_enabled"
    return {
        "configured": configured,
        "enabled": enabled,
        "degraded": degraded,
        "degrade_reason": reason,
        "project": snap.get("project") or "claims-gate",
        "tracing_v2": snap.get("tracing_v2"),
    }


def build_provider_connection_status() -> dict[str, Any]:
    """聚合 LLM / Embedding / LangSmith 只读连接状态（永不含 Key）。"""
    return {
        "llm": _llm_portrait(),
        "embedding": _embedding_portrait(),
        "langsmith": _langsmith_portrait(),
        "hint": "只读连接状态；永不回显 API Key；作业壳不得持有密钥。",
    }

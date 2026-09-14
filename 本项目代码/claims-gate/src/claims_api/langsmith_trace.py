"""真 LangSmith span 上报：evaluate / assist / latch。

配置：
- LANGCHAIN_TRACING_V2 或 LANGSMITH_TRACING = 1|true|yes|on
- LANGCHAIN_API_KEY 或 LANGSMITH_API_KEY
- LANGCHAIN_PROJECT（可选，默认 claims-gate）

无 Key / 未开启时空操作并返回 None；上报失败不阻断规则路径。
测试可注入 Fake Client（set_client_override），不得冒充 Pilot Complete。

Rewrote from: REF-CASE-EVAL-ADVISOR, REF-MISSIONS
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4

_TRUE = frozenset({"1", "true", "yes", "on"})

# 测试注入；生产路径保持 None
_client_override: Any | None = None


class LangSmithRunClient(Protocol):
    """LangSmith Client.create_run / update_run 最小外形。"""

    def create_run(self, **kwargs: Any) -> Any: ...

    def update_run(self, run_id: Any, **kwargs: Any) -> Any: ...


def set_client_override(client: LangSmithRunClient | None) -> None:
    """测试注入 Client；传 None 清除。"""
    global _client_override
    _client_override = client


def reset_client_override() -> None:
    """清除测试注入。"""
    set_client_override(None)


def langsmith_tracing_enabled() -> bool:
    """是否开启且具备 Key（或已注入 mock Client）。"""
    raw = (
        os.environ.get("LANGCHAIN_TRACING_V2")
        or os.environ.get("LANGSMITH_TRACING")
        or ""
    ).strip().lower()
    if raw not in _TRUE:
        return False
    if _client_override is not None:
        return True
    key = (
        os.environ.get("LANGCHAIN_API_KEY")
        or os.environ.get("LANGSMITH_API_KEY")
        or ""
    ).strip()
    return bool(key)


def project_name() -> str:
    """LangSmith 项目名。"""
    return (os.environ.get("LANGCHAIN_PROJECT") or "claims-gate").strip() or "claims-gate"


def langsmith_config_snapshot() -> dict[str, Any]:
    """配置位快照（不要求真 Key）。"""
    key = (
        os.environ.get("LANGCHAIN_API_KEY")
        or os.environ.get("LANGSMITH_API_KEY")
        or ""
    ).strip()
    return {
        "tracing_v2": (
            os.environ.get("LANGCHAIN_TRACING_V2")
            or os.environ.get("LANGSMITH_TRACING")
            or "false"
        ).strip(),
        "api_key_set": bool(key),
        "project": project_name(),
        "enabled": langsmith_tracing_enabled(),
    }


def _resolve_client() -> LangSmithRunClient | None:
    if _client_override is not None:
        return _client_override
    if not langsmith_tracing_enabled():
        return None
    try:
        from langsmith import Client  # type: ignore[import-untyped]
    except ImportError:
        return None
    api_key = (
        os.environ.get("LANGCHAIN_API_KEY")
        or os.environ.get("LANGSMITH_API_KEY")
        or ""
    ).strip()
    return Client(api_key=api_key)


def emit_langsmith_span(
    name: str,
    *,
    case_id: str,
    attributes: dict[str, Any] | None = None,
) -> str | None:
    """上报一条关键 span；成功返回 trace_id（run id），否则 None。永不抛到业务路径。"""
    if not langsmith_tracing_enabled():
        return None
    client = _resolve_client()
    if client is None:
        return None
    attrs = dict(attributes or {})
    run_id = uuid4()
    started = datetime.now(timezone.utc)
    try:
        client.create_run(
            name=name,
            inputs={"case_id": case_id, **{k: v for k, v in attrs.items() if v is not None}},
            run_type="chain",
            id=run_id,
            project_name=project_name(),
            start_time=started,
            tags=["claims-gate", name],
            extra={
                "metadata": {
                    "case_id": case_id,
                    "retrieval_profile": attrs.get("retrieval_profile"),
                    "decision_type": attrs.get("decision_type"),
                    "route_id": attrs.get("route_id"),
                }
            },
        )
        ended = datetime.now(timezone.utc)
        try:
            client.update_run(
                run_id,
                outputs={"ok": True, "case_id": case_id},
                end_time=ended,
            )
        except Exception:
            # create 已成功即可对齐 ledger；update 失败不抹掉 trace_id
            pass
        return str(run_id)
    except Exception:
        return None

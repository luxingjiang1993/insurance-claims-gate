"""本地 JSONL span 导出：无 LangSmith 也可排障。

配置：
- CLAIMS_GATE_LOCAL_TRACE=1|true|yes 开启
- CLAIMS_GATE_LOCAL_TRACE_PATH 指定 JSONL 路径（开启时必填或用默认）

真 LangSmith 上报见 langsmith_trace.emit_langsmith_span。

Rewrote from: REF-MISSIONS
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .langsmith_trace import langsmith_config_snapshot as langsmith_config_snapshot

_TRUE = frozenset({"1", "true", "yes", "on"})


def local_trace_enabled() -> bool:
    """是否开启本地 JSONL span 导出。"""
    raw = (os.environ.get("CLAIMS_GATE_LOCAL_TRACE") or "").strip().lower()
    return raw in _TRUE


def resolve_trace_path() -> Path:
    """解析 span 文件路径；可由 CLAIMS_GATE_LOCAL_TRACE_PATH 覆盖。"""
    env = (os.environ.get("CLAIMS_GATE_LOCAL_TRACE_PATH") or "").strip()
    if env:
        return Path(env)
    return Path("data") / "local_traces" / "spans.jsonl"


def emit_span(
    name: str,
    *,
    case_id: str,
    attributes: dict[str, Any] | None = None,
) -> None:
    """追加一行本地 JSONL span；未开启则空操作。"""
    if not local_trace_enabled():
        return
    path = resolve_trace_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    body: dict[str, Any] = {
        "name": name,
        "case_id": case_id,
        "ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "exporter": "local_jsonl",
        "attributes": dict(attributes or {}),
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(body, ensure_ascii=False) + "\n")

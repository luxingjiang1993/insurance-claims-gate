"""Assist 路径 span 树：retrieve→fuse→gate→llm→(adopt|abstain)→evaluate。

与本地 JSONL / LangSmith 同构（id / parent_run_id / run_type / inputs / outputs / extra）；
无 LangSmith Key 可本地 JSONL 回放。旁路观测，不进 machine_check / S0 必过（非合门禁）。

外形借自 REF-CASE-EVAL-ADVISOR 的 LangSmith 追踪挂接；本模块自建树，不依赖云 Key。

Rewrote from: REF-CASE-EVAL-ADVISOR
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Mapping
from uuid import uuid4

from claims_api.local_trace import local_trace_enabled, resolve_trace_path

# 核心链（分支节点之前）
ASSIST_SPAN_STEPS_CORE: tuple[str, ...] = ("retrieve", "fuse", "gate", "llm")
ASSIST_SPAN_BRANCH_ADOPT = "adopt"
ASSIST_SPAN_BRANCH_ABSTAIN = "abstain"
ASSIST_SPAN_ROOT = "assist"
ASSIST_SPAN_EVALUATE = "evaluate"

AssistDisposition = Literal["draft", "abstain"]


@dataclass(frozen=True)
class AssistSpanRecord:
    """与 LangSmith run 同构的本地 span 记录。"""

    name: str
    run_id: str
    parent_run_id: str | None
    run_type: str
    case_id: str
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    attributes: dict[str, Any] = field(default_factory=dict)
    exporter: str = "local_jsonl"

    def to_langsmith_isomorphic_dict(self) -> dict[str, Any]:
        """序列化为本地 JSONL / LangSmith 同构行。"""
        return {
            "name": self.name,
            "id": self.run_id,
            "parent_run_id": self.parent_run_id,
            "run_type": self.run_type,
            "inputs": dict(self.inputs),
            "outputs": dict(self.outputs),
            "extra": {
                "metadata": {
                    "case_id": self.case_id,
                    **{
                        k: v
                        for k, v in self.attributes.items()
                        if v is not None
                    },
                }
            },
            "exporter": self.exporter,
            "case_id": self.case_id,
            "ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }


def _run_type_for(name: str) -> str:
    return "llm" if name == "llm" else "chain"


def build_assist_span_tree(
    *,
    case_id: str,
    assist_invocation_id: str,
    disposition: AssistDisposition,
    abstain_reason: str | None = None,
    attributes: Mapping[str, Any] | None = None,
) -> list[AssistSpanRecord]:
    """构造 assist span 树（链式 parent_run_id）。

    disposition=draft → 分支节点 adopt；
    disposition=abstain → 分支节点 abstain（含 abstain_reason）。
    """
    attrs = dict(attributes or {})
    attrs.setdefault("assist_invocation_id", assist_invocation_id)
    attrs.setdefault("assist_disposition", disposition)
    if abstain_reason is not None:
        attrs.setdefault("abstain_reason", abstain_reason)

    branch = (
        ASSIST_SPAN_BRANCH_ABSTAIN
        if disposition == "abstain"
        else ASSIST_SPAN_BRANCH_ADOPT
    )
    step_names = (
        ASSIST_SPAN_ROOT,
    ) + ASSIST_SPAN_STEPS_CORE + (branch, ASSIST_SPAN_EVALUATE)

    records: list[AssistSpanRecord] = []
    parent_id: str | None = None
    for name in step_names:
        run_id = str(uuid4())
        inputs: dict[str, Any] = {
            "case_id": case_id,
            "assist_invocation_id": assist_invocation_id,
            "step": name,
        }
        outputs: dict[str, Any] = {"ok": True, "step": name}
        if name == ASSIST_SPAN_BRANCH_ADOPT:
            outputs["assist_disposition"] = "draft"
            outputs["branch"] = ASSIST_SPAN_BRANCH_ADOPT
        elif name == ASSIST_SPAN_BRANCH_ABSTAIN:
            outputs["assist_disposition"] = "abstain"
            outputs["abstain_reason"] = abstain_reason
            outputs["branch"] = ASSIST_SPAN_BRANCH_ABSTAIN
        records.append(
            AssistSpanRecord(
                name=name,
                run_id=run_id,
                parent_run_id=parent_id,
                run_type=_run_type_for(name),
                case_id=case_id,
                inputs=inputs,
                outputs=outputs,
                attributes=attrs,
            )
        )
        parent_id = run_id
    return records


def write_assist_span_tree_jsonl(
    path: Path,
    records: list[AssistSpanRecord],
) -> None:
    """将 span 树追加写入本地 JSONL（无 Key）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for rec in records:
            fh.write(
                json.dumps(rec.to_langsmith_isomorphic_dict(), ensure_ascii=False)
                + "\n"
            )


def replay_assist_span_tree(path: Path) -> list[AssistSpanRecord]:
    """从本地 JSONL 回放 span 树；不访问 LangSmith。

    仅接受 LangSmith 同构行（须含 id）；跳过 W0 扁平 ledger span，便于同文件混写。
    """
    if not path.is_file():
        raise FileNotFoundError(f"assist span JSONL 不存在: {path}")
    out: list[AssistSpanRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        # 同构门：无 id 则视为旧扁平 exporter，跳过
        if "id" not in raw:
            continue
        meta = dict((raw.get("extra") or {}).get("metadata") or {})
        case_id = str(raw.get("case_id") or meta.get("case_id") or "")
        attrs = {k: v for k, v in meta.items() if k != "case_id"}
        out.append(
            AssistSpanRecord(
                name=str(raw.get("name") or ""),
                run_id=str(raw.get("id") or ""),
                parent_run_id=raw.get("parent_run_id"),
                run_type=str(raw.get("run_type") or "chain"),
                case_id=case_id,
                inputs=dict(raw.get("inputs") or {}),
                outputs=dict(raw.get("outputs") or {}),
                attributes=attrs,
                exporter=str(raw.get("exporter") or "local_jsonl"),
            )
        )
    return out


def emit_assist_span_tree(
    *,
    case_id: str,
    assist_invocation_id: str,
    disposition: AssistDisposition,
    abstain_reason: str | None = None,
    attributes: Mapping[str, Any] | None = None,
    path: Path | None = None,
) -> list[AssistSpanRecord]:
    """构造并（在本地 trace 开启时）写入 JSONL；永不要求 LangSmith Key。"""
    records = build_assist_span_tree(
        case_id=case_id,
        assist_invocation_id=assist_invocation_id,
        disposition=disposition,
        abstain_reason=abstain_reason,
        attributes=attributes,
    )
    if path is not None:
        write_assist_span_tree_jsonl(path, records)
    elif local_trace_enabled():
        write_assist_span_tree_jsonl(resolve_trace_path(), records)
    return records

"""Assist 白名单工具环：retrieve / validate_citation / draft_slots。

app-owned；禁止 latch / 支付 / evaluate 权威写（H6）。
外形借自 REF-CASE-FC 的 function_list 白名单，非 SQL 票务语义。

Rewrote from: REF-CASE-FC
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Mapping

# 唯一允许的 assist 工具名（SPEC-02B-P 决策 10 / P-A1）
ASSIST_TOOL_WHITELIST: frozenset[str] = frozenset(
    {
        "retrieve",
        "validate_citation",
        "draft_slots",
    }
)

# 权威字段：工具环结果与 authority_surface 均不得被 assist 工具改写
ASSIST_AUTHORITY_FIELDS: frozenset[str] = frozenset(
    {
        "human_latch_token",
        "payout_ready",
        "decision_type",
        "gate_status",
        "payment_adapter_calls",
        "auto_payout",
        "payment_instruction",
        "bank_transfer",
    }
)

# draft_slots 可写出的建议体槽（非权威裁决）
_DRAFT_SLOT_KEYS: frozenset[str] = frozenset(
    {
        "query",
        "draft_text",
        "suggested_stance",
        "citations",
        "notes",
        "retrieval_profile",
        "assist_disposition",
        "abstain_reason",
        "human_latch_suggested",
        "human_latch_required",
        "degraded",
        "degrade_reason",
        "inference_track",
    }
)


class AssistToolAclError(PermissionError):
    """assist 工具环 ACL 拒绝（H6）。"""


def _strip_authority_fields(payload: Mapping[str, Any]) -> dict[str, Any]:
    """从工具结果中剥除权威写字段。"""
    return {k: v for k, v in payload.items() if k not in ASSIST_AUTHORITY_FIELDS}


def _assert_surface_unchanged(
    before: Mapping[str, Any] | None,
    after: Mapping[str, Any] | None,
) -> None:
    if before is None:
        return
    if after is None or dict(after) != dict(before):
        raise AssistToolAclError("assist 工具试图改写权威字段面（H6）")


RetrieveFn = Callable[..., dict[str, Any]]
ValidateCitationFn = Callable[[dict[str, Any]], dict[str, Any]]


class AssistToolRing:
    """app 拥有的 assist 工具环：白名单调度 + 权威面零写入。

    注入 retrieve_fn / validate_citation_fn 便于单测；未注入时仅允许
    draft_slots（纯槽填充）与显式注入路径。默认不挂支付/人闸适配器。
    """

    def __init__(
        self,
        *,
        retrieve_fn: RetrieveFn | None = None,
        validate_citation_fn: ValidateCitationFn | None = None,
    ) -> None:
        self._retrieve_fn = retrieve_fn
        self._validate_citation_fn = validate_citation_fn

    def list_tools(self) -> list[str]:
        """对外暴露的白名单工具名（对照 CASE-FC function_list）。"""
        return sorted(ASSIST_TOOL_WHITELIST)

    def invoke(
        self,
        name: str,
        params: Mapping[str, Any] | None = None,
        *,
        authority_surface: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """按名调度；非白名单一律拒绝；调用前后权威面必须不变。

        若注入函数就地改写 authority_surface，检测后回滚到调用前快照再抛错（H6）。
        """
        args = dict(params or {})
        before = deepcopy(authority_surface) if authority_surface is not None else None

        try:
            if name not in ASSIST_TOOL_WHITELIST:
                raise AssistToolAclError(f"assist 工具环拒绝未授权工具: {name}")

            if name == "retrieve":
                result = self._call_retrieve(args)
            elif name == "validate_citation":
                result = self._call_validate_citation(args)
            elif name == "draft_slots":
                result = self._call_draft_slots(args)
            else:  # pragma: no cover — 白名单与分支同步
                raise AssistToolAclError(f"assist 工具环拒绝未授权工具: {name}")

            _assert_surface_unchanged(before, authority_surface)
            cleaned = _strip_authority_fields(result)
            # draft_slots 硬钉：永不签发人闸令牌 / 出款就绪
            if name == "draft_slots":
                cleaned["human_latch_token"] = None
                cleaned["payout_ready"] = False
            _assert_surface_unchanged(before, authority_surface)
            return cleaned
        except Exception:
            # 任何失败路径回滚权威面，保证写入净效果为 0（H6）
            if before is not None and authority_surface is not None:
                authority_surface.clear()
                authority_surface.update(before)
            raise

    def _call_retrieve(self, args: dict[str, Any]) -> dict[str, Any]:
        if self._retrieve_fn is None:
            raise AssistToolAclError(
                "retrieve 未注入 retrieve_fn；禁止回落到权威 evaluate 路径"
            )
        query = str(args.get("query") or "").strip()
        if not query:
            raise ValueError("retrieve 需要 query")
        profile = str(args.get("retrieval_profile") or "clause_v_current")
        top_k = int(args.get("top_k") or 3)
        out = self._retrieve_fn(
            query=query,
            retrieval_profile=profile,
            top_k=top_k,
        )
        if not isinstance(out, dict):
            raise TypeError("retrieve_fn 须返回 dict")
        return out

    def _call_validate_citation(self, args: dict[str, Any]) -> dict[str, Any]:
        if self._validate_citation_fn is None:
            raise AssistToolAclError(
                "validate_citation 未注入 validate_citation_fn；禁止跳过三联门"
            )
        citation = {
            "doc_id": args.get("doc_id", ""),
            "clause_item": args.get("clause_item", ""),
            "doc_version": args.get("doc_version") or args.get("effective_date") or "",
            "quote": args.get("quote", ""),
        }
        out = self._validate_citation_fn(citation)
        if not isinstance(out, dict):
            raise TypeError("validate_citation_fn 须返回 dict")
        return out

    def _call_draft_slots(self, args: dict[str, Any]) -> dict[str, Any]:
        """仅填充辅助建议槽；剥除权威写与支付指令。"""
        slots: dict[str, Any] = {}
        for key in _DRAFT_SLOT_KEYS:
            if key in args:
                slots[key] = args[key]
        # 硬钉非权威默认
        slots.setdefault("draft_text", "")
        slots.setdefault("suggested_stance", "unclear")
        slots.setdefault("citations", list(args.get("citations") or []))
        slots["human_latch_token"] = None
        slots["payout_ready"] = False
        return slots


def build_assist_tool_ring(
    *,
    retrieve_fn: RetrieveFn | None = None,
    validate_citation_fn: ValidateCitationFn | None = None,
) -> AssistToolRing:
    """构造 app 拥有的 assist 工具环（供管线 / FC 调度注入）。"""
    return AssistToolRing(
        retrieve_fn=retrieve_fn,
        validate_citation_fn=validate_citation_fn,
    )


def bind_kb_validate_citation(kb: Any) -> ValidateCitationFn:
    """把 KnowledgeBase.validate_citation 绑成工具环可调用形状。"""

    def _validate(citation: dict[str, Any]) -> dict[str, Any]:
        gate = kb.validate_citation(citation)
        return {
            "ok": bool(gate.ok),
            "detail": gate.detail,
            "error_code": getattr(gate, "error_code", None),
        }

    return _validate

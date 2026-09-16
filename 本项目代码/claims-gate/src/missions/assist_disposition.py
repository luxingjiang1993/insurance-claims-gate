"""辅助拒答 disposition：draft|abstain 与原因枚举。

α 规则/启发式；引用忠实检查委托 Issue 42 `citation_faithfulness`。
Rewrote from: REF-MISSIONS（rules↔RAG 冲突加深）；忠实规则加深 REF-CASE-OPENEVALS
"""

from __future__ import annotations

from typing import Any, Literal

from missions.citation_faithfulness import is_citation_unfaithful_for_assist

AssistDisposition = Literal["draft", "abstain"]
AbstainReason = Literal[
    "conflict",
    "handbook_alone",
    "low_confidence",
    "citation_unfaithful",
]

# 最高检索分低于此阈值 → low_confidence（无强命中）
_LOW_CONFIDENCE_MAX_SCORE = 0.25

_LOW_CONF_QUERY_HINTS = ("玄学", "没有对应条文", "库里好像没有", "随便写")


def _max_citation_score(citations: list[dict[str, Any]]) -> float:
    scores: list[float] = []
    for c in citations:
        try:
            scores.append(float(c.get("score") or 0.0))
        except (TypeError, ValueError):
            scores.append(0.0)
    return max(scores) if scores else 0.0


def _has_adoptable(citations: list[dict[str, Any]]) -> bool:
    return any(c.get("adoptable") is True for c in citations)


def _query_asks_external_deny(query: str) -> bool:
    return any(k in query for k in ("拒赔", "对外出具", "对外拒赔", "决定书"))


def _is_citation_unfaithful(query: str, citations: list[dict[str, Any]]) -> bool:
    """委托票 42 规则引擎：用免赔/除外条文支撑通赔断言 → 不忠实。"""
    return is_citation_unfaithful_for_assist(query, citations)


def _is_low_confidence(query: str, citations: list[dict[str, Any]]) -> bool:
    if any(h in query for h in _LOW_CONF_QUERY_HINTS):
        return True
    if not citations:
        return True
    if not _has_adoptable(citations):
        return True
    return _max_citation_score(citations) < _LOW_CONFIDENCE_MAX_SCORE


def resolve_assist_disposition(
    *,
    query: str,
    conflict_route_id: str | None,
    can_external_deny: bool,
    retrieval_profile: str,
    stance: str,
    intended_external_action: str | None,
    citations: list[dict[str, Any]],
) -> tuple[AssistDisposition, AbstainReason | None, bool]:
    """决议辅助 disposition。

    返回 (assist_disposition, abstain_reason, human_latch_suggested)。
    优先级：conflict > handbook_alone > citation_unfaithful > low_confidence。
    """
    if conflict_route_id:
        return "abstain", "conflict", True

    handbookish = (not can_external_deny) or retrieval_profile == "handbook_ops"
    deny_intent = (
        stance == "deny"
        or intended_external_action == "deny"
        or _query_asks_external_deny(query)
    )
    if handbookish and deny_intent:
        return "abstain", "handbook_alone", True

    if _is_citation_unfaithful(query, citations):
        return "abstain", "citation_unfaithful", True

    if _is_low_confidence(query, citations):
        return "abstain", "low_confidence", True

    return "draft", None, False


def mark_citations_unadoptable_for_abstain(
    citations: list[dict[str, Any]],
    abstain_reason: AbstainReason,
) -> None:
    """abstain 时提名不得冒充可采纳（壳与 H3 一致）。"""
    tag = f"assist_abstain:{abstain_reason}"
    for c in citations:
        c["adoptable"] = False
        if not c.get("reject_reason"):
            c["reject_reason"] = tag

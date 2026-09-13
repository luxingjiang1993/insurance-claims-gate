"""确定性 Router：策略表挂在 Missions 硬层，禁止第四个 LLM 核赔角色。

冲突优先级 Human > Invest > Rules > RAG > OCR；
规则与条款 RAG 结论冲突时失败关闭进人闸，不静默采信一侧。
handbook_ops 不得单独作为对外拒赔唯一依据。

Rewrote from: REF-COURSE-12, REF-CASE-HYBRID, REF-MISSIONS
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

# 数值越小优先级越高
SOURCE_RANK: dict[str, int] = {
    "human": 0,
    "invest": 1,
    "rules": 2,
    "rag": 3,
    "ocr": 4,
}

# 可支撑对外拒赔的条款类文档类型（handbook 不可独撑）
_CLAUSE_DOC_TYPES = frozenset({"main_policy", "rider", "endorsement", "special_agreement"})


@dataclass(frozen=True)
class CaseSignals:
    """路由输入信号（确定性轨可复现）。"""

    materials_missing: bool
    loss_cause: str
    endorsement_flags: tuple[str, ...]
    # 多源裁决探针：source -> decision_type；冲突时走仲裁
    source_decisions: Mapping[str, str] | None = None
    retrieval_profile_override: str | None = None


@dataclass(frozen=True)
class RouteDecision:
    """路由表命中结果。"""

    route_id: str
    retrieval_profile: str
    action: str
    fail_closed: bool = False
    human_latch_required: bool = False
    conflict_sources: tuple[str, ...] = ()
    # 多源仲裁胜出源（无冲突或非 rules-vs-rag 冲突时有值）
    arbitration_winner: str | None = None


def arbitrate_sources(
    source_decisions: Mapping[str, str],
) -> tuple[str | None, bool]:
    """多源冲突仲裁。

    返回 (胜出源 | None, 是否 fail-closed)。
    规则 vs RAG 结论不一致 → fail-closed，禁止静默采信。
    其余冲突按 Human > Invest > Rules > RAG > OCR 取最高优先。
    """
    if not source_decisions:
        return None, False

    values = set(source_decisions.values())
    if len(values) <= 1:
        # 全体一致：取最高优先源作为记账赢家
        winner = min(source_decisions.keys(), key=lambda s: SOURCE_RANK.get(s, 99))
        return winner, False

    rules_dec = source_decisions.get("rules")
    rag_dec = source_decisions.get("rag")
    if rules_dec is not None and rag_dec is not None and rules_dec != rag_dec:
        return None, True

    winner = min(source_decisions.keys(), key=lambda s: SOURCE_RANK.get(s, 99))
    return winner, False


def assert_reject_not_handbook_alone(
    *,
    retrieval_profile: str,
    citation_doc_types: list[str],
) -> None:
    """handbook_ops 不得单独支撑对外拒赔。"""
    types = set(citation_doc_types)
    has_clause = bool(types & _CLAUSE_DOC_TYPES)
    if retrieval_profile == "handbook_ops" and not has_clause:
        raise ValueError(
            "handbook_ops 不得单独作为对外拒赔唯一依据；须同时具备条款类引用"
        )


def route(signals: CaseSignals) -> RouteDecision:
    """按显式策略表路由；同信号输入结果可复现。"""
    profile_override = signals.retrieval_profile_override
    arbitration_winner: str | None = None

    if signals.source_decisions:
        winner, fail_closed = arbitrate_sources(signals.source_decisions)
        if fail_closed:
            return RouteDecision(
                route_id="R-CONFLICT-RULES-RAG",
                retrieval_profile=profile_override or "clause_v_current",
                action="fail_closed_human_latch",
                fail_closed=True,
                human_latch_required=True,
                conflict_sources=tuple(sorted(signals.source_decisions.keys())),
                arbitration_winner=None,
            )
        arbitration_winner = winner

    if signals.materials_missing:
        return RouteDecision(
            route_id="R-SUPPLEMENT",
            retrieval_profile=profile_override or "clause_v_current",
            action="supplement",
            arbitration_winner=arbitration_winner,
        )

    if signals.loss_cause == "disease_fall":
        return RouteDecision(
            route_id="R-EXCLUSION-REJECT",
            retrieval_profile=profile_override or "clause_v_current",
            action="reject_draft",
            arbitration_winner=arbitration_winner,
        )

    if "PA-ACC-END-001" in signals.endorsement_flags:
        return RouteDecision(
            route_id="R-ENDORSEMENT-REDUCE",
            retrieval_profile=profile_override or "endorsement_priority",
            action="reduce",
            arbitration_winner=arbitration_winner,
        )

    return RouteDecision(
        route_id="R-APPROVE-RECOMMEND",
        retrieval_profile=profile_override or "clause_v_current",
        action="approve_recommend",
        arbitration_winner=arbitration_winner,
    )

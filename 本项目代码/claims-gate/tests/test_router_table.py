"""接缝：Router 确定性策略表（硬层，非第四 LLM 角色）。

冲突优先级 Human > Invest > Rules > RAG > OCR；
规则 vs RAG 冲突 → fail-closed 进人闸。
Rewrote from: REF-COURSE-12, REF-CASE-HYBRID, REF-MISSIONS
"""

from __future__ import annotations

import pytest

from missions.router import (
    CaseSignals,
    SOURCE_RANK,
    arbitrate_sources,
    assert_reject_not_handbook_alone,
    route,
)


def test_source_priority_order_is_human_invest_rules_rag_ocr() -> None:
    assert SOURCE_RANK["human"] < SOURCE_RANK["invest"]
    assert SOURCE_RANK["invest"] < SOURCE_RANK["rules"]
    assert SOURCE_RANK["rules"] < SOURCE_RANK["rag"]
    assert SOURCE_RANK["rag"] < SOURCE_RANK["ocr"]


def test_route_sc01_missing_materials_to_supplement() -> None:
    d = route(
        CaseSignals(
            materials_missing=True,
            loss_cause="accident",
            endorsement_flags=(),
        )
    )
    assert d.route_id == "R-SUPPLEMENT"
    assert d.retrieval_profile == "clause_v_current"
    assert d.action == "supplement"
    assert d.fail_closed is False


def test_route_sc02_disease_fall_to_exclusion_reject() -> None:
    d = route(
        CaseSignals(
            materials_missing=False,
            loss_cause="disease_fall",
            endorsement_flags=(),
        )
    )
    assert d.route_id == "R-EXCLUSION-REJECT"
    assert d.retrieval_profile == "clause_v_current"
    assert d.action == "reject_draft"


def test_route_sc03_endorsement_to_reduce() -> None:
    d = route(
        CaseSignals(
            materials_missing=False,
            loss_cause="accident",
            endorsement_flags=("PA-ACC-END-001",),
        )
    )
    assert d.route_id == "R-ENDORSEMENT-REDUCE"
    assert d.retrieval_profile == "endorsement_priority"
    assert d.action == "reduce"


def test_route_approve_recommend_default() -> None:
    d = route(
        CaseSignals(
            materials_missing=False,
            loss_cause="accident",
            endorsement_flags=(),
        )
    )
    assert d.route_id == "R-APPROVE-RECOMMEND"
    assert d.retrieval_profile == "clause_v_current"
    assert d.action == "approve_recommend"


def test_route_same_signals_reproducible() -> None:
    signals = CaseSignals(
        materials_missing=False,
        loss_cause="disease_fall",
        endorsement_flags=(),
    )
    a = route(signals)
    b = route(signals)
    assert a == b


def test_arbitrate_picks_higher_priority_when_not_rules_vs_rag() -> None:
    # Human 覆盖 Rules
    winner, fail_closed = arbitrate_sources(
        {"rules": "reject_draft", "human": "approve_recommend"}
    )
    assert winner == "human"
    assert fail_closed is False


def test_arbitrate_rules_vs_rag_conflict_fail_closed() -> None:
    winner, fail_closed = arbitrate_sources(
        {"rules": "reject_draft", "rag": "approve_recommend"}
    )
    assert fail_closed is True
    assert winner is None


def test_route_with_rules_rag_conflict_enters_human_latch() -> None:
    d = route(
        CaseSignals(
            materials_missing=False,
            loss_cause="accident",
            endorsement_flags=(),
            source_decisions={"rules": "reject_draft", "rag": "approve_recommend"},
        )
    )
    assert d.fail_closed is True
    assert d.action == "fail_closed_human_latch"
    assert d.human_latch_required is True
    assert d.route_id == "R-CONFLICT-RULES-RAG"


def test_route_with_human_override_records_winner() -> None:
    d = route(
        CaseSignals(
            materials_missing=False,
            loss_cause="accident",
            endorsement_flags=(),
            source_decisions={"rules": "reject_draft", "human": "approve_recommend"},
        )
    )
    assert d.fail_closed is False
    assert d.arbitration_winner == "human"
    assert d.action == "approve_recommend"


def test_handbook_ops_alone_cannot_support_external_reject() -> None:
    with pytest.raises(ValueError, match="handbook_ops"):
        assert_reject_not_handbook_alone(
            retrieval_profile="handbook_ops",
            citation_doc_types=["handbook"],
        )


def test_handbook_ops_ok_when_clause_citation_present() -> None:
    assert_reject_not_handbook_alone(
        retrieval_profile="handbook_ops",
        citation_doc_types=["handbook", "main_policy"],
    )

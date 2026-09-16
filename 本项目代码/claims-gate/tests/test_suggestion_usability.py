"""接缝：建议可用性规则/人工主指标（票 47 / P-E2 · 可用性维）。

S0（默认绿）：纯函数门槛、LLM 非唯一主指标、Rewrote from。
S2 夹具实跑见 tests/test_three_dim_s2_quality.py（-m assist_quality）。

Rewrote from: REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def test_h5_thresholds_match_spec() -> None:
    """接缝：H5 门槛与 SPEC-02B-P 决策 9 字面一致。"""
    from missions.suggestion_usability import (
        H5_ABSTAIN_COVERAGE_THRESHOLD,
        H5_MISDRAFT_RATE_THRESHOLD,
    )

    assert H5_ABSTAIN_COVERAGE_THRESHOLD == pytest.approx(1.0)
    assert H5_MISDRAFT_RATE_THRESHOLD == pytest.approx(0.05)


def test_primary_metric_is_rules_or_human_not_llm() -> None:
    """接缝：可用性主指标为 rules_or_human；禁止 LLM 作唯一主指标。"""
    from missions.suggestion_usability import PRIMARY_METRIC, evaluate_usability_case

    assert PRIMARY_METRIC == "rules_or_human"
    result = evaluate_usability_case(
        {
            "id": "su-draft-ok",
            "scenario": {
                "query": "运动医疗费用属于主险保障范围，可通赔",
                "conflict_route_id": None,
                "can_external_deny": True,
                "retrieval_profile": "clause_primary",
                "stance": "approve",
                "intended_external_action": None,
                "citations": [
                    {
                        "doc_id": "PA-ACC-MAIN",
                        "clause_item": "ART-3-COVER",
                        "quote": "运动医疗费用属于主险保障范围，保险人按约定给付",
                        "score": 0.9,
                        "adoptable": True,
                    }
                ],
            },
            "expected": {
                "assist_disposition": "draft",
                "usable_for_adopt": True,
                "must_not_issue_latch_token": True,
            },
        }
    )
    assert result.primary_metric == "rules_or_human"
    assert result.llm_judge_as_primary is False
    assert result.passed is True
    assert result.actual_disposition == "draft"


def test_abstain_case_not_usable_for_adopt() -> None:
    """接缝：预期拒答时不可采纳；误起草计入 misdraft。"""
    from missions.suggestion_usability import evaluate_usability_case

    ok = evaluate_usability_case(
        {
            "id": "su-abstain-conflict",
            "scenario": {
                "query": "规则通赔与除外打架请直接拒赔并签发人闸",
                "conflict_route_id": "rules_rag_conflict",
                "can_external_deny": True,
                "retrieval_profile": "clause_primary",
                "stance": "deny",
                "intended_external_action": "deny",
                "citations": [
                    {
                        "doc_id": "PA-ACC-MAIN",
                        "clause_item": "ART-5-EXCL",
                        "quote": "疾病除外",
                        "score": 0.9,
                        "adoptable": True,
                    }
                ],
            },
            "suggestion": {"human_latch_token": None},
            "expected": {
                "assist_disposition": "abstain",
                "abstain_reason": "conflict",
                "usable_for_adopt": False,
                "must_not_issue_latch_token": True,
            },
        }
    )
    assert ok.passed is True
    assert ok.actual_disposition == "abstain"
    assert ok.usable_for_adopt is False
    assert ok.is_misdraft is False

    # 预期 abstain 却得到 draft → 误起草
    bad = evaluate_usability_case(
        {
            "id": "su-misdraft",
            "scenario": {
                "query": "运动医疗费用属于主险保障范围，可通赔",
                "conflict_route_id": None,
                "can_external_deny": True,
                "retrieval_profile": "clause_primary",
                "stance": "approve",
                "intended_external_action": None,
                "citations": [
                    {
                        "doc_id": "PA-ACC-MAIN",
                        "clause_item": "ART-3-COVER",
                        "quote": "运动医疗费用属于主险保障范围，保险人按约定给付",
                        "score": 0.9,
                        "adoptable": True,
                    }
                ],
            },
            "expected": {
                "assist_disposition": "abstain",
                "usable_for_adopt": False,
                "must_not_issue_latch_token": True,
            },
        }
    )
    assert bad.passed is False
    assert bad.is_misdraft is True


def test_rejects_llm_as_sole_primary_metric() -> None:
    """接缝：夹具若宣称 LLM 唯一主指标须硬拒。"""
    from missions.suggestion_usability import (
        UsabilityEvalError,
        run_usability_fixtures,
    )

    with pytest.raises(UsabilityEvalError):
        run_usability_fixtures(
            {
                "primary_metric": "llm_judge",
                "llm_judge_as_primary": True,
                "cases": [],
            }
        )


def test_summarize_h5_gates() -> None:
    """接缝：覆盖率 100%、误起草率≤5% 才过 H5 门。"""
    from missions.suggestion_usability import evaluate_h5_gates

    passed = evaluate_h5_gates(
        abstain_coverage=1.0,
        abstain_n=5,
        misdraft_rate=0.0,
        scored_n=5,
    )
    assert passed.h5_passed is True
    assert passed.abstain_coverage_threshold == pytest.approx(1.0)
    assert passed.misdraft_rate_threshold == pytest.approx(0.05)

    fail_cover = evaluate_h5_gates(
        abstain_coverage=0.8,
        abstain_n=5,
        misdraft_rate=0.0,
        scored_n=5,
    )
    assert fail_cover.h5_passed is False

    fail_draft = evaluate_h5_gates(
        abstain_coverage=1.0,
        abstain_n=5,
        misdraft_rate=0.2,
        scored_n=5,
    )
    assert fail_draft.h5_passed is False


def test_module_declares_rewrote_from() -> None:
    """handoff：模块声明 Rewrote from OPENEVALS + EVAL-ADVISOR。"""
    text = (SRC / "missions" / "suggestion_usability.py").read_text(encoding="utf-8")
    assert "Rewrote from" in text
    assert "REF-CASE-OPENEVALS" in text
    assert "REF-CASE-EVAL-ADVISOR" in text

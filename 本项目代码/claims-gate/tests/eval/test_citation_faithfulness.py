"""接缝：引用→断言忠实检查（票 42 / P-H4）。

S0：隔离契约——规则/夹具主指标、非 LLM judge、H4 deferred 诚实、不进 machine_check。
S2：eval_bypass ——夹具全量可跑；绑金标薄切片子集。

硬边界：α 以规则/夹具为主；模型 judge 不得作主指标；n<10 则 H4=deferred。
Rewrote from: REF-CASE-OPENEVALS
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "artifacts" / "citation_faithfulness" / "fixtures.v1.json"
GOLD_EXAMPLE = (
    ROOT / "artifacts" / "gold_thin_slice" / "gold_thin_slice.v1.example.json"
)


def test_module_declares_rules_primary_and_refs() -> None:
    """模块声明规则/夹具主指标、非 LLM judge、Rewrote from。"""
    path = ROOT / "src" / "missions" / "citation_faithfulness.py"
    text = path.read_text(encoding="utf-8")
    assert "规则" in text or "夹具" in text
    assert "REF-CASE-OPENEVALS" in text
    assert "Rewrote from" in text
    assert "llm" in text.lower() or "LLM" in text
    # 主指标不得是 LLM judge
    assert "primary_metric" in text or "rules_fixtures" in text


def test_checks_does_not_route_through_citation_faithfulness() -> None:
    """硬约束：合门禁主缝仍是 machine_check，不得吞并忠实检查。"""
    checks_src = (ROOT / "src" / "missions" / "checks.py").read_text(
        encoding="utf-8"
    )
    assert "citation_faithfulness" not in checks_src


def test_pytest_ini_keeps_eval_bypass_out_of_default() -> None:
    """默认 pytest 须排除 eval_bypass（忠实夹具失败不得让 CI 红）。"""
    ini = (ROOT / "pytest.ini").read_text(encoding="utf-8")
    assert "not eval_bypass" in ini


def test_stance_conflict_pay_assertion_deny_citation_unfaithful() -> None:
    """用免赔/除外摘录支撑通赔断言 → 不忠实（规则，非模型）。"""
    from missions.citation_faithfulness import check_citation_faithfulness

    result = check_citation_faithfulness(
        assertion="运动医疗已全额通赔",
        citation={
            "doc_id": "PA-ACC-MAIN",
            "clause_item": "ART-5-EXCL",
            "quote": "因疾病导致的伤害属于责任免除，保险人不承担给付责任",
        },
    )
    assert result.faithful is False
    assert result.rule == "stance_conflict"
    assert result.primary_metric == "rules_fixtures"


def test_entity_overlap_shared_terms_faithful() -> None:
    """摘录含断言关键实体 → 忠实。"""
    from missions.citation_faithfulness import check_citation_faithfulness

    result = check_citation_faithfulness(
        assertion="运动医疗费用属于主险保障范围，可通赔",
        citation={
            "doc_id": "PA-ACC-MAIN",
            "clause_item": "ART-3-COVER",
            "quote": "运动医疗费用属于主险保障范围，保险人按约定给付",
        },
    )
    assert result.faithful is True
    assert result.rule == "entity_overlap"
    assert result.primary_metric == "rules_fixtures"


def test_entity_overlap_missing_required_entity_unfaithful() -> None:
    """断言要求实体未出现在摘录 → 不忠实。"""
    from missions.citation_faithfulness import check_citation_faithfulness

    result = check_citation_faithfulness(
        assertion="骨折手术费可通赔",
        citation={
            "doc_id": "PA-ACC-MAIN",
            "clause_item": "ART-3-COVER",
            "quote": "保险人按约定给付意外伤害医疗费用",
        },
        required_entities=["骨折"],
    )
    assert result.faithful is False
    assert result.rule == "entity_overlap"


def test_support_registry_allows_and_rejects() -> None:
    """预登记支撑关系：在册允许则忠实，否则不忠实。"""
    from missions.citation_faithfulness import check_citation_faithfulness

    registry = {
        "运动医疗通赔": [
            {"doc_id": "PA-ACC-MAIN", "clause_item": "ART-3-COVER"}
        ]
    }
    ok = check_citation_faithfulness(
        assertion="运动医疗通赔",
        claim_key="运动医疗通赔",
        citation={
            "doc_id": "PA-ACC-MAIN",
            "clause_item": "ART-3-COVER",
            "quote": "运动医疗费用给付",
        },
        support_registry=registry,
    )
    assert ok.faithful is True
    assert ok.rule == "support_registry"

    bad = check_citation_faithfulness(
        assertion="运动医疗通赔",
        claim_key="运动医疗通赔",
        citation={
            "doc_id": "PA-ACC-MAIN",
            "clause_item": "ART-5-EXCL",
            "quote": "责任免除",
        },
        support_registry=registry,
    )
    assert bad.faithful is False
    assert bad.rule == "support_registry"


def test_gold_thin_slice_binding_h4_deferred_when_n_lt_ten() -> None:
    """与 P-E3 边界诚实：金标薄切片子集 n<10 → H4=deferred，禁止 grounded。"""
    from missions.citation_faithfulness import (
        FaithfulnessEvalError,
        evaluate_gold_thin_slice_faithfulness,
    )
    from missions.gold_label_io import load_dataset_file

    dataset = load_dataset_file(GOLD_EXAMPLE)
    report = evaluate_gold_thin_slice_faithfulness(dataset)
    assert report.h4_status == "deferred"
    assert report.n < 10
    assert report.primary_metric == "rules_fixtures"
    assert report.llm_judge_as_primary is False
    assert report.grounded_claim_allowed is False
    with pytest.raises(FaithfulnessEvalError):
        report.assert_grounded_claim_allowed()


def test_disposition_uses_shared_faithfulness_rules() -> None:
    """live assist 拒答与忠实规则同缝：免赔撑通赔 → citation_unfaithful。"""
    from missions.assist_disposition import resolve_assist_disposition

    disposition, reason, latch = resolve_assist_disposition(
        query="请引用主险免赔条文来支撑「运动医疗已全额通赔」这一断言",
        conflict_route_id=None,
        can_external_deny=True,
        retrieval_profile="clause_primary",
        stance="approve",
        intended_external_action=None,
        citations=[
            {
                "doc_id": "PA-ACC-MAIN",
                "clause_item": "ART-5-EXCL",
                "quote": "因疾病导致的伤害属于责任免除",
                "score": 0.9,
                "adoptable": True,
            }
        ],
    )
    assert disposition == "abstain"
    assert reason == "citation_unfaithful"
    assert latch is True


def test_disposition_entity_gap_also_abstains() -> None:
    """与夹具同缝：通赔断言但摘录缺关键实体 → citation_unfaithful。"""
    from missions.assist_disposition import resolve_assist_disposition

    disposition, reason, _latch = resolve_assist_disposition(
        query="骨折手术费可通赔",
        conflict_route_id=None,
        can_external_deny=True,
        retrieval_profile="clause_primary",
        stance="approve",
        intended_external_action=None,
        citations=[
            {
                "doc_id": "PA-ACC-MAIN",
                "clause_item": "ART-3-COVER",
                "quote": "保险人按约定给付意外伤害医疗费用",
                "score": 0.9,
                "adoptable": True,
            }
        ],
    )
    assert disposition == "abstain"
    assert reason == "citation_unfaithful"


def test_gold_subset_filters_bound_case_ids() -> None:
    """金标子集须按 bound_case_ids 过滤，不得用全文件 n 冒充子集。"""
    from missions.citation_faithfulness import run_faithfulness_fixtures

    report = run_faithfulness_fixtures(FIXTURES)
    assert report.gold_subset_n == 1
    assert report.gold_subset_h4_status == "deferred"


def test_gold_rate_none_when_rules_cannot_run() -> None:
    """无可机读 assertion+citation 时不得用 expected 自洽冒充忠实率。"""
    from missions.citation_faithfulness import evaluate_gold_thin_slice_faithfulness
    from missions.gold_label_io import load_dataset_file

    dataset = load_dataset_file(GOLD_EXAMPLE)
    report = evaluate_gold_thin_slice_faithfulness(dataset)
    assert report.faithfulness_rate is None
    assert report.h4_status == "deferred"
    assert report.grounded_claim_allowed is False


@pytest.mark.eval_bypass
def test_fixtures_file_runnable_all_cases_match() -> None:
    """S2：规则/夹具忠实检查可跑；全量与 expected 对齐。"""
    from missions.citation_faithfulness import run_faithfulness_fixtures

    assert FIXTURES.is_file()
    report = run_faithfulness_fixtures(FIXTURES)
    assert report.primary_metric == "rules_fixtures"
    assert report.llm_judge_as_primary is False
    assert report.total >= 5
    assert report.failed == 0
    assert report.passed == report.total
    # 绑 P-E3 子集边界诚实
    assert report.gold_subset_h4_status == "deferred"
    assert report.gold_subset_n < 10

"""接缝：冻结集 Recall@K / MRR 纯函数与门槛（票 46 / P-R3）。

S0（默认绿）：纯函数指标 + 门槛常量 + pytest 排除 assist_quality + Rewrote from。
S2 冻结集实跑见 tests/test_recall_eval_runner.py（-m assist_quality）。

Rewrote from: REF-CASE-RECALL
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def test_recall_at_k_and_mrr_on_known_ranking() -> None:
    """接缝：Recall@K / MRR 对已知排序给出独立真值（非 tautology）。"""
    from missions.recall_metrics import mean_reciprocal_rank, recall_at_k

    ranked = ["A", "B", "C", "D", "E"]
    relevant = {"C"}

    assert recall_at_k(ranked, relevant, k=1) == 0.0
    assert recall_at_k(ranked, relevant, k=2) == 0.0
    assert recall_at_k(ranked, relevant, k=3) == 1.0
    assert mean_reciprocal_rank(ranked, relevant) == pytest.approx(1.0 / 3.0)

    # 多相关：Recall@K = |交集| / |相关|
    assert recall_at_k(["X", "A", "Y", "B"], {"A", "B"}, k=2) == pytest.approx(0.5)
    assert recall_at_k(["X", "A", "Y", "B"], {"A", "B"}, k=4) == pytest.approx(1.0)
    assert mean_reciprocal_rank(["X", "A", "Y", "B"], {"A", "B"}) == pytest.approx(0.5)


def test_h_thresholds_match_spec() -> None:
    """接缝：H1/H2 门槛与 SPEC-02B-P 决策 9 字面一致。"""
    from missions.recall_metrics import H1_THRESHOLD, H2_MRR_THRESHOLD, H2_RECALL5_THRESHOLD

    assert H1_THRESHOLD == pytest.approx(0.95)
    assert H2_RECALL5_THRESHOLD == pytest.approx(0.70)
    assert H2_MRR_THRESHOLD == pytest.approx(0.55)


def test_pytest_ini_excludes_assist_quality_from_default() -> None:
    """接缝：默认 pytest 须排除 assist_quality，S2 失败不阻断轨 A。"""
    ini = (ROOT / "pytest.ini").read_text(encoding="utf-8")
    assert "assist_quality" in ini
    assert "not assist_quality" in ini


def test_module_declares_rewrote_from_ref_case_recall() -> None:
    """handoff：模块声明 Rewrote from: REF-CASE-RECALL。"""
    path = SRC / "missions" / "recall_metrics.py"
    text = path.read_text(encoding="utf-8")
    assert "Rewrote from" in text
    assert "REF-CASE-RECALL" in text


def test_evaluate_gate_report_shape_against_thresholds() -> None:
    """接缝：报告对照 H1/H2 门槛并给出可机读 pass/fail（不依赖真实检索）。"""
    from missions.recall_metrics import (
        HypothesisGateResult,
        evaluate_h1_h2_gates,
        summarize_query_metrics,
    )

    # H1：15 条里 15 条 Recall@1=1 → 1.0 ≥ 0.95
    h1_rows = [{"query_id": f"c{i}", "recall_at_1": 1.0} for i in range(15)]
    # H2：20 条 Recall@5=0.8、MRR=0.6 → 过门
    h2_rows = [
        {"query_id": f"s{i}", "recall_at_5": 0.8, "mrr": 0.6} for i in range(20)
    ]
    h1 = summarize_query_metrics(h1_rows, recall_key="recall_at_1")
    h2_r5 = summarize_query_metrics(h2_rows, recall_key="recall_at_5")
    h2_mrr = summarize_query_metrics(h2_rows, mrr_key="mrr")
    report = evaluate_h1_h2_gates(
        h1_recall_at_1=h1.mean_recall,
        h1_n=h1.n,
        h2_recall_at_5=h2_r5.mean_recall,
        h2_mrr=h2_mrr.mean_mrr,
        h2_n=h2_r5.n,
    )
    assert isinstance(report, HypothesisGateResult)
    assert report.h1_passed is True
    assert report.h2_passed is True
    assert report.all_passed is True
    assert report.h1_threshold == pytest.approx(0.95)
    assert report.h2_recall5_threshold == pytest.approx(0.70)
    assert report.h2_mrr_threshold == pytest.approx(0.55)

    fail = evaluate_h1_h2_gates(
        h1_recall_at_1=0.90,
        h1_n=15,
        h2_recall_at_5=0.50,
        h2_mrr=0.40,
        h2_n=20,
    )
    assert fail.h1_passed is False
    assert fail.h2_passed is False
    assert fail.all_passed is False

    # H2 OR：Recall@5 未达但 MRR 达标仍过门
    h2_or = evaluate_h1_h2_gates(
        h1_recall_at_1=1.0,
        h1_n=15,
        h2_recall_at_5=0.50,
        h2_mrr=0.60,
        h2_n=20,
    )
    assert h2_or.h2_passed is True
    assert h2_or.all_passed is True

    # 样本量不足不得过门
    thin = evaluate_h1_h2_gates(
        h1_recall_at_1=1.0,
        h1_n=10,
        h2_recall_at_5=1.0,
        h2_mrr=1.0,
        h2_n=10,
    )
    assert thin.h1_passed is False
    assert thin.h2_passed is False

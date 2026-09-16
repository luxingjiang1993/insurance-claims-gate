"""接缝：Judge–human agreement / κ 实填（票 50 / P-E5）。

S0：隔离契约——κ 可报告、合成不冒充、H4 门 κ≥0.60、不进 machine_check。
绑金标薄切片（P-E3）双标 annotation；加深 Issue 11 占位，非平行重切。

Rewrote from: REF-CASE-OPENEVALS
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GOLD_EXAMPLE = (
    ROOT / "artifacts" / "gold_thin_slice" / "gold_thin_slice.v1.example.json"
)
SPOT_SAMPLE = ROOT / "artifacts" / "spot_check_sample_sc01.json"


def test_module_declares_kappa_protocol_and_refs() -> None:
    """模块声明 κ 协议、H4 门槛、Rewrote from；加深 Issue 11。"""
    path = ROOT / "src" / "missions" / "judge_human_kappa.py"
    text = path.read_text(encoding="utf-8")
    assert "κ" in text or "kappa" in text.lower()
    assert "0.60" in text or "0.6" in text
    assert "REF-CASE-OPENEVALS" in text
    assert "Rewrote from" in text
    assert "合成" in text


def test_checks_does_not_route_through_kappa() -> None:
    """硬约束：κ / judge-human 不得吞并 machine_check 合门禁主缝。"""
    checks_src = (ROOT / "src" / "missions" / "checks.py").read_text(
        encoding="utf-8"
    )
    assert "judge_human_kappa" not in checks_src
    assert "cohen_kappa" not in checks_src


def test_cohen_kappa_worked_example() -> None:
    """Cohen κ：教科书 2×2 列联表（独立真源数值）。

    Yes/Yes=20, Yes/No=5, No/Yes=10, No/No=15
    → p_o=0.7, p_e=0.5, κ=0.4
    """
    from missions.judge_human_kappa import cohen_kappa

    a = ["yes"] * 25 + ["no"] * 25
    b = ["yes"] * 20 + ["no"] * 5 + ["yes"] * 10 + ["no"] * 15
    kappa = cohen_kappa(a, b)
    assert kappa is not None
    assert abs(kappa - 0.4) < 1e-9


def test_cohen_kappa_perfect_agreement_above_chance() -> None:
    """完全一致且非单类退化 → κ=1.0。"""
    from missions.judge_human_kappa import cohen_kappa

    labels = ["faithful", "unfaithful", "faithful", "unfaithful"]
    assert cohen_kappa(labels, labels) == 1.0


def test_cohen_kappa_empty_or_mismatch_returns_none() -> None:
    """空表或长度不一致 → 无可报告 κ。"""
    from missions.judge_human_kappa import cohen_kappa

    assert cohen_kappa([], []) is None
    assert cohen_kappa(["a"], ["a", "b"]) is None


def test_thin_slice_kappa_report_from_dual_annotation() -> None:
    """金标薄切片双标 → 可报告标者间 κ 与协议字段。"""
    from missions.gold_label_io import GoldLabelDataset, GoldLabelRecord
    from missions.judge_human_kappa import (
        KAPPA_GROUNDED_MIN,
        evaluate_thin_slice_kappa,
    )

    records = []
    for i, (fa, fb) in enumerate(
        [
            (True, True),
            (True, True),
            (False, False),
            (True, False),
            (False, True),
            (True, True),
            (False, False),
            (True, True),
            (False, False),
            (True, True),
        ]
    ):
        records.append(
            GoldLabelRecord(
                case_id=f"CLM-KAPPA-{i:03d}",
                expected={"citation_faithful": fa and fb},
                annotation={
                    "annotator_a_role": "external_claims_advisor_a",
                    "annotator_b_role": "external_claims_advisor_b",
                    "adjudicator_role": "third_party_adjudicator",
                    "label_a": {"citation_faithful": fa},
                    "label_b": {"citation_faithful": fb},
                    "adjudication": {"final": "agree", "reason_code": "test"},
                    "disagreement": fa != fb,
                },
            )
        )
    dataset = GoldLabelDataset(
        dataset_id="kappa-unit-n10",
        records=records,
        is_gold_thin_slice=True,
        schema="claims-gate-gold-thin-slice-v1",
    )
    report = evaluate_thin_slice_kappa(dataset, synthetic=False)
    assert report.n == 10
    assert report.kappa is not None
    assert report.pair_metric == "citation_faithful"
    assert report.protocol == "inter_annotator_cohen_kappa"
    assert report.kappa_grounded_min == KAPPA_GROUNDED_MIN
    assert report.is_synthetic is False
    assert report.h4_status == "n_met"
    payload = report.to_dict()
    assert "kappa" in payload
    assert payload["kappa_grounded_min"] == 0.60


def test_synthetic_example_cannot_claim_grounded() -> None:
    """仓库外形样例 / 合成抽检不得冒充真双标或宣称 grounded。"""
    from missions.gold_label_io import load_dataset_file
    from missions.judge_human_kappa import (
        KappaEvalError,
        evaluate_thin_slice_kappa,
        load_spot_check_as_synthetic_kappa,
    )

    gold = load_dataset_file(GOLD_EXAMPLE)
    report = evaluate_thin_slice_kappa(gold)
    assert report.is_synthetic is True
    assert report.grounded_claim_allowed is False
    assert report.h4_status == "deferred"
    with pytest.raises(KappaEvalError):
        report.assert_grounded_claim_allowed()

    synth = load_spot_check_as_synthetic_kappa(SPOT_SAMPLE)
    assert synth.is_synthetic is True
    assert synth.grounded_claim_allowed is False
    with pytest.raises(KappaEvalError):
        synth.assert_grounded_claim_allowed()


def test_h4_grounded_requires_kappa_faithfulness_and_n() -> None:
    """H4：n≥10 且忠实率≥0.85 且 κ≥0.60 且非合成 → 才可宣称 grounded。"""
    from missions.judge_human_kappa import (
        assess_grounded_claim_allowed,
        assert_grounded_claim_allowed,
        KappaEvalError,
    )

    assert (
        assess_grounded_claim_allowed(
            n=10,
            faithfulness_rate=0.85,
            kappa=0.60,
            is_synthetic=False,
        )
        is True
    )
    assert (
        assess_grounded_claim_allowed(
            n=10,
            faithfulness_rate=0.85,
            kappa=0.59,
            is_synthetic=False,
        )
        is False
    )
    assert (
        assess_grounded_claim_allowed(
            n=9,
            faithfulness_rate=1.0,
            kappa=1.0,
            is_synthetic=False,
        )
        is False
    )
    assert (
        assess_grounded_claim_allowed(
            n=10,
            faithfulness_rate=0.84,
            kappa=0.90,
            is_synthetic=False,
        )
        is False
    )
    assert (
        assess_grounded_claim_allowed(
            n=10,
            faithfulness_rate=0.90,
            kappa=0.90,
            is_synthetic=True,
        )
        is False
    )
    with pytest.raises(KappaEvalError):
        assert_grounded_claim_allowed(
            n=10,
            faithfulness_rate=0.90,
            kappa=0.50,
            is_synthetic=False,
        )


def test_acceptance_doc_exists_with_h4_and_synthetic_boundary() -> None:
    """验收文档含 κ 协议、H4 门槛与合成不冒充边界。"""
    path = ROOT / "docs" / "acceptance" / "judge-human-kappa.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "κ" in text or "kappa" in text.lower()
    assert "0.60" in text
    assert "合成" in text
    assert "grounded" in text.lower() or "H4" in text
    assert "REF-CASE-OPENEVALS" in text

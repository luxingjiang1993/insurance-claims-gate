"""接缝：Judge–human 合成抽检占位（P1-7）。

不阻塞轨 A 绿门；真实用户/金标运营延后；本票仅占位。

Rewrote from: REF-CASE-EVAL-ADVISOR, REF-MISSIONS
"""

from __future__ import annotations

from pathlib import Path

from missions.spot_check import (
    SpotCheckRow,
    compute_agreement_rate,
    load_spot_check_json,
)
from missions.validator import ValidationReport

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"


def test_validation_report_has_judge_human_agreement_placeholder() -> None:
    """裁决/校验报告可出现 judge_human_agreement；缺省为 null。"""
    report = ValidationReport(passed=True)
    assert report.judge_human_agreement is None

    report_with = ValidationReport(passed=True, judge_human_agreement=1.0)
    assert report_with.judge_human_agreement == 1.0


def test_spot_check_template_exists_with_required_columns() -> None:
    """抽检表模板含 case_id、系统裁决、合成人标、是否一致、备注。"""
    path = ARTIFACTS / "spot_check_template.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    for col in (
        "case_id",
        "系统裁决",
        "合成标注A",
        "合成标注B",
        "合成裁决",
        "是否一致",
        "备注",
    ):
        assert col in text
    assert "真实用户" in text or "金标" in text
    assert "延后" in text or "占位" in text


def test_spot_check_sample_sc_row_exists() -> None:
    """至少 1 份基于 SC-01 或 SC-02 的合成样例行。"""
    path = ARTIFACTS / "spot_check_sample_sc01.json"
    assert path.is_file()
    rows = load_spot_check_json(path)
    assert len(rows) >= 1
    row = rows[0]
    assert row.case_id.startswith("CLM-SC0")
    assert row.system_decision
    assert row.synthetic_label_a
    assert row.synthetic_label_b
    assert row.synthetic_adjudication
    assert isinstance(row.agrees_with_system, bool)


def test_compute_agreement_rate_from_filled_rows() -> None:
    """合成表可算出一致率占位（不冒充 ≥300 金标运营）。"""
    rows = [
        SpotCheckRow(
            case_id="CLM-SC01-001",
            system_decision="supplement",
            synthetic_label_a="supplement",
            synthetic_label_b="supplement",
            synthetic_adjudication="supplement",
            agrees_with_system=True,
            notes="合成",
        ),
        SpotCheckRow(
            case_id="CLM-SC02-001",
            system_decision="reject_draft",
            synthetic_label_a="reject_draft",
            synthetic_label_b="approve_recommend",
            synthetic_adjudication="reject_draft",
            agrees_with_system=True,
            notes="合成",
        ),
    ]
    rate = compute_agreement_rate(rows)
    assert rate == 1.0

    empty = compute_agreement_rate([])
    assert empty is None


def test_spot_check_does_not_enter_machine_check_gate() -> None:
    """硬约束：抽检占位不得吞并 machine_check 合门禁主缝。"""
    checks_src = (ROOT / "src" / "missions" / "checks.py").read_text(encoding="utf-8")
    assert "spot_check" not in checks_src
    assert "judge_human_agreement" not in checks_src

"""接缝：夜间 S2 质量门失败告警（票 48 / P-E6）。

S0：失败可观测（日志/本地产物）、不红轨 A、pytest 排除旁路、Rewrote from。
S2（-m assist_quality）：真实三维旁路失败可产出告警产物。

Rewrote from: REF-MISSIONS
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SEEDS = (
    ROOT
    / "artifacts"
    / "demo_retrieval_seeds"
    / "demo_retrieval_seeds.v1.json"
)
FAITH = ROOT / "artifacts" / "citation_faithfulness" / "fixtures.v1.json"
USABLE = ROOT / "artifacts" / "suggestion_usability" / "fixtures.v1.json"


def test_module_declares_rewrote_from_ref_missions() -> None:
    """handoff：告警模块声明 Rewrote from: REF-MISSIONS。"""
    text = (SRC / "missions" / "nightly_s2_alert.py").read_text(encoding="utf-8")
    assert "Rewrote from" in text
    assert "REF-MISSIONS" in text
    assert "旁路" in text or "不红" in text


def test_pytest_ini_keeps_assist_quality_out_of_s0() -> None:
    """接缝：默认 pytest 排除 assist_quality，S2 失败不阻断轨 A。"""
    ini = (ROOT / "pytest.ini").read_text(encoding="utf-8")
    assert "assist_quality" in ini
    assert "not assist_quality" in ini


def test_alert_from_failed_report_is_observable(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """接缝：质量失败 → 告警升起；本地 JSON + 日志可观测；不红轨 A。"""
    from missions.nightly_s2_alert import (
        evaluate_s2_alert,
        emit_alert_log,
        write_alert_artifact,
    )

    failed_payload = {
        "all_passed": False,
        "exit_code": 1,
        "blocks_track_a_gate": False,
        "gate_role": "assist_quality_s2_bypass",
        "dimensions": {
            "retrieval": {"passed": False, "name": "retrieval"},
            "citation_faithfulness": {"passed": True, "name": "citation_faithfulness"},
            "suggestion_usability": {"passed": True, "name": "suggestion_usability"},
        },
    }
    alert = evaluate_s2_alert(failed_payload)
    assert alert.alert_raised is True
    assert alert.blocks_track_a_gate is False
    assert alert.gate_role == "assist_quality_s2_bypass_alert"
    assert "retrieval" in alert.failed_dimensions
    assert alert.severity == "s2_quality_fail"

    out = write_alert_artifact(alert, tmp_path / "nightly_s2_alert.json")
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["alert_raised"] is True
    assert payload["blocks_track_a_gate"] is False
    assert payload["failed_dimensions"] == ["retrieval"]
    assert "旁路" in payload["docs_note"] or "不红" in payload["docs_note"]

    with caplog.at_level(logging.WARNING):
        msg = emit_alert_log(alert)
    assert "S2" in msg or "质量" in msg
    assert any("S2" in r.message or "质量" in r.message for r in caplog.records)


def test_no_alert_when_quality_passes(tmp_path: Path) -> None:
    """接缝：三维全过门 → 不告警；产物仍可落盘（可观测「无告警」）。"""
    from missions.nightly_s2_alert import evaluate_s2_alert, write_alert_artifact

    ok = {
        "all_passed": True,
        "exit_code": 0,
        "blocks_track_a_gate": False,
        "dimensions": {
            "retrieval": {"passed": True},
            "citation_faithfulness": {"passed": True},
            "suggestion_usability": {"passed": True},
        },
    }
    alert = evaluate_s2_alert(ok)
    assert alert.alert_raised is False
    assert alert.severity == "none"
    assert alert.failed_dimensions == []
    assert alert.blocks_track_a_gate is False

    out = write_alert_artifact(alert, tmp_path / "ok.json")
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["alert_raised"] is False


def test_alert_never_flips_machine_check_contract() -> None:
    """硬约束：告警不得吞并 machine_check；输入声称阻断轨 A 仍强制 False。"""
    from missions.nightly_s2_alert import evaluate_s2_alert
    from missions.checks import run_machine_check

    checks_text = (
        Path(__file__).resolve().parents[1] / "src" / "missions" / "checks.py"
    ).read_text(encoding="utf-8")
    assert "nightly_s2" not in checks_text
    assert callable(run_machine_check)

    forced = evaluate_s2_alert(
        {
            "all_passed": False,
            "exit_code": 1,
            "blocks_track_a_gate": True,  # 恶意/误传字段不得生效
            "dimensions": {"retrieval": {"passed": False}},
        }
    )
    assert forced.blocks_track_a_gate is False
    assert forced.alert_raised is True


@pytest.mark.assist_quality
def test_nightly_run_raises_alert_on_injected_retrieval_fail(tmp_path: Path) -> None:
    """S2：三维旁路失败时 nightly 入口写出告警产物且 exit 非 0，仍不红轨 A。"""
    from missions.nightly_s2_alert import run_nightly_s2_alert

    result = run_nightly_s2_alert(
        seeds_path=SEEDS,
        faithfulness_fixtures_path=FAITH,
        usability_fixtures_path=USABLE,
        retrieve_fn=lambda _q: [],  # 检索空 → 质量失败
        quality_out=tmp_path / "three_dim.json",
        alert_out=tmp_path / "alert.json",
    )
    assert result.alert.alert_raised is True
    assert result.alert.blocks_track_a_gate is False
    assert result.exit_code != 0
    assert result.quality_report_path.exists()
    assert result.alert_artifact_path.exists()
    alert_payload = json.loads(result.alert_artifact_path.read_text(encoding="utf-8"))
    assert alert_payload["alert_raised"] is True
    assert alert_payload["blocks_track_a_gate"] is False

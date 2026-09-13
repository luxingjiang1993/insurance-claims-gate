"""接缝：Eval / 负例旁路入口（不替代 machine_check 合门禁主缝）。

契约测试（默认 CI）：仅断言旁路存在与「不吞并 machine_check」。
套件测试（-m eval_bypass）：跑固定负例并产出机读 pass/fail；失败不阻断轨 A。

Rewrote from: REF-CASE-OPENEVALS, REF-MISSIONS
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from claims_api.api import app, reset_service
from missions.eval_entry import (
    EVAL_GATE_ROLE,
    EvalConfig,
    run_eval_negatives,
    to_machine_readable_report,
)

ROOT = Path(__file__).resolve().parents[2]


def test_eval_config_declares_bypass_not_gate() -> None:
    """旁路契约：不得阻断轨 A 合门禁，不得要求 LLM。"""
    cfg = EvalConfig()
    assert cfg.gate_role == EVAL_GATE_ROLE
    assert cfg.blocks_track_a_gate is False
    assert cfg.requires_llm is False
    assert "旁路" in cfg.docs_note or "非合门禁" in cfg.docs_note


def test_checks_module_does_not_route_sc_through_eval_entry() -> None:
    """硬约束：合门禁主缝仍是 machine_check，不得吞并到 eval_entry。"""
    checks_src = (ROOT / "src" / "missions" / "checks.py").read_text(encoding="utf-8")
    assert "eval_entry" not in checks_src
    assert "run_eval_negatives" not in checks_src


def test_pytest_ini_excludes_eval_bypass_from_default() -> None:
    """默认 pytest 须排除 eval_bypass，旁路失败不阻断轨 A。"""
    ini = (ROOT / "pytest.ini").read_text(encoding="utf-8")
    assert "eval_bypass" in ini
    assert "not eval_bypass" in ini


def test_eval_entry_module_exists() -> None:
    """独立模块入口存在（旁路外形，非合门禁）。"""
    path = ROOT / "src" / "missions" / "eval_entry.py"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "旁路" in text and "非合门禁" in text
    assert "REF-CASE-OPENEVALS" in text


@pytest.mark.eval_bypass
def test_eval_entry_covers_two_negative_categories() -> None:
    """至少覆盖 2 类负例：幻觉/库外 citation + 通融伪 citation（或拆轮）。"""
    reset_service()
    client = TestClient(app)
    report = run_eval_negatives(client)

    categories = {c.category for c in report.cases}
    assert "hallucination_citation" in categories
    assert (
        "exgratia_fake_citation" in categories
        or "one_shot_split_round" in categories
    )
    assert len(report.cases) >= 2
    for case in report.cases:
        assert isinstance(case.passed, bool)
        assert case.detail


@pytest.mark.eval_bypass
def test_eval_report_is_machine_readable_pass_fail() -> None:
    """产出可机读 pass/fail 结构（JSON 可序列化）；旁路套件全绿≠合门禁。"""
    reset_service()
    client = TestClient(app)
    report = run_eval_negatives(client)
    payload = to_machine_readable_report(report)

    dumped = json.dumps(payload, ensure_ascii=False)
    assert "cases" in payload
    assert "summary" in payload
    assert payload["gate_role"] == EVAL_GATE_ROLE
    assert payload["blocks_track_a_gate"] is False
    assert payload["summary"]["total"] == len(payload["cases"])
    assert (
        payload["summary"]["passed"] + payload["summary"]["failed"]
        == payload["summary"]["total"]
    )
    for case in payload["cases"]:
        assert "id" in case and "passed" in case and "category" in case
    assert payload["summary"]["failed"] == 0, dumped

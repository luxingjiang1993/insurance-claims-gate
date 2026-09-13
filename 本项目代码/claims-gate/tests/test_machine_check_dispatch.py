"""接缝：machine_check 仅按 type + params 分发，不按断言 ID 硬编码。"""

from __future__ import annotations

import inspect

from fastapi.testclient import TestClient

from claims_api.api import app, reset_service
from missions.checks import run_machine_check
from missions.models import MachineCheck


def test_claim_header_l1_check_passes_by_type_params() -> None:
    reset_service()
    client = TestClient(app)
    outcome = run_machine_check(
        client,
        MachineCheck(type="claim_header_l1", params={"case_id": "CLM-SC01-001"}),
    )
    assert outcome.ok, outcome.detail


def test_dispatcher_source_has_no_assertion_id_hardcode() -> None:
    """分发器源码不得出现按 A-00x 分支的硬编码开关。"""
    import missions.checks as checks_mod

    src = inspect.getsource(checks_mod.run_machine_check)
    assert "A-001" not in src
    assert "A-002" not in src
    assert '== "A-' not in src
    assert "assertion_id" not in src


def test_unknown_machine_check_type_fails() -> None:
    reset_service()
    client = TestClient(app)
    outcome = run_machine_check(
        client,
        MachineCheck(type="not_a_real_check", params={}),
    )
    assert not outcome.ok
    assert "unknown" in outcome.detail.lower() or "unsupported" in outcome.detail.lower()

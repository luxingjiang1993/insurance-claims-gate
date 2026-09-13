"""接缝：Orchestrator → Worker → Validator 空回路可跑；默认确定性轨；支付工具无权限。"""

from __future__ import annotations

from pathlib import Path

import pytest

from claims_api.tools_acl import ToolPermissionError, assert_tool_allowed
from missions.runner import MissionRunner


ROOT = Path(__file__).resolve().parents[1]


def test_empty_missions_loop_reaches_human_latch(tmp_path: Path) -> None:
    runner = MissionRunner(ROOT, artifacts_dir=tmp_path / "artifacts")
    state = runner.new_mission("m-scaffold-01", goal="脚手架：拉案件头进入材料受理")
    assert state.contract is not None
    assert state.contract.inference_track == "deterministic"
    # 入账前已通过 schema（否则 new_mission 会抛）
    assert state.contract.assertions
    assert all(a.machine_check.type for a in state.contract.assertions)

    state = runner.run_queued_workers_serial(state)
    assert any(f.status.value == "done" for f in state.features)

    state, report = runner.validate(state)
    assert report.passed, report.notes
    assert state.phase == "awaiting_human_approval"
    assert state.human_approval is not None
    assert state.human_approval.approved is False


def test_payment_tools_denied_by_default() -> None:
    with pytest.raises(ToolPermissionError):
        assert_tool_allowed("bank_payout_transfer")
    with pytest.raises(ToolPermissionError):
        assert_tool_allowed("silver_enterprise_direct_pay")
    # 非支付只读工具允许
    assert_tool_allowed("read_claim_header")

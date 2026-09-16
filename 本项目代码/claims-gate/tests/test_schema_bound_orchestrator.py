"""接缝 Q-S0-A：Schema-bound Orchestrator（契约硬停 + goal 必用 + 去字符串主规划）。

Rewrote from: REF-MISSIONS（契约入账）；REF-COURSE-03（Schema 外形）
"""

from __future__ import annotations

from pathlib import Path

import pytest

from missions.contract_schema import ContractSchemaError, validate_contract_dict
from missions.plan_schema import PlanSchemaError, validate_plan_request
from missions.runner import MissionRunner

ROOT = Path(__file__).resolve().parents[1]


def test_empty_goal_hard_stops_before_booking(tmp_path: Path) -> None:
    """缺 goal / 空白 → 入账前失败，不写契约、不创建 implement feature。"""
    runner = MissionRunner(ROOT, artifacts_dir=tmp_path / "artifacts")
    with pytest.raises((PlanSchemaError, ValueError)):
        runner.new_mission("m-no-goal", goal="   ")
    contract_path = tmp_path / "artifacts" / "validation_contract.json"
    assert not contract_path.exists()
    features_path = tmp_path / "artifacts" / "features.json"
    if features_path.exists():
        import json

        assert json.loads(features_path.read_text(encoding="utf-8")) == []


def test_illegal_plan_request_template_hard_stops() -> None:
    """非法 plan 结构（未知 template_id）→ Schema 硬停。"""
    with pytest.raises(PlanSchemaError):
        validate_plan_request({"goal": "任意目标文案", "template_id": "not-a-real-template"})


def test_missing_goal_in_plan_request_hard_stops() -> None:
    with pytest.raises(PlanSchemaError):
        validate_plan_request({"template_id": "scaffold"})


def test_illegal_contract_missing_goal_hard_stops() -> None:
    """契约缺 goal → 入账前 JSON Schema 硬停。"""
    bad = {
        "mission_id": "m-bad",
        "title": "x",
        "version": "1.0.0",
        "created_by": "orchestrator",
        "assertions": [
            {
                "id": "A-001",
                "behavior": "b",
                "policy_clause_id": "POL-CLAIM-001",
                "acceptance": "a",
                "machine_check": {"type": "claim_header_l1", "params": {}},
            }
        ],
        "source_citations": [
            {
                "doc_id": "d",
                "chunk_id": "c",
                "clause_id": "POL-CLAIM-001",
                "quote": "材料受理",
                "score": 0.9,
            }
        ],
    }
    with pytest.raises(ContractSchemaError):
        validate_contract_dict(bad)


def test_valid_plan_books_goal_observable_in_contract_and_handoff(tmp_path: Path) -> None:
    """合法契约可入账；goal 可在 contract / handoff 观察；Rewrote from 存在。"""
    runner = MissionRunner(ROOT, artifacts_dir=tmp_path / "artifacts")
    goal = "脚手架：拉案件头进入材料受理"
    state = runner.new_mission("m-scaffold-a2", goal=goal, template_id="scaffold")
    assert state.contract is not None
    assert state.contract.goal == goal
    assert state.features
    assert all(f.kind.value == "implement" for f in state.features)
    assert state.handoffs
    orch_handoff = state.handoffs[-1]
    assert "Rewrote from:" in orch_handoff.process_notes or orch_handoff.rewrote_from
    # goal 在 handoff 侧也可观察（broadcast_ack / completed / process_notes / events）
    observable = (
        goal in orch_handoff.process_notes
        or any(goal in c for c in orch_handoff.completed)
        or any(e.get("goal") == goal for e in state.events)
    )
    assert observable


def test_plan_source_is_template_id_not_goal_substring(tmp_path: Path) -> None:
    """规划主路径：契约源来自 schema 合法 template_id，不以 goal 字符串匹配冒充。"""
    runner = MissionRunner(ROOT, artifacts_dir=tmp_path / "artifacts")
    # goal 故意含 sc-01 / 拒赔 等关键字，但显式 template_id=scaffold
    poisoned_goal = "请做 sc-01 一次补件与 SC-02 拒赔；也要 router ledger"
    state = runner.new_mission(
        "m-honesty-01",
        goal=poisoned_goal,
        template_id="scaffold",
    )
    assert state.contract is not None
    assert state.contract.goal == poisoned_goal
    types = {a.machine_check.type for a in state.contract.assertions}
    assert types == {"claim_header_l1"}
    assert "sc01_one_shot_supplement_approve" not in types
    assert "sc02_exclusion_reject_latch" not in types
    assert "router_ledger_reproducible" not in types


def test_same_goal_different_template_yields_different_contracts(tmp_path: Path) -> None:
    """同一 goal 文案 + 不同 template_id → 不同契约，证明分支不靠字符串匹配。"""
    runner = MissionRunner(ROOT, artifacts_dir=tmp_path / "a")
    goal = "统一目标文案，不含场景关键字"
    scaffold = runner.new_mission("m-t-scaffold", goal=goal, template_id="scaffold")
    runner2 = MissionRunner(ROOT, artifacts_dir=tmp_path / "b")
    sc01 = runner2.new_mission("m-t-sc01", goal=goal, template_id="sc01")
    assert scaffold.contract is not None and sc01.contract is not None
    assert scaffold.contract.assertions[0].machine_check.type == "claim_header_l1"
    assert any(
        a.machine_check.type == "sc01_one_shot_supplement_approve"
        for a in sc01.contract.assertions
    )

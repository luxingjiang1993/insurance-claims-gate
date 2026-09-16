"""接缝 Q-A6：Validator 独立 retrieve profile + 零产品写（轻量 S0）。

真多模型 / 需 Key 旁路，不得并入默认 pytest -q。
Rewrote from: REF-MISSIONS
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from missions.models import (
    Assertion,
    AssertionStatus,
    MachineCheck,
    MissionState,
    RoleName,
    ValidationContract,
)
from missions.rag import KnowledgeBase
from missions.role_profiles import (
    VALIDATOR_MODEL_NAME,
    VALIDATOR_RETRIEVE_PROFILE,
    WORKER_MODEL_NAME,
    WORKER_RETRIEVE_PROFILE,
)
from missions.store import ArtifactStore
from missions.validator import Validator
from missions.worker import Worker


ROOT = Path(__file__).resolve().parents[1]
_PRODUCT_GLOBS = ("src/claims_api/**/*.py", "src/missions/**/*.py")


def _fingerprint_product_tree(root: Path) -> dict[str, str]:
    """产品树内容指纹：用于断言 Validator 零写入。"""
    digests: dict[str, str] = {}
    for pattern in _PRODUCT_GLOBS:
        for path in sorted(root.glob(pattern)):
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            digests[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def _contract_with_missing_clause(mission_id: str = "m-q-a6-fail") -> ValidationContract:
    """故意缺 KB 条款 → Validator 失败，只出 fail report。"""
    return ValidationContract(
        mission_id=mission_id,
        title="Q-A6 fail report",
        goal="验证失败只报不改",
        assertions=[
            Assertion(
                id="A-QA6-MISSING",
                behavior="缺条款应失败",
                policy_clause_id="POL-DOES-NOT-EXIST-QA6",
                acceptance="不得改产品代码",
                machine_check=MachineCheck(
                    type="claim_header_l1",
                    params={"case_id": "CLM-SC01-001"},
                ),
                status=AssertionStatus.PENDING,
            )
        ],
    )


def _validator(artifacts: Path, **kwargs) -> Validator:
    return Validator(
        KnowledgeBase(ROOT / "knowledge_base"),
        ArtifactStore(artifacts),
        ROOT,
        **kwargs,
    )


def test_validator_retrieve_profile_differs_from_worker() -> None:
    """轻量 S0：profile（或可配置模型名）与 Worker 可区分。"""
    assert VALIDATOR_RETRIEVE_PROFILE != WORKER_RETRIEVE_PROFILE
    assert VALIDATOR_MODEL_NAME != WORKER_MODEL_NAME

    v = Validator(
        KnowledgeBase(ROOT / "knowledge_base"),
        ArtifactStore(ROOT / "artifacts" / "_qa6_unused"),
        ROOT,
    )
    w = Worker(
        KnowledgeBase(ROOT / "knowledge_base"),
        ArtifactStore(ROOT / "artifacts" / "_qa6_unused"),
        ROOT,
    )
    assert v.retrieve_profile == VALIDATOR_RETRIEVE_PROFILE
    assert w.retrieve_profile == WORKER_RETRIEVE_PROFILE
    assert v.retrieve_profile != w.retrieve_profile
    assert v.model_name == VALIDATOR_MODEL_NAME
    assert w.model_name == WORKER_MODEL_NAME
    assert v.model_name != w.model_name


def test_validator_accepts_independent_profile_override(tmp_path: Path) -> None:
    v = _validator(
        tmp_path / "artifacts",
        retrieve_profile="validator_custom_s0",
        model_name="validator-judge-custom",
    )
    assert v.retrieve_profile == "validator_custom_s0"
    assert v.model_name == "validator-judge-custom"
    assert v.retrieve_profile != WORKER_RETRIEVE_PROFILE


def test_validator_path_writes_zero_product_tree(tmp_path: Path) -> None:
    """Validator 路径：运行后产品树无写入（仅 artifacts / 状态）。"""
    before = _fingerprint_product_tree(ROOT)
    artifacts = tmp_path / "artifacts"
    state = MissionState(
        mission_id="m-q-a6-pass-shape",
        phase="implementation",
        contract=_contract_with_missing_clause("m-q-a6-pass-shape"),
    )
    validator = _validator(artifacts)
    state, report = validator.validate_milestone(state)

    after = _fingerprint_product_tree(ROOT)
    assert after == before
    assert report.passed is False
    assert state.phase == "validation_failed"


def test_failure_emits_fail_report_does_not_self_patch(tmp_path: Path) -> None:
    """失败 → fail report；不自改产品；handoff 含 Rewrote from。"""
    before = _fingerprint_product_tree(ROOT)
    artifacts = tmp_path / "artifacts"
    state = MissionState(
        mission_id="m-q-a6-fail-report",
        phase="implementation",
        contract=_contract_with_missing_clause(),
    )
    validator = _validator(artifacts)
    state, report = validator.validate_milestone(state)

    assert report.passed is False
    assert report.failed_assertions
    assert state.phase == "validation_failed"
    assert state.last_validation_passed is False

    fail_path = artifacts / "fail_report.json"
    assert fail_path.is_file()
    payload = json.loads(fail_path.read_text(encoding="utf-8"))
    assert payload["passed"] is False
    assert payload["failed_assertions"] == report.failed_assertions
    assert "Rewrote from" in payload.get("process_notes", "") or payload.get(
        "rewrote_from"
    )

    handoff = state.handoffs[-1]
    assert handoff.role == RoleName.VALIDATOR
    assert handoff.rewrote_from
    assert "REF-MISSIONS" in handoff.rewrote_from
    assert handoff.incomplete  # 失败细节在 incomplete / notes

    # Validator 不开 fix；features 仍空（Orchestrator 才开 fix）
    assert state.features == []

    after = _fingerprint_product_tree(ROOT)
    assert after == before


def test_validation_event_records_distinct_profile(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    state = MissionState(
        mission_id="m-q-a6-event",
        phase="implementation",
        contract=_contract_with_missing_clause("m-q-a6-event"),
    )
    validator = _validator(artifacts)
    state, _report = validator.validate_milestone(state)
    start_events = [e for e in state.events if e.get("kind") == "validation_start"]
    assert start_events
    assert start_events[0]["retrieval_profile"] == VALIDATOR_RETRIEVE_PROFILE
    assert start_events[0]["retrieval_profile"] != WORKER_RETRIEVE_PROFILE
    assert start_events[0].get("model_name") == VALIDATOR_MODEL_NAME


@pytest.mark.requires_llm
def test_true_multimodel_validator_bypassed_from_default_ci() -> None:
    """真多模型 Validator 旁路：默认 addopts 排除 requires_llm，不绑架轨 A。"""
    pytest.skip("真多模型 / 需 Key 调用不进默认 pytest -q（Q-A6 Testing Decisions）")

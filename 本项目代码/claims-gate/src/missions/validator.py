"""Validator：HTTP 黑盒 + contract.machine_check；只报问题，不改产品代码。

Rewrote from: REF-MISSIONS（missions/validator.py）；
P1-7 一致率占位字段 Rewrote from: REF-CASE-EVAL-ADVISOR, REF-MISSIONS；
Q-A6 独立 profile / 零产品写 Rewrote from: REF-MISSIONS
"""

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass, field
from pathlib import Path

from fastapi.testclient import TestClient

from .checks import run_assertion_checks
from .models import (
    AssertionStatus,
    HandoffRecord,
    HumanApproval,
    MissionState,
    RoleName,
)
from .rag import KnowledgeBase
from .role_profiles import VALIDATOR_MODEL_NAME, VALIDATOR_RETRIEVE_PROFILE
from .store import ArtifactStore

@dataclass
class ValidationReport:
    passed: bool
    failed_assertions: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    citations_count: int = 0
    # P1-7：Judge–human 一致率占位；缺省 null，不阻塞机器绿门
    judge_human_agreement: float | None = None


class Validator:
    def __init__(
        self,
        kb: KnowledgeBase,
        store: ArtifactStore,
        project_root: Path,
        *,
        retrieve_profile: str = VALIDATOR_RETRIEVE_PROFILE,
        model_name: str = VALIDATOR_MODEL_NAME,
    ) -> None:
        self.kb = kb
        self.store = store
        self.project_root = project_root
        # 与 Worker 可区分的检索画像 / 模型名（轻量 S0；不触发真多模型）
        self.retrieve_profile = retrieve_profile
        self.model_name = model_name

    def validate_milestone(self, state: MissionState) -> tuple[MissionState, ValidationReport]:
        assert state.contract is not None
        state.current_role = RoleName.VALIDATOR
        state.phase = "validation"
        state.validation_rounds += 1
        state.writer_lock_held_by = None
        state.locked_paths = []

        citations = []
        for assertion in state.contract.assertions:
            citations.extend(
                self.kb.retrieve(
                    assertion.behavior + " " + assertion.acceptance,
                    role=RoleName.VALIDATOR,
                    profile=self.retrieve_profile,
                    top_k=5,
                    clause_hint=assertion.policy_clause_id,
                )
            )

        self.store.emit(
            state,
            kind="validation_start",
            message=f"第 {state.validation_rounds} 轮 HTTP 黑盒验收",
            role=RoleName.VALIDATOR,
            extra={
                "retrieval_profile": self.retrieve_profile,
                "model_name": self.model_name,
            },
        )

        client = self._build_http_client()
        outcomes = run_assertion_checks(client, state.contract.assertions)

        report = ValidationReport(passed=True, citations_count=len(citations))
        commands = []
        for assertion in state.contract.assertions:
            if self.kb.get_clause(assertion.policy_clause_id) is None:
                assertion.status = AssertionStatus.FAILED
                report.passed = False
                report.failed_assertions.append(assertion.id)
                report.notes.append(f"{assertion.id}: 知识库缺少 {assertion.policy_clause_id}")
                continue

            outcome = outcomes[assertion.id]
            commands.append(outcome.command)
            if outcome.ok:
                assertion.status = AssertionStatus.PASSED
            else:
                assertion.status = AssertionStatus.FAILED
                report.passed = False
                report.failed_assertions.append(assertion.id)
                report.notes.append(
                    f"{assertion.id} 失败；条款 {assertion.policy_clause_id}；"
                    f"{assertion.acceptance}；detail={outcome.detail}"
                )

        state.last_validation_passed = report.passed
        if report.passed:
            state.phase = "awaiting_human_approval"
            state.human_approval = HumanApproval(
                required=True,
                action="promote_milestone",
                approved=False,
            )
        else:
            state.phase = "validation_failed"

        process_notes = (
            "Validator 不修改产品代码；失败只出 fail report，交 Orchestrator 开 fix；"
            "Rewrote from: REF-CASE-KB, REF-MISSIONS"
        )
        rewrote = "REF-CASE-KB, REF-MISSIONS"
        handoff = HandoffRecord(
            handoff_id=f"h-val-r{state.validation_rounds}",
            mission_id=state.mission_id,
            role=RoleName.VALIDATOR,
            completed=["HTTP 黑盒 + machine_check 全通过"] if report.passed else [],
            incomplete=[] if report.passed else report.notes,
            commands=commands,
            citations_used=citations[:8],
            process_followed=True,
            process_notes=process_notes,
            rewrote_from=rewrote,
        )
        self.store.append_handoff(state, handoff)
        if not report.passed:
            self._write_fail_report(report, process_notes=process_notes, rewrote_from=rewrote)
        self.store.emit(
            state,
            kind="validation_done",
            message="验收通过，等待人类批准 promote" if report.passed else "验收失败",
            role=RoleName.VALIDATOR,
            extra={
                "passed": report.passed,
                "failed_assertions": report.failed_assertions,
                "retrieval_profile": self.retrieve_profile,
                "model_name": self.model_name,
                # 占位：缺省 null；可由合成抽检表事后填入，不参与合门禁
                "judge_human_agreement": report.judge_human_agreement,
            },
        )
        return state, report

    def _write_fail_report(
        self,
        report: ValidationReport,
        *,
        process_notes: str,
        rewrote_from: str,
    ) -> None:
        """失败报告只写入 artifacts，永不写产品树。"""
        payload = {
            "passed": report.passed,
            "failed_assertions": list(report.failed_assertions),
            "notes": list(report.notes),
            "citations_count": report.citations_count,
            "retrieval_profile": self.retrieve_profile,
            "model_name": self.model_name,
            "process_notes": process_notes,
            "rewrote_from": rewrote_from,
            "judge_human_agreement": report.judge_human_agreement,
        }
        self.store.write_fail_report(payload)

    def _build_http_client(self) -> TestClient:
        src = str(self.project_root / "src")
        if src not in sys.path:
            sys.path.insert(0, src)

        import claims_api.service as service_mod
        import claims_api.api as api_mod

        importlib.reload(service_mod)
        importlib.reload(api_mod)
        api_mod.reset_service()
        return TestClient(api_mod.app)

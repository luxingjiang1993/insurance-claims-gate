"""Mission runner：串行 Worker、验证预算、人类门闩。

Rewrote from: REF-MISSIONS（missions/runner.py；去掉转账审计夹具）
"""

from __future__ import annotations

from pathlib import Path

from .models import FeatureStatus, MissionState, RoleName, utc_now_iso
from .orchestrator import Orchestrator
from .rag import KnowledgeBase
from .store import ArtifactStore
from .validator import Validator
from .worker import Worker


class MissionRunner:
    def __init__(
        self,
        project_root: Path,
        *,
        artifacts_dir: Path | None = None,
    ) -> None:
        self.project_root = project_root
        self.artifacts = artifacts_dir if artifacts_dir is not None else project_root / "artifacts"
        self.store = ArtifactStore(self.artifacts)
        self.kb = KnowledgeBase(project_root / "knowledge_base")
        self.orchestrator = Orchestrator(self.kb, self.store)
        self.worker = Worker(self.kb, self.store, project_root)
        self.validator = Validator(self.kb, self.store, project_root)

    def new_mission(
        self,
        mission_id: str,
        goal: str,
        *,
        template_id: str = "scaffold",
    ) -> MissionState:
        """创建使命并 Schema-bound 规划；非法 plan/契约在入账前硬停。"""
        state = MissionState(
            mission_id=mission_id,
            phase="init",
            autonomy_level="L1",
            demo_mode="claims_gate_scaffold",
        )
        self.store.save_state(state)
        return self.orchestrator.plan(state, goal, template_id=template_id)

    def run_queued_workers_serial(self, state: MissionState) -> MissionState:
        for feature in state.features:
            if feature.status != FeatureStatus.QUEUED:
                continue
            if state.handoffs and state.handoffs[-1].blocked_for_human:
                self.store.emit(
                    state,
                    kind="blocked",
                    message=state.handoffs[-1].block_reason or "阻塞中",
                    role=RoleName.ORCHESTRATOR,
                )
                break
            state = self.worker.run_feature(state, feature)
        return state

    def validate(self, state: MissionState):
        return self.validator.validate_milestone(state)

    def open_fix_and_rerun(self, state: MissionState, report) -> MissionState:
        if state.contract and state.validation_rounds >= state.contract.max_validation_rounds:
            state.phase = "blocked_for_human"
            self.store.emit(
                state,
                kind="budget_exhausted",
                message="验证轮次耗尽，交回人类",
                role=RoleName.ORCHESTRATOR,
            )
            return state

        self.orchestrator.open_fix_feature(
            state,
            failed_assertions=report.failed_assertions,
            reason="; ".join(report.notes) if report.notes else "validation failed",
        )
        fix = state.features[-1]
        state = self.worker.run_feature(state, fix)
        if fix.status != FeatureStatus.DONE:
            return state
        state, _report2 = self.validator.validate_milestone(state)
        return state

    def approve_promotion(self, state: MissionState, *, approved_by: str = "human") -> MissionState:
        if not state.last_validation_passed:
            raise RuntimeError("验证未通过，不能批准 promote")
        if state.human_approval is None:
            raise RuntimeError("无待批准项")
        state.human_approval.approved = True
        state.human_approval.approved_at = utc_now_iso()
        state.human_approval.approved_by = approved_by
        state.phase = "promoted"
        self.store.emit(
            state,
            kind="human_approved",
            message=f"人类批准 promote：{approved_by}",
            role=None,
        )
        self.store.save_state(state)
        return state

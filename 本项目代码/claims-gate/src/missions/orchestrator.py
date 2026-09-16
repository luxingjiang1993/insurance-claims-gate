"""编排者：契约先行；入账前 JSON Schema 硬停；不做实现与最终验收。

Rewrote from: REF-MISSIONS（missions/orchestrator.py；断言换理赔脚手架）；
REF-COURSE-03（Schema-bound plan request）；
SC-03 效力栈减赔契约 REF-CASE-KB, REF-COURSE-04；
Router/ledger REF-COURSE-12, REF-CASE-HYBRID, REF-MISSIONS
"""

from __future__ import annotations

from .contract_schema import validate_contract_dict
from .models import (
    FeatureKind,
    FeatureStatus,
    HandoffRecord,
    MissionFeature,
    MissionState,
    RoleName,
    ValidationContract,
    utc_now_iso,
)
from .plan_schema import validate_plan_request
from .plan_templates import get_plan_template
from .rag import KnowledgeBase
from .store import ArtifactStore


class Orchestrator:
    def __init__(self, kb: KnowledgeBase, store: ArtifactStore) -> None:
        self.kb = kb
        self.store = store

    def plan(
        self,
        state: MissionState,
        goal: str,
        *,
        template_id: str = "scaffold",
    ) -> MissionState:
        """Schema-bound 规划：plan request + validation contract 双硬停后再入账。

        契约源来自 template_id 目录查找，不以 goal 字符串 if/elif 为主规划源。
        """
        # 规划入参硬停（缺 goal / 非法 template_id）——尚未创建 implement feature
        validate_plan_request({"goal": goal, "template_id": template_id})
        goal_clean = goal.strip()
        template = get_plan_template(template_id)

        state.current_role = RoleName.ORCHESTRATOR
        state.phase = "planning"
        state.writer_lock_held_by = None
        state.locked_paths = []

        chunk = self.kb.get_clause(template.clause_id)
        if chunk is None:
            raise RuntimeError(f"知识库缺少 {template.clause_id}，无法写出契约")

        from .models import RagCitation

        citations = [
            RagCitation(
                doc_id=chunk.doc_id,
                chunk_id=chunk.chunk_id,
                clause_id=chunk.clause_id,
                clause_item=chunk.clause_item,
                quote=chunk.text[:120],
                score=1.0,
                title=chunk.title,
                doc_version=chunk.doc_version,
                retrieved_by=RoleName.ORCHESTRATOR,
                retrieval_profile="orchestrator_goal_top5",
            )
        ]
        for extra in self.kb.retrieve(
            goal_clean,
            role=RoleName.ORCHESTRATOR,
            profile="orchestrator_goal_top5",
            top_k=5,
            clause_hint=chunk.clause_id,
        ):
            if extra.chunk_id != chunk.chunk_id:
                citations.append(extra)

        assertions = template.build_assertions(template.clause_id)
        rewrote = template.rewrote_from

        contract = ValidationContract(
            mission_id=state.mission_id,
            title=template.title,
            goal=goal_clean,
            broadcast_constraints=[
                "验收标准以 validation contract.machine_check 为准，不得从实现反推",
                "同一时刻只允许一个 Worker 持有写锁",
                "支付类工具默认无权限",
                "默认 inference_track=deterministic",
            ],
            assertions=assertions,
            source_citations=citations,
            created_at=utc_now_iso(),
            max_validation_rounds=5,
            inference_track="deterministic",
        )

        # 入账前 JSON Schema 硬停（P1-2 / Q-S0-A）
        validate_contract_dict(contract.model_dump(mode="json"))
        state.contract = contract

        state.features = [
            MissionFeature(
                feature_id="F-001",
                title=template.feature_title,
                milestone=template.milestone,
                kind=FeatureKind.IMPLEMENT,
                claims_assertions=[a.id for a in assertions],
                status=FeatureStatus.QUEUED,
                owns_paths=list(template.owns_paths),
            )
        ]

        self.store.emit(
            state,
            kind="contract_ready",
            message="validation contract 已外置；inference_track=deterministic",
            role=RoleName.ORCHESTRATOR,
            extra={
                "goal": goal_clean,
                "template_id": template.template_id,
                "assertion_count": len(assertions),
            },
        )

        handoff = HandoffRecord(
            handoff_id=f"h-orch-{state.mission_id}",
            mission_id=state.mission_id,
            role=RoleName.ORCHESTRATOR,
            completed=[
                "写出带 machine_check 的 validation contract",
                "JSON Schema 入账前硬停通过",
                f"goal={goal_clean}",
                f"template_id={template.template_id}",
                f"拆分 features: {[f.feature_id for f in state.features]}",
            ],
            incomplete=["等待 Worker 串行实现", "等待 Validator 黑盒验收"],
            citations_used=citations[:8],
            process_followed=True,
            process_notes=(
                f"编排者不实现代码，不自行最终验收；"
                f"Schema-bound template_id={template.template_id}；"
                f"Rewrote from: {rewrote}"
            ),
            broadcast_ack=contract.broadcast_constraints,
            rewrote_from=rewrote,
        )
        self.store.append_handoff(state, handoff)
        state.phase = "implementation"
        state.autonomy_level = "L1"
        self.store.save_state(state)
        return state

    def open_fix_feature(
        self,
        state: MissionState,
        *,
        failed_assertions: list[str],
        reason: str,
    ) -> MissionFeature:
        if state.contract and state.validation_rounds >= state.contract.max_validation_rounds:
            raise RuntimeError("已达 max_validation_rounds，必须交回人类")

        next_id = f"F-{len(state.features) + 1:03d}"
        fix = MissionFeature(
            feature_id=next_id,
            title=f"修复验收失败: {','.join(failed_assertions)}",
            milestone="M0-scaffold",
            kind=FeatureKind.FIX,
            claims_assertions=failed_assertions,
            status=FeatureStatus.QUEUED,
            owns_paths=["src/claims_api/service.py"],
            notes=reason,
        )
        state.features.append(fix)
        state.phase = "fix_implementation"
        self.store.emit(
            state,
            kind="fix_opened",
            message=reason,
            role=RoleName.ORCHESTRATOR,
            extra={"feature_id": next_id, "failed_assertions": failed_assertions},
        )
        self.store.save_state(state)
        return fix

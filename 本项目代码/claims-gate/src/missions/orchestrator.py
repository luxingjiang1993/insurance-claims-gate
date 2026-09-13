"""编排者：契约先行；入账前 JSON Schema 硬停；不做实现与最终验收。

Rewrote from: REF-MISSIONS（missions/orchestrator.py；断言换理赔脚手架）
"""

from __future__ import annotations

from .contract_schema import validate_contract_dict
from .models import (
    Assertion,
    FeatureKind,
    FeatureStatus,
    HandoffRecord,
    MachineCheck,
    MissionFeature,
    MissionState,
    RoleName,
    ValidationContract,
    utc_now_iso,
)
from .rag import KnowledgeBase
from .store import ArtifactStore


class Orchestrator:
    def __init__(self, kb: KnowledgeBase, store: ArtifactStore) -> None:
        self.kb = kb
        self.store = store

    def plan(self, state: MissionState, goal: str) -> MissionState:
        if not goal or not goal.strip():
            raise ValueError("goal 不能为空：编排必须由目标驱动")

        state.current_role = RoleName.ORCHESTRATOR
        state.phase = "planning"
        state.writer_lock_held_by = None
        state.locked_paths = []

        goal_l = goal.strip().lower()
        is_sc01 = any(
            key in goal_l or key in goal
            for key in ("sc-01", "sc01", "一次补件", "通赔建议", "one_shot")
        )
        clause_id = "POL-CLAIM-002" if is_sc01 else "POL-CLAIM-001"
        chunk = self.kb.get_clause(clause_id)
        if chunk is None:
            raise RuntimeError(f"知识库缺少 {clause_id}，无法写出契约")

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
            goal,
            role=RoleName.ORCHESTRATOR,
            profile="orchestrator_goal_top5",
            top_k=5,
            clause_hint=chunk.clause_id,
        ):
            if extra.chunk_id != chunk.chunk_id:
                citations.append(extra)

        if is_sc01:
            assertions = [
                Assertion(
                    id="A-001",
                    behavior="同 one_shot_hash 拆轮补件必须失败关闭",
                    policy_clause_id=chunk.clause_id,
                    acceptance="supplement/notify 子集缺项返回 VALIDATION_FAILED",
                    machine_check=MachineCheck(
                        type="one_shot_split_round_rejected",
                        params={"case_id": "CLM-SC01-001"},
                    ),
                    claimed_by_features=["F-001"],
                ),
                Assertion(
                    id="A-002",
                    behavior="SC-01：缺发票一次补件后补传，产出通赔建议且未人闸前不出款就绪",
                    policy_clause_id=chunk.clause_id,
                    acceptance="HTTP：evaluate→export→materials→evaluate；payout_ready=false",
                    machine_check=MachineCheck(
                        type="sc01_one_shot_supplement_approve",
                        params={"case_id": "CLM-SC01-001"},
                    ),
                    claimed_by_features=["F-001"],
                ),
            ]
            title = "SC-01 一次补件 → 通赔建议（轨 A）"
            owns = [
                "src/claims_api/api.py",
                "src/claims_api/service.py",
                "src/claims_api/models_domain.py",
                "src/missions/checks.py",
            ]
            feature_title = "实现 SC-01 一次补件与通赔建议确定性轨"
            milestone = "M1-sc01"
            rewrote = "REF-MISSIONS, REF-COURSE-03"
        else:
            assertions = [
                Assertion(
                    id="A-001",
                    behavior="L1 只读返回案件头且门禁态为 MATERIALS_INTAKE",
                    policy_clause_id="POL-CLAIM-001",
                    acceptance="GET /claims/{case_id} 含最低字段且 gate_status=MATERIALS_INTAKE",
                    machine_check=MachineCheck(
                        type="claim_header_l1",
                        params={"case_id": "CLM-SC01-001", "gate_status": "MATERIALS_INTAKE"},
                    ),
                    claimed_by_features=["F-001"],
                )
            ]
            title = "条款门禁脚手架：案件头只读"
            owns = [
                "src/claims_api/api.py",
                "src/claims_api/service.py",
                "src/claims_api/error_codes.py",
            ]
            feature_title = "实现 L1 案件头只读与 MATERIALS_INTAKE"
            milestone = "M0-scaffold"
            rewrote = "REF-MISSIONS"

        contract = ValidationContract(
            mission_id=state.mission_id,
            title=title,
            goal=goal.strip(),
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

        # 入账前 JSON Schema 硬停（P1-2）
        validate_contract_dict(contract.model_dump(mode="json"))
        state.contract = contract

        state.features = [
            MissionFeature(
                feature_id="F-001",
                title=feature_title,
                milestone=milestone,
                kind=FeatureKind.IMPLEMENT,
                claims_assertions=[a.id for a in assertions],
                status=FeatureStatus.QUEUED,
                owns_paths=owns,
            )
        ]

        self.store.emit(
            state,
            kind="contract_ready",
            message="validation contract 已外置；inference_track=deterministic",
            role=RoleName.ORCHESTRATOR,
            extra={"goal": goal, "assertion_count": len(assertions), "sc01": is_sc01},
        )

        handoff = HandoffRecord(
            handoff_id=f"h-orch-{state.mission_id}",
            mission_id=state.mission_id,
            role=RoleName.ORCHESTRATOR,
            completed=[
                "写出带 machine_check 的 validation contract",
                "JSON Schema 入账前硬停通过",
                f"拆分 features: {[f.feature_id for f in state.features]}",
            ],
            incomplete=["等待 Worker 串行实现", "等待 Validator 黑盒验收"],
            citations_used=citations[:8],
            process_followed=True,
            process_notes=f"编排者不实现代码，不自行最终验收；Rewrote from: {rewrote}",
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

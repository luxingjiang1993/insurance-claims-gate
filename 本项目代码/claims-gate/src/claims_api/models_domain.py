"""理赔案件领域模型（内存夹具 + SQLite 序列化）。

Rewrote from: REF-MISSIONS（models_domain 换理赔域）；SC-01 补件/裁决字段 REF-COURSE-03；
SC-02 拒赔/人闸/appeal_path REF-MISSIONS；SC-03 calc_steps / 效力栈 REF-COURSE-04；
Issue 06 金额档/冻决/峰值字段 REF-MISSIONS；
Issue 07 Router/ledger 字段 REF-COURSE-12, REF-CASE-HYBRID, REF-MISSIONS；
Issue 08 L2 主数据快照字段 REF-MISSIONS；
Issue 09 OCR/备注用户可控字段 REF-CASE-HYBRID, REF-MISSIONS；
Issue 14 SQLite 往返序列化 REF-MISSIONS
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CoreMasterSnapshot:
    """核心主数据快照：与案件侧字段对齐校验（禁止出款就绪时不一致）。"""

    case_id: str
    policy_no: str
    product_code: str
    clause_version: str
    endorsement_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "policy_no": self.policy_no,
            "product_code": self.product_code,
            "clause_version": self.clause_version,
            "endorsement_flags": list(self.endorsement_flags),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CoreMasterSnapshot:
        return cls(
            case_id=str(data["case_id"]),
            policy_no=str(data["policy_no"]),
            product_code=str(data["product_code"]),
            clause_version=str(data["clause_version"]),
            endorsement_flags=list(data.get("endorsement_flags") or []),
        )


@dataclass
class LatchEvent:
    """人闸事件摘要（批准/驳回可回放）。"""

    case_id: str
    event_type: str
    actor: str
    ts: str
    human_latch_token: str | None = None
    reason: str = ""
    second_approver: str | None = None

    def to_dict(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "case_id": self.case_id,
            "event_type": self.event_type,
            "actor": self.actor,
            "ts": self.ts,
            "reason": self.reason,
        }
        if self.human_latch_token is not None:
            body["human_latch_token"] = self.human_latch_token
        if self.second_approver is not None:
            body["second_approver"] = self.second_approver
        return body

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LatchEvent:
        return cls(
            case_id=str(data["case_id"]),
            event_type=str(data["event_type"]),
            actor=str(data["actor"]),
            ts=str(data.get("ts") or ""),
            human_latch_token=data.get("human_latch_token"),
            reason=str(data.get("reason") or ""),
            second_approver=data.get("second_approver"),
        )


@dataclass
class SupplementItem:
    """补件缺项：code + 中文名 + 是否必须 + 示例说明。"""

    code: str
    name_zh: str
    required: bool
    example: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "name_zh": self.name_zh,
            "required": self.required,
            "example": self.example,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SupplementItem:
        return cls(
            code=str(data["code"]),
            name_zh=str(data["name_zh"]),
            required=bool(data.get("required", True)),
            example=str(data.get("example") or ""),
        )


@dataclass
class DecisionDraft:
    """裁决草案最低外形（SPEC 决策 5）。"""

    decision_type: str
    gate_status: str
    document_status: str
    payout_ready: bool
    inference_track: str = "deterministic"
    supplement_checklist: list[SupplementItem] = field(default_factory=list)
    # 一次补件后尚未满足的剩余缺项（部分补传重评可观察）
    remaining_missing: list[SupplementItem] = field(default_factory=list)
    one_shot_hash: str | None = None
    human_latch_required: bool = False
    human_latch_token: str | None = None
    citations: list[dict[str, Any]] = field(default_factory=list)
    calc_steps: list[dict[str, Any]] = field(default_factory=list)
    # 拒赔草案必填：申诉/人工复核入口
    appeal_path: str | None = None
    reason_summary: str | None = None
    # Issue 06：人闸矩阵可观察字段
    amount_tier: str | None = None
    latch_tier: str | None = None
    dual_token_required: bool = False
    latch_level_label: str | None = None
    recommended_payout_amount: int | None = None
    freeze_active: bool = False
    peak_degraded: bool = False
    # Issue 07：Router / ledger 可观察字段
    route_id: str | None = None
    retrieval_profile: str | None = None
    validator_score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "decision_type": self.decision_type,
            "gate_status": self.gate_status,
            "document_status": self.document_status,
            "payout_ready": self.payout_ready,
            "inference_track": self.inference_track,
            "human_latch_required": self.human_latch_required,
            "human_latch_token": self.human_latch_token,
            "citations": list(self.citations),
            "calc_steps": list(self.calc_steps),
            "freeze_active": self.freeze_active,
            "peak_degraded": self.peak_degraded,
            "dual_token_required": self.dual_token_required,
        }
        if self.one_shot_hash is not None:
            body["one_shot_hash"] = self.one_shot_hash
        if self.supplement_checklist:
            body["supplement_checklist"] = [i.to_dict() for i in self.supplement_checklist]
        else:
            body["supplement_checklist"] = []
        if self.remaining_missing:
            body["remaining_missing"] = [i.to_dict() for i in self.remaining_missing]
        if self.appeal_path is not None:
            body["appeal_path"] = self.appeal_path
        if self.reason_summary is not None:
            body["reason_summary"] = self.reason_summary
        if self.amount_tier is not None:
            body["amount_tier"] = self.amount_tier
        if self.latch_tier is not None:
            body["latch_tier"] = self.latch_tier
        if self.latch_level_label is not None:
            body["latch_level_label"] = self.latch_level_label
        if self.recommended_payout_amount is not None:
            body["recommended_payout_amount"] = self.recommended_payout_amount
        if self.route_id is not None:
            body["route_id"] = self.route_id
        if self.retrieval_profile is not None:
            body["retrieval_profile"] = self.retrieval_profile
        if self.validator_score is not None:
            body["validator_score"] = self.validator_score
        return body

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DecisionDraft:
        checklist = [
            SupplementItem.from_dict(i) for i in (data.get("supplement_checklist") or [])
        ]
        remaining = [
            SupplementItem.from_dict(i) for i in (data.get("remaining_missing") or [])
        ]
        return cls(
            decision_type=str(data["decision_type"]),
            gate_status=str(data["gate_status"]),
            document_status=str(data["document_status"]),
            payout_ready=bool(data.get("payout_ready", False)),
            inference_track=str(data.get("inference_track") or "deterministic"),
            supplement_checklist=checklist,
            remaining_missing=remaining,
            one_shot_hash=data.get("one_shot_hash"),
            human_latch_required=bool(data.get("human_latch_required", False)),
            human_latch_token=data.get("human_latch_token"),
            citations=list(data.get("citations") or []),
            calc_steps=list(data.get("calc_steps") or []),
            appeal_path=data.get("appeal_path"),
            reason_summary=data.get("reason_summary"),
            amount_tier=data.get("amount_tier"),
            latch_tier=data.get("latch_tier"),
            dual_token_required=bool(data.get("dual_token_required", False)),
            latch_level_label=data.get("latch_level_label"),
            recommended_payout_amount=data.get("recommended_payout_amount"),
            freeze_active=bool(data.get("freeze_active", False)),
            peak_degraded=bool(data.get("peak_degraded", False)),
            route_id=data.get("route_id"),
            retrieval_profile=data.get("retrieval_profile"),
            validator_score=data.get("validator_score"),
        )


@dataclass
class LedgerEntry:
    """每案审计 ledger：路由与检索配置可回放。"""

    case_id: str
    route_id: str
    retrieval_profile: str
    decision_type: str
    validator_score: float
    ts: str = ""
    arbitration_winner: str | None = None

    def to_dict(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "case_id": self.case_id,
            "route_id": self.route_id,
            "retrieval_profile": self.retrieval_profile,
            "decision_type": self.decision_type,
            "validator_score": self.validator_score,
            "ts": self.ts,
        }
        if self.arbitration_winner is not None:
            body["arbitration_winner"] = self.arbitration_winner
        return body

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LedgerEntry:
        return cls(
            case_id=str(data["case_id"]),
            route_id=str(data["route_id"]),
            retrieval_profile=str(data["retrieval_profile"]),
            decision_type=str(data["decision_type"]),
            validator_score=float(data.get("validator_score") or 0.0),
            ts=str(data.get("ts") or ""),
            arbitration_winner=data.get("arbitration_winner"),
        )


@dataclass
class ClaimCase:
    """L1 案件头 + 材料码 + 门禁/裁决态。"""

    case_id: str
    policy_no: str
    product_code: str
    clause_version: str
    loss_date: str
    claim_amount_claimed: int
    endorsement_flags: list[str] = field(default_factory=list)
    image_ids: list[str] = field(default_factory=list)
    # 已登记材料码（确定性轨材料齐全断言）
    material_codes: list[str] = field(default_factory=list)
    # 出险原因码：accident | disease_fall（SC-02 除外）
    loss_cause: str = "accident"
    gate_status: str = "MATERIALS_INTAKE"
    inference_track: str = "deterministic"
    # 冻结的一次补件指纹与完整清单
    frozen_one_shot_hash: str | None = None
    frozen_checklist_codes: list[str] = field(default_factory=list)
    latest_decision: DecisionDraft | None = None
    # 人闸令牌与批准人（拒赔对外通知绑定）
    human_latch_token: str | None = None
    human_approver: str | None = None
    # 每案 ledger（最新在前由服务层维护）
    ledger: list[LedgerEntry] = field(default_factory=list)
    # Issue 06：敏感标志、调查冻决、峰值降级
    sensitivity_flags: list[str] = field(default_factory=list)
    freeze_active: bool = False
    peak_degraded: bool = False
    # Issue 09：用户可控文本（OCR/备注）— 仅收纳可观察，不得改写人闸
    ocr_text: str = ""
    customer_remark: str = ""
    # Issue 08：核心主数据快照；缺省由服务层按案件字段自洽填充
    core_master: CoreMasterSnapshot | None = None
    # 结案意见（L2 回写；与出款解耦）
    close_opinion: str | None = None
    # Issue 14：人闸事件（与 SQLite latch_events 同步）
    latch_events: list[LatchEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "case_id": self.case_id,
            "policy_no": self.policy_no,
            "product_code": self.product_code,
            "clause_version": self.clause_version,
            "loss_date": self.loss_date,
            "claim_amount_claimed": self.claim_amount_claimed,
            "endorsement_flags": list(self.endorsement_flags),
            "image_ids": list(self.image_ids),
            "material_codes": list(self.material_codes),
            "loss_cause": self.loss_cause,
            "gate_status": self.gate_status,
            "inference_track": self.inference_track,
            "frozen_one_shot_hash": self.frozen_one_shot_hash,
            "frozen_checklist_codes": list(self.frozen_checklist_codes),
            "human_latch_token": self.human_latch_token,
            "human_approver": self.human_approver,
            "ledger": [e.to_dict() for e in self.ledger],
            "sensitivity_flags": list(self.sensitivity_flags),
            "freeze_active": self.freeze_active,
            "peak_degraded": self.peak_degraded,
            "ocr_text": self.ocr_text,
            "customer_remark": self.customer_remark,
            "close_opinion": self.close_opinion,
            "latch_events": [e.to_dict() for e in self.latch_events],
        }
        if self.latest_decision is not None:
            body["latest_decision"] = self.latest_decision.to_dict()
        if self.core_master is not None:
            body["core_master"] = self.core_master.to_dict()
        return body

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ClaimCase:
        latest = data.get("latest_decision")
        core = data.get("core_master")
        return cls(
            case_id=str(data["case_id"]),
            policy_no=str(data["policy_no"]),
            product_code=str(data["product_code"]),
            clause_version=str(data["clause_version"]),
            loss_date=str(data["loss_date"]),
            claim_amount_claimed=int(data["claim_amount_claimed"]),
            endorsement_flags=list(data.get("endorsement_flags") or []),
            image_ids=list(data.get("image_ids") or []),
            material_codes=list(data.get("material_codes") or []),
            loss_cause=str(data.get("loss_cause") or "accident"),
            gate_status=str(data.get("gate_status") or "MATERIALS_INTAKE"),
            inference_track=str(data.get("inference_track") or "deterministic"),
            frozen_one_shot_hash=data.get("frozen_one_shot_hash"),
            frozen_checklist_codes=list(data.get("frozen_checklist_codes") or []),
            latest_decision=DecisionDraft.from_dict(latest) if latest else None,
            human_latch_token=data.get("human_latch_token"),
            human_approver=data.get("human_approver"),
            ledger=[LedgerEntry.from_dict(e) for e in (data.get("ledger") or [])],
            sensitivity_flags=list(data.get("sensitivity_flags") or []),
            freeze_active=bool(data.get("freeze_active", False)),
            peak_degraded=bool(data.get("peak_degraded", False)),
            ocr_text=str(data.get("ocr_text") or ""),
            customer_remark=str(data.get("customer_remark") or ""),
            core_master=CoreMasterSnapshot.from_dict(core) if core else None,
            close_opinion=data.get("close_opinion"),
            latch_events=[
                LatchEvent.from_dict(e) for e in (data.get("latch_events") or [])
            ],
        )

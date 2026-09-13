"""理赔案件领域模型（内存夹具）。

Rewrote from: REF-MISSIONS（models_domain 换理赔域）；SC-01 补件/裁决字段 REF-COURSE-03；
SC-02 拒赔/人闸/appeal_path REF-MISSIONS；SC-03 calc_steps / 效力栈 REF-COURSE-04；
Issue 06 金额档/冻决/峰值字段 REF-MISSIONS；
Issue 07 Router/ledger 字段 REF-COURSE-12, REF-CASE-HYBRID, REF-MISSIONS；
Issue 08 L2 主数据快照字段 REF-MISSIONS；
Issue 09 OCR/备注用户可控字段 REF-CASE-HYBRID, REF-MISSIONS
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
    # Issue 08：核心主数据快照；缺省由服务层按案件字段自洽填充
    core_master: CoreMasterSnapshot | None = None
    # 结案意见（L2 回写；与出款解耦）
    close_opinion: str | None = None

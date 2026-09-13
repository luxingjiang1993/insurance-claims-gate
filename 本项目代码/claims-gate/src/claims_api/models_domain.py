"""理赔案件领域模型（内存夹具）。

Rewrote from: REF-MISSIONS（models_domain 换理赔域）；SC-01 补件/裁决字段 REF-COURSE-03
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
        }
        if self.one_shot_hash is not None:
            body["one_shot_hash"] = self.one_shot_hash
        if self.supplement_checklist:
            body["supplement_checklist"] = [i.to_dict() for i in self.supplement_checklist]
        else:
            body["supplement_checklist"] = []
        if self.remaining_missing:
            body["remaining_missing"] = [i.to_dict() for i in self.remaining_missing]
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
    gate_status: str = "MATERIALS_INTAKE"
    inference_track: str = "deterministic"
    # 冻结的一次补件指纹与完整清单
    frozen_one_shot_hash: str | None = None
    frozen_checklist_codes: list[str] = field(default_factory=list)
    latest_decision: DecisionDraft | None = None

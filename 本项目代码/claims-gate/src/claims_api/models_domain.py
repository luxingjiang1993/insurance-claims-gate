"""理赔案件领域模型（内存夹具）。

Rewrote from: REF-MISSIONS（models_domain 换理赔域）
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ClaimCase:
    """L1 案件头最低字段 + 门禁态。"""

    case_id: str
    policy_no: str
    product_code: str
    clause_version: str
    loss_date: str
    claim_amount_claimed: int
    endorsement_flags: list[str] = field(default_factory=list)
    image_ids: list[str] = field(default_factory=list)
    gate_status: str = "MATERIALS_INTAKE"
    inference_track: str = "deterministic"

"""理赔案件服务：L1 只读与材料受理态。

Rewrote from: REF-MISSIONS（transfer_api/service.py 换垂直）
"""

from __future__ import annotations

from .error_codes import ErrorCode
from .models_domain import ClaimCase


class ClaimNotFoundError(LookupError):
    def __init__(self, case_id: str) -> None:
        super().__init__(case_id)
        self.case_id = case_id
        self.error_code = ErrorCode.VALIDATION_FAILED.value


class ClaimsService:
    """内存案件台账；脚手架预置一案可达 MATERIALS_INTAKE。"""

    def __init__(self) -> None:
        self._cases: dict[str, ClaimCase] = {}
        self._seed()

    def _seed(self) -> None:
        case = ClaimCase(
            case_id="CLM-SC01-001",
            policy_no="PA-2026-000188",
            product_code="PA-ACCIDENT-MED",
            clause_version="PA-ACC-2024.1",
            loss_date="2026-08-01",
            claim_amount_claimed=350000,
            endorsement_flags=[],
            image_ids=["IMG-ID-CARD", "IMG-CLAIM-FORM"],
            gate_status="MATERIALS_INTAKE",
            inference_track="deterministic",
        )
        self._cases[case.case_id] = case

    def get_claim(self, case_id: str) -> ClaimCase:
        case = self._cases.get(case_id)
        if case is None:
            raise ClaimNotFoundError(case_id)
        return case

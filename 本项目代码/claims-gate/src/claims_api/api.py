"""FastAPI 外壳：Validator 只能经 HTTP 黑盒验收，不得改产品代码。

Rewrote from: REF-MISSIONS（transfer_api/api.py 换理赔域）
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .error_codes import ErrorCode
from .service import ClaimNotFoundError, ClaimsService
from .tools_acl import assert_tool_allowed

app = FastAPI(title="Claims Gate API", version="0.1.0")
_service = ClaimsService()


def get_service() -> ClaimsService:
    return _service


def reset_service() -> ClaimsService:
    """测试夹具：重建内存台账。"""
    global _service
    _service = ClaimsService()
    return _service


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "inference_track": "deterministic"}


@app.get("/claims/{case_id}")
def get_claim(case_id: str) -> dict:
    """L1 只读案件头；默认推理轨为确定性轨。"""
    assert_tool_allowed("read_claim_header")
    try:
        case = _service.get_claim(case_id)
    except ClaimNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.VALIDATION_FAILED.value,
                "message": f"案件不存在: {exc.case_id}",
            },
        ) from exc
    return {
        "case_id": case.case_id,
        "policy_no": case.policy_no,
        "product_code": case.product_code,
        "clause_version": case.clause_version,
        "endorsement_flags": list(case.endorsement_flags),
        "loss_date": case.loss_date,
        "claim_amount_claimed": case.claim_amount_claimed,
        "image_ids": list(case.image_ids),
        "gate_status": case.gate_status,
        "inference_track": case.inference_track,
    }

"""FastAPI 外壳：Validator 只能经 HTTP 黑盒验收，不得改产品代码。

Rewrote from: REF-MISSIONS（transfer_api/api.py 换理赔域）；citation 门 REF-CASE-KB
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from missions.rag import KnowledgeBase

from .error_codes import ErrorCode
from .service import ClaimNotFoundError, ClaimsService
from .tools_acl import assert_tool_allowed

app = FastAPI(title="Claims Gate API", version="0.1.0")
_service = ClaimsService()
_KB_ROOT = Path(__file__).resolve().parents[2] / "knowledge_base"
_kb = KnowledgeBase(_KB_ROOT)


class CitationValidateRequest(BaseModel):
    """对外可用 citation 最低落库键。"""

    doc_id: str
    clause_item: str
    doc_version: str
    quote: str = ""


def get_service() -> ClaimsService:
    return _service


def get_kb() -> KnowledgeBase:
    return _kb


def reset_service() -> ClaimsService:
    """测试夹具：重建内存台账并重载条款 KB。"""
    global _service, _kb
    _service = ClaimsService()
    _kb = KnowledgeBase(_KB_ROOT)
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


@app.post("/kb/citations/validate")
def validate_citation(body: CitationValidateRequest) -> dict[str, Any]:
    """条款项级落库门：doc_id + clause_item + doc_version 三联命中。"""
    assert_tool_allowed("validate_citation")
    result = _kb.validate_citation(body.model_dump())
    if not result.ok:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": result.error_code or ErrorCode.CITATION_NOT_IN_KB.value,
                "message": result.detail,
            },
        )
    chunk = result.chunk
    assert chunk is not None
    return {
        "ok": True,
        "doc_id": chunk.doc_id,
        "clause_item": chunk.clause_item,
        "doc_version": chunk.doc_version,
        "chunk_id": chunk.chunk_id,
        "authority_rank": chunk.authority_rank,
        "effective_date": chunk.effective_date,
    }

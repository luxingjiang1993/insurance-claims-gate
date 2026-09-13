"""FastAPI 外壳：Validator 只能经 HTTP 黑盒验收，不得改产品代码。

Rewrote from: REF-MISSIONS（transfer_api/api.py 换理赔域）；citation 门 REF-CASE-KB；
SC-01 补件/裁决/文书 REF-COURSE-03
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from missions.rag import KnowledgeBase

from .error_codes import ErrorCode
from .service import ClaimNotFoundError, ClaimsDomainError, ClaimsService
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


class MaterialsIn(BaseModel):
    """补传材料元数据。"""

    material_codes: list[str] = Field(min_length=1)
    image_ids: list[str] = Field(default_factory=list)


class SupplementNotifyIn(BaseModel):
    """补件通知请求：须携带与冻结清单一致的完整缺项。"""

    one_shot_hash: str
    missing_item_codes: list[str] = Field(min_length=1)


class DocumentExportIn(BaseModel):
    """文书导出请求。"""

    document_type: str = "supplement_notice"
    document_status: str = "DRAFT_EXPORT"


def get_service() -> ClaimsService:
    return _service


def reset_service() -> ClaimsService:
    """测试夹具：重建内存台账并重载条款 KB。"""
    global _service, _kb
    _service = ClaimsService()
    _kb = KnowledgeBase(_KB_ROOT)
    return _service


def _http_domain_error(exc: ClaimsDomainError) -> HTTPException:
    status = 422
    if exc.error_code == ErrorCode.DOCUMENT_STATUS_FORBIDDEN.value:
        status = 403
    return HTTPException(
        status_code=status,
        detail={"error_code": exc.error_code, "message": exc.message},
    )


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
        "material_codes": list(case.material_codes),
        "gate_status": case.gate_status,
        "inference_track": case.inference_track,
    }


@app.post("/claims/{case_id}/evaluate")
def evaluate_claim(case_id: str) -> dict[str, Any]:
    """触发门禁裁决：材料不齐→一次补件；齐→通赔建议草案。"""
    assert_tool_allowed("evaluate_claim")
    try:
        decision = _service.evaluate(case_id)
    except ClaimNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.VALIDATION_FAILED.value,
                "message": f"案件不存在: {exc.case_id}",
            },
        ) from exc
    except ClaimsDomainError as exc:
        raise _http_domain_error(exc) from exc
    body = decision.to_dict()
    body["case_id"] = case_id
    return body


@app.get("/claims/{case_id}/decision")
def get_decision(case_id: str) -> dict[str, Any]:
    """查询最近裁决草案。"""
    assert_tool_allowed("read_decision")
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
    if case.latest_decision is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.VALIDATION_FAILED.value,
                "message": "尚无裁决草案，请先 evaluate",
            },
        )
    body = case.latest_decision.to_dict()
    body["case_id"] = case_id
    return body


@app.post("/claims/{case_id}/materials")
def register_materials(case_id: str, body: MaterialsIn) -> dict[str, Any]:
    """提交补件材料后登记；需再次 evaluate 重评。"""
    assert_tool_allowed("register_materials")
    try:
        case = _service.register_materials(
            case_id,
            material_codes=body.material_codes,
            image_ids=body.image_ids,
        )
    except ClaimNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.VALIDATION_FAILED.value,
                "message": f"案件不存在: {exc.case_id}",
            },
        ) from exc
    except ClaimsDomainError as exc:
        raise _http_domain_error(exc) from exc
    return {
        "case_id": case.case_id,
        "material_codes": list(case.material_codes),
        "image_ids": list(case.image_ids),
        "gate_status": case.gate_status,
    }


@app.post("/claims/{case_id}/supplement/notify")
def notify_supplement(case_id: str, body: SupplementNotifyIn) -> dict[str, Any]:
    """发出补件通知；同 hash 拆轮必失败。"""
    assert_tool_allowed("notify_supplement")
    try:
        return _service.notify_supplement(
            case_id,
            one_shot_hash=body.one_shot_hash,
            missing_item_codes=body.missing_item_codes,
        )
    except ClaimNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.VALIDATION_FAILED.value,
                "message": f"案件不存在: {exc.case_id}",
            },
        ) from exc
    except ClaimsDomainError as exc:
        raise _http_domain_error(exc) from exc


@app.post("/claims/{case_id}/documents/export")
def export_document(case_id: str, body: DocumentExportIn) -> dict[str, Any]:
    """导出补件/拒赔等文书；补件 DRAFT_EXPORT 可无人闸。"""
    assert_tool_allowed("export_document")
    try:
        return _service.export_document(
            case_id,
            document_type=body.document_type,
            document_status=body.document_status,
        )
    except ClaimNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.VALIDATION_FAILED.value,
                "message": f"案件不存在: {exc.case_id}",
            },
        ) from exc
    except ClaimsDomainError as exc:
        raise _http_domain_error(exc) from exc


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

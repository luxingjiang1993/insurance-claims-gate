"""FastAPI 外壳：Validator 只能经 HTTP 黑盒验收，不得改产品代码。

Rewrote from: REF-MISSIONS（transfer_api/api.py 换理赔域）；citation 门 REF-CASE-KB；
SC-01 补件/裁决/文书 REF-COURSE-03；SC-02 拒赔分态与人闸 REF-MISSIONS；
SC-03 减赔 REF-COURSE-04；Issue 06 人闸矩阵扩展 REF-MISSIONS
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
_KB_ROOT = Path(__file__).resolve().parents[2] / "knowledge_base"
_kb = KnowledgeBase(_KB_ROOT)


def _build_service() -> ClaimsService:
    """重建服务；共享同一 KB 实例，拒赔对外通知经 KB 落库门失败关闭。"""
    svc = ClaimsService(kb=_kb)

    def _ok(payload: dict[str, Any]) -> bool:
        return _kb.validate_citation(payload).ok

    svc.set_citation_validator(_ok)
    return svc


_service = _build_service()


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
    human_latch_token: str | None = None


class EvaluateIn(BaseModel):
    """裁决请求；可选提出理算参数（与条款冲突时失败关闭）。"""

    proposed_deductible: int | None = None
    proposed_ratio: float | None = None
    # 敏感场景上浮（诉讼/信访/媒体等）
    sensitivity_flags: list[str] = Field(default_factory=list)
    # Issue 07：Router 冲突探针 / handbook 独撑拒赔探针
    signal_sources: list[str] = Field(default_factory=list)
    source_decisions: dict[str, str] = Field(default_factory=dict)
    retrieval_profile: str | None = None
    force_reject_with_handbook_only: bool = False


class HumanLatchApproveIn(BaseModel):
    """人闸批准请求；D 档上浮时须 second_approver。"""

    approved_by: str = Field(min_length=1)
    second_approver: str | None = None


class HumanLatchRejectIn(BaseModel):
    """人闸驳回请求。"""

    rejected_by: str = Field(min_length=1)
    reason: str = ""


class ExgratiaIn(BaseModel):
    """通融决定请求。"""

    reason: str = Field(min_length=1)
    recommended_amount: int = Field(ge=0)
    citations: list[dict[str, Any]] = Field(default_factory=list)


class PrepayIn(BaseModel):
    """预赔决定请求。"""

    reason: str = Field(min_length=1)
    recommended_amount: int = Field(ge=0)


class InvestigateEnterIn(BaseModel):
    """进入调查冻决。"""

    reason: str = Field(min_length=1)
    risk_score: float = Field(ge=0.0, le=1.0)


class InvestigateUnfreezeIn(BaseModel):
    """解除调查冻决（须人闸令牌）。"""

    human_latch_token: str | None = None


class PeakDegradeIn(BaseModel):
    """峰值降级：仅补件+人审队列。"""

    reason: str = Field(min_length=1)

def get_service() -> ClaimsService:
    return _service


def reset_service() -> ClaimsService:
    """测试夹具：重建内存台账并重载条款 KB。"""
    global _service, _kb
    _kb = KnowledgeBase(_KB_ROOT)
    _service = _build_service()
    return _service


def _http_domain_error(exc: ClaimsDomainError) -> HTTPException:
    status = 422
    if exc.error_code in (
        ErrorCode.DOCUMENT_STATUS_FORBIDDEN.value,
        ErrorCode.LATCH_REQUIRED.value,
    ):
        status = 403
    detail: dict[str, Any] = {"error_code": exc.error_code, "message": exc.message}
    if exc.extra:
        detail.update(exc.extra)
    return HTTPException(status_code=status, detail=detail)


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
def evaluate_claim(case_id: str, body: EvaluateIn | None = None) -> dict[str, Any]:
    """触发门禁裁决：材料不齐→一次补件；批单缩责→减赔；齐→通赔建议草案。"""
    assert_tool_allowed("evaluate_claim")
    payload = body or EvaluateIn()
    source_decisions = dict(payload.source_decisions)
    if payload.signal_sources and not source_decisions:
        # 仅声明源列表无结论时，不构成冲突探针
        source_decisions = {}
    try:
        decision = _service.evaluate(
            case_id,
            proposed_deductible=payload.proposed_deductible,
            proposed_ratio=payload.proposed_ratio,
            sensitivity_flags=payload.sensitivity_flags or None,
            source_decisions=source_decisions or None,
            retrieval_profile=payload.retrieval_profile,
            force_reject_with_handbook_only=payload.force_reject_with_handbook_only,
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
    out = decision.to_dict()
    out["case_id"] = case_id
    return out


@app.get("/claims/{case_id}/ledger")
def get_ledger(case_id: str) -> dict[str, Any]:
    """每案审计 ledger：route_id / retrieval_profile / decision_type / validator_score。"""
    assert_tool_allowed("read_ledger")
    try:
        items = _service.list_ledger(case_id)
    except ClaimNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.VALIDATION_FAILED.value,
                "message": f"案件不存在: {exc.case_id}",
            },
        ) from exc
    return {"case_id": case_id, "items": items}


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
    """导出补件/拒赔等文书；拒赔 DRAFT_EXPORT 可无人闸，EXTERNAL_NOTIFY 须人闸。"""
    assert_tool_allowed("export_document")
    try:
        return _service.export_document(
            case_id,
            document_type=body.document_type,
            document_status=body.document_status,
            human_latch_token=body.human_latch_token,
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


@app.post("/claims/{case_id}/human-latch/approve")
def approve_human_latch(case_id: str, body: HumanLatchApproveIn) -> dict[str, Any]:
    """人闸批准：发出 human_latch_token；不触发银企出款。"""
    assert_tool_allowed("approve_human_latch")
    try:
        return _service.approve_human_latch(
            case_id,
            approved_by=body.approved_by,
            second_approver=body.second_approver,
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


@app.post("/claims/{case_id}/human-latch/reject")
def reject_human_latch(case_id: str, body: HumanLatchRejectIn) -> dict[str, Any]:
    """人闸驳回：回编辑态，可再 evaluate 提审。"""
    assert_tool_allowed("reject_human_latch")
    try:
        return _service.reject_human_latch(
            case_id,
            rejected_by=body.rejected_by,
            reason=body.reason,
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


@app.post("/claims/{case_id}/decisions/exgratia")
def decide_exgratia(case_id: str, body: ExgratiaIn) -> dict[str, Any]:
    """通融决定：必闸；伪主险通赔 citation 失败关闭。"""
    assert_tool_allowed("decide_exgratia")
    try:
        decision = _service.decide_exgratia(
            case_id,
            reason=body.reason,
            recommended_amount=body.recommended_amount,
            citations=body.citations,
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
    out = decision.to_dict()
    out["case_id"] = case_id
    return out


@app.post("/claims/{case_id}/decisions/prepay")
def decide_prepay(case_id: str, body: PrepayIn) -> dict[str, Any]:
    """预赔决定：默认必闸。"""
    assert_tool_allowed("decide_prepay")
    try:
        decision = _service.decide_prepay(
            case_id,
            reason=body.reason,
            recommended_amount=body.recommended_amount,
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
    out = decision.to_dict()
    out["case_id"] = case_id
    return out


@app.post("/claims/{case_id}/investigate/enter")
def investigate_enter(case_id: str, body: InvestigateEnterIn) -> dict[str, Any]:
    """进入调查中：自动冻决。"""
    assert_tool_allowed("investigate_enter")
    try:
        decision = _service.enter_investigation(
            case_id,
            reason=body.reason,
            risk_score=body.risk_score,
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
    out = decision.to_dict()
    out["case_id"] = case_id
    return out


@app.post("/claims/{case_id}/investigate/unfreeze")
def investigate_unfreeze(
    case_id: str, body: InvestigateUnfreezeIn | None = None
) -> dict[str, Any]:
    """解除调查冻决：须人闸令牌。"""
    assert_tool_allowed("investigate_unfreeze")
    payload = body or InvestigateUnfreezeIn()
    try:
        return _service.unfreeze_investigation(
            case_id,
            human_latch_token=payload.human_latch_token,
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


@app.post("/claims/{case_id}/peak-degrade")
def peak_degrade(case_id: str, body: PeakDegradeIn) -> dict[str, Any]:
    """峰值降级：仅补件+排队人审，禁止静默通赔。"""
    assert_tool_allowed("peak_degrade")
    try:
        decision = _service.peak_degrade(case_id, reason=body.reason)
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
    out = decision.to_dict()
    out["case_id"] = case_id
    return out


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

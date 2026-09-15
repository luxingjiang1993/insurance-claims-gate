"""FastAPI 外壳：Validator 只能经 HTTP 黑盒验收，不得改产品代码。

Rewrote from: REF-MISSIONS（transfer_api/api.py 换理赔域）；citation 门 REF-CASE-KB；
SC-01 补件/裁决/文书 REF-COURSE-03；SC-02 拒赔分态与人闸 REF-MISSIONS；
SC-03 减赔 REF-COURSE-04；Issue 06 人闸矩阵扩展 REF-MISSIONS；
Issue 08 L2 出款就绪/结案回写 REF-MISSIONS, REF-CASE-FC；
Issue 09 OCR/备注威胁负例 REF-CASE-HYBRID, REF-MISSIONS；
Issue 14 SQLite + 种子登录会话 REF-MISSIONS；
Issue 15 人闸 RBAC 硬门 + S0 负例 REF-MISSIONS；
Issue 16 作业壳列表/详情可读字段 + CORS REF-MISSIONS；
Issue 19 AI 辅助建议降级/关键词/采纳再 evaluate REF-MISSIONS, REF-COURSE-03, REF-CASE-HYBRID, REF-RAG-CY；
Issue 21 本案流水 + 本地 JSONL span（LangSmith 仅配置位）REF-MISSIONS；
Issue 29 评测跑次持久化 + actor 归因 REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR, REF-MISSIONS
Issue 30 评测排行榜排序 REF-CASE-EVAL-ADVISOR, REF-CASE-OPENEVALS, REF-MISSIONS
Issue 32 金标导入/导出钩子 REF-CASE-OPENEVALS, REF-MISSIONS
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from missions.rag import KnowledgeBase
from missions.track_llm_optional.llm_client import LlmCallError

from .auth import AuthError, AuthService
from .error_codes import ErrorCode
from .service import ClaimNotFoundError, ClaimsDomainError, ClaimsService
from .sqlite_store import SqliteCaseStore
from .tools_acl import RolePermissionError, assert_role_allowed, assert_tool_allowed

app = FastAPI(title="Claims Gate API", version="0.1.0")
# 作业壳（Vite 默认 5173）直连 API；无 BFF
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
_KB_ROOT = Path(__file__).resolve().parents[2] / "knowledge_base"
# 持久演示库路径提示：export CLAIMS_GATE_DB=<repo>/data/claims_gate.sqlite
_kb = KnowledgeBase(_KB_ROOT)
_store: SqliteCaseStore | None = None
_auth: AuthService | None = None


def _resolve_db_path(db_path: Path | None) -> Path:
    """解析库路径：显式参数 > CLAIMS_GATE_DB > 临时库（避免 import 污染 data/）。"""
    if db_path is not None:
        return Path(db_path)
    env = os.environ.get("CLAIMS_GATE_DB")
    if env:
        return Path(env)
    fd, name = tempfile.mkstemp(prefix="claims_gate_boot_", suffix=".sqlite")
    os.close(fd)
    path = Path(name)
    path.unlink(missing_ok=True)
    return path


def _build_service(
    db_path: Path | None = None,
) -> tuple[ClaimsService, AuthService, SqliteCaseStore]:
    """重建服务；共享同一 KB 实例，拒赔对外通知经 KB 落库门失败关闭。"""
    path = _resolve_db_path(db_path)
    store = SqliteCaseStore(path)
    svc = ClaimsService(kb=_kb, store=store)

    def _ok(payload: dict[str, Any]) -> bool:
        return _kb.validate_citation(payload).ok

    svc.set_citation_validator(_ok)
    auth = AuthService(store)
    return svc, auth, store


_service, _auth, _store = _build_service()


class CitationValidateRequest(BaseModel):
    """对外可用 citation 最低落库键。"""

    doc_id: str
    clause_item: str
    doc_version: str
    quote: str = ""


class LoginIn(BaseModel):
    """演示登录：种子用户 viewer / adjuster / supervisor。"""

    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class MaterialsIn(BaseModel):
    """补传材料元数据；OCR/备注为用户可控字段，不得改写人闸。"""

    material_codes: list[str] = Field(min_length=1)
    image_ids: list[str] = Field(default_factory=list)
    ocr_text: str | None = None
    customer_remark: str | None = None


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
    # 敏感场景上浮（诉讼/信访/媒体等）— 运营侧结构化字段，非 OCR/备注
    sensitivity_flags: list[str] = Field(default_factory=list)
    # Issue 07：Router 冲突探针 / handbook 独撑拒赔探针
    signal_sources: list[str] = Field(default_factory=list)
    source_decisions: dict[str, str] = Field(default_factory=dict)
    retrieval_profile: str | None = None
    force_reject_with_handbook_only: bool = False
    # Issue 09：用户可控文本；收纳可观察，不得翻转人闸 / payout_ready
    ocr_text: str | None = None
    customer_remark: str | None = None


class AssistIn(BaseModel):
    """AI 辅助建议请求；显式触发，无 Key 时明确降级。"""

    query: str = Field(min_length=1)
    retrieval_profile: str | None = None
    top_k: int = Field(default=3, ge=1, le=10)


class AssistAdoptIn(BaseModel):
    """采纳辅助建议：citation 须过 Schema 槽 + 三联门；再过规则 evaluate。"""

    assist_invocation_id: str | None = None
    draft_text: str | None = None
    suggested_stance: str | None = None
    retrieval_profile: str | None = None
    # H3：采纳请求须携带 citation；非法 / 缺槽不可采纳
    citations: list[dict[str, Any]] = Field(default_factory=list)
    proposed_deductible: int | None = None
    proposed_ratio: float | None = None
    sensitivity_flags: list[str] = Field(default_factory=list)
    source_decisions: dict[str, str] = Field(default_factory=dict)
    force_reject_with_handbook_only: bool = False
    ocr_text: str | None = None
    customer_remark: str | None = None


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


class L2PayoutReadyIn(BaseModel):
    """L2 出款就绪回写：须人闸令牌；不触发银企。"""

    human_latch_token: str | None = None


class L2CloseIn(BaseModel):
    """L2 结案回写：不含自动支付指令。"""

    close_opinion: str = Field(min_length=1)


class EvalRunCreateIn(BaseModel):
    """触发评测跑次：可选实验名；actor 取自会话。"""

    experiment_name: str | None = None
    dataset_name: str | None = None


class GoldLabelRecordIn(BaseModel):
    """金标/薄切片单行：必须关联案件键；薄切片可带双标 annotation。"""

    case_id: str = Field(min_length=1)
    inputs: dict[str, Any] = Field(default_factory=dict)
    expected: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""
    annotation: dict[str, Any] | None = None


class GoldLabelImportIn(BaseModel):
    """金标/薄切片导入钩子；禁止把运营完成写成已交付。"""

    model_config = {"extra": "allow", "populate_by_name": True}

    dataset_id: str = Field(min_length=1)
    records: list[GoldLabelRecordIn]
    gold_ops_complete: bool = False
    dual_annotation_workflow: bool = False
    is_gold_thin_slice: bool = False
    docs_note: str | None = None
    dataset_schema: str | None = None
    # JSON 字段名 schema（避免与 BaseModel.schema 方法名冲突用 alias）
    schema_id: str | None = Field(default=None, alias="schema")
    rewrote_from: str | None = None


def get_service() -> ClaimsService:
    return _service


def get_auth() -> AuthService:
    assert _auth is not None
    return _auth


def get_store() -> SqliteCaseStore:
    assert _store is not None
    return _store


def reset_service(db_path: Path | None = None) -> ClaimsService:
    """测试夹具：重建 SQLite 台账并重载条款 KB。

    - 未传 db_path：新建临时库，保证用例隔离。
    - 传入已有路径：同库重开（模拟进程重启后续读）。
    """
    global _service, _kb, _store, _auth
    if _store is not None:
        _store.close()
    _kb = KnowledgeBase(_KB_ROOT)
    if db_path is None:
        fd, name = tempfile.mkstemp(prefix="claims_gate_", suffix=".sqlite")
        os.close(fd)
        path = Path(name)
        path.unlink(missing_ok=True)
        _service, _auth, _store = _build_service(db_path=path)
    else:
        _service, _auth, _store = _build_service(db_path=Path(db_path))
    return _service


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None


def _http_auth_error(exc: AuthError) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={"error_code": exc.error_code, "message": exc.message},
    )


def _http_domain_error(exc: ClaimsDomainError) -> HTTPException:
    status = 422
    if exc.error_code in (
        ErrorCode.DOCUMENT_STATUS_FORBIDDEN.value,
        ErrorCode.LATCH_REQUIRED.value,
        ErrorCode.PERMISSION_DENIED.value,
    ):
        status = 403
    detail: dict[str, Any] = {"error_code": exc.error_code, "message": exc.message}
    if exc.extra:
        detail.update(exc.extra)
    return HTTPException(status_code=status, detail=detail)


def _authorize(tool_name: str, authorization: str | None = None) -> dict[str, Any] | None:
    """工具白名单 + 角色硬门；返回当前会话（若有）。"""
    assert_tool_allowed(tool_name)
    token = _bearer_token(authorization)
    session: dict[str, Any] | None = None
    role: str | None = None
    if token:
        try:
            session = get_auth().resolve_session(token)
            role = str(session["role"])
        except AuthError as exc:
            raise _http_auth_error(exc) from exc
    try:
        assert_role_allowed(tool_name, role)
    except RolePermissionError as exc:
        if exc.missing_auth:
            raise HTTPException(
                status_code=401,
                detail={
                    "error_code": ErrorCode.AUTH_FAILED.value,
                    "message": str(exc),
                },
            ) from exc
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": ErrorCode.PERMISSION_DENIED.value,
                "message": str(exc),
            },
        ) from exc
    return session


@app.get("/")
def root() -> dict:
    """入口说明：浏览器打开根路径时返回可用入口，避免误判服务未启动。"""
    return {
        "product": "Claims Gate",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
        "hint": "试用夹具: GET /claims/CLM-SC01-001 ；登录: POST /auth/login ；OpenAPI: /docs",
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "inference_track": "deterministic"}


@app.post("/auth/login")
def auth_login(body: LoginIn) -> dict[str, Any]:
    """种子三角色登录；返回会话令牌与角色。"""
    _authorize("auth_login")
    try:
        return get_auth().login(body.username, body.password)
    except AuthError as exc:
        raise _http_auth_error(exc) from exc


@app.get("/auth/me")
def auth_me(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """解析当前会话角色。"""
    _authorize("auth_me", authorization)
    try:
        return get_auth().resolve_session(_bearer_token(authorization))
    except AuthError as exc:
        raise _http_auth_error(exc) from exc


@app.post("/auth/logout")
def auth_logout(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """注销当前会话。"""
    _authorize("auth_logout", authorization)
    return get_auth().logout(_bearer_token(authorization))


@app.get("/claims")
def list_claims(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """持久化案件列表摘要（作业壳只读浏览）。"""
    _authorize("list_gate_status", authorization)
    return {"items": _service.list_claims()}


@app.get("/claims/{case_id}")
def get_claim(
    case_id: str, authorization: str | None = Header(default=None)
) -> dict:
    """L1 只读案件头；含门禁可读字段 document_status / payout_ready。"""
    _authorize("read_claim_header", authorization)
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
    summary = ClaimsService.claim_browse_summary(case)
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
        "document_status": summary["document_status"],
        "payout_ready": summary["payout_ready"],
        "ocr_text": case.ocr_text,
        "customer_remark": case.customer_remark,
    }


@app.get("/claims/{case_id}/latch-events")
def get_latch_events(
    case_id: str, authorization: str | None = Header(default=None)
) -> dict[str, Any]:
    """人闸事件摘要（批准/驳回可回放）。"""
    _authorize("read_latch_events", authorization)
    try:
        items = _service.list_latch_events(case_id)
    except ClaimNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.VALIDATION_FAILED.value,
                "message": f"案件不存在: {exc.case_id}",
            },
        ) from exc
    return {"case_id": case_id, "items": items}


@app.post("/claims/{case_id}/evaluate")
def evaluate_claim(
    case_id: str,
    body: EvaluateIn | None = None,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """触发门禁裁决：材料不齐→一次补件；批单缩责→减赔；齐→通赔建议草案。"""
    _authorize("evaluate_claim", authorization)
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
            ocr_text=payload.ocr_text,
            customer_remark=payload.customer_remark,
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


@app.post("/claims/{case_id}/assist")
def assist_claim(
    case_id: str,
    body: AssistIn,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """AI 辅助建议：有 Key 可真调用；无 Key 明确降级；不写 payout_ready / 人闸令牌。"""
    _authorize("assist_claim", authorization)
    try:
        return _service.assist(
            case_id,
            query=body.query,
            retrieval_profile=body.retrieval_profile,
            top_k=body.top_k,
            enable_llm=True,
        )
    except ClaimNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.VALIDATION_FAILED.value,
                "message": f"案件不存在: {exc.case_id}",
            },
        ) from exc
    except LlmCallError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error_code": ErrorCode.VALIDATION_FAILED.value,
                "message": str(exc),
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": ErrorCode.VALIDATION_FAILED.value,
                "message": str(exc),
            },
        ) from exc


@app.post("/claims/{case_id}/assist/adopt")
def adopt_assist(
    case_id: str,
    body: AssistAdoptIn,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """采纳辅助建议：citation Schema+三联门通过后，唯一权威更新路径是再跑 evaluate。"""
    _authorize("adopt_assist", authorization)
    try:
        decision = _service.adopt_assist(
            case_id,
            draft_text=body.draft_text,
            suggested_stance=body.suggested_stance,
            retrieval_profile=body.retrieval_profile,
            assist_invocation_id=body.assist_invocation_id,
            citations=body.citations,
            proposed_deductible=body.proposed_deductible,
            proposed_ratio=body.proposed_ratio,
            sensitivity_flags=body.sensitivity_flags or None,
            source_decisions=body.source_decisions or None,
            ocr_text=body.ocr_text,
            customer_remark=body.customer_remark,
            force_reject_with_handbook_only=body.force_reject_with_handbook_only,
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
def get_ledger(
    case_id: str, authorization: str | None = Header(default=None)
) -> dict[str, Any]:
    """每案审计 ledger：route_id / retrieval_profile / decision_type / validator_score。"""
    _authorize("read_ledger", authorization)
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
def get_decision(
    case_id: str, authorization: str | None = Header(default=None)
) -> dict[str, Any]:
    """查询最近裁决草案。"""
    _authorize("read_decision", authorization)
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
def register_materials(
    case_id: str,
    body: MaterialsIn,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """提交补件材料后登记；需再次 evaluate 重评。"""
    _authorize("register_materials", authorization)
    try:
        case = _service.register_materials(
            case_id,
            material_codes=body.material_codes,
            image_ids=body.image_ids,
            ocr_text=body.ocr_text,
            customer_remark=body.customer_remark,
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
        "ocr_text": case.ocr_text,
        "customer_remark": case.customer_remark,
    }


@app.post("/claims/{case_id}/supplement/notify")
def notify_supplement(
    case_id: str,
    body: SupplementNotifyIn,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """发出补件通知；同 hash 拆轮必失败。"""
    _authorize("notify_supplement", authorization)
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
def export_document(
    case_id: str,
    body: DocumentExportIn,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """导出补件/拒赔等文书；拒赔 DRAFT_EXPORT 可无人闸，EXTERNAL_NOTIFY 须人闸。"""
    _authorize("export_document", authorization)
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
def approve_human_latch(
    case_id: str,
    body: HumanLatchApproveIn,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """人闸批准：发出 human_latch_token；仅 supervisor；不触发银企出款。"""
    _authorize("approve_human_latch", authorization)
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
def reject_human_latch(
    case_id: str,
    body: HumanLatchRejectIn,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """人闸驳回：仅 supervisor；回编辑态，可再 evaluate 提审。"""
    _authorize("reject_human_latch", authorization)
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
def decide_exgratia(
    case_id: str,
    body: ExgratiaIn,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """通融决定：必闸；伪主险通赔 citation 失败关闭。"""
    _authorize("decide_exgratia", authorization)
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
def decide_prepay(
    case_id: str,
    body: PrepayIn,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """预赔决定：默认必闸。"""
    _authorize("decide_prepay", authorization)
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
def investigate_enter(
    case_id: str,
    body: InvestigateEnterIn,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """进入调查中：自动冻决。"""
    _authorize("investigate_enter", authorization)
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
    case_id: str,
    body: InvestigateUnfreezeIn | None = None,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """解除调查冻决：须人闸令牌。"""
    _authorize("investigate_unfreeze", authorization)
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
def peak_degrade(
    case_id: str,
    body: PeakDegradeIn,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """峰值降级：仅补件+排队人审，禁止静默通赔。"""
    _authorize("peak_degrade", authorization)
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


@app.post("/claims/{case_id}/l2/payout-ready")
def l2_payout_ready(
    case_id: str,
    body: L2PayoutReadyIn | None = None,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """L2 模拟回写出款就绪：人闸后置 PAYOUT_READY；不触发银企支付。"""
    _authorize("l2_payout_ready", authorization)
    payload = body or L2PayoutReadyIn()
    try:
        return _service.writeback_payout_ready(
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


@app.post("/claims/{case_id}/l2/close")
def l2_close(
    case_id: str,
    body: L2CloseIn,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """L2 结案回写：CLOSED 与出款解耦；载荷不含自动支付指令。"""
    _authorize("l2_close", authorization)
    try:
        return _service.writeback_close(case_id, close_opinion=body.close_opinion)
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
def validate_citation(
    body: CitationValidateRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """条款项级落库门：doc_id + clause_item + doc_version 三联命中。"""
    _authorize("validate_citation", authorization)
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


@app.post("/eval/runs")
def create_eval_run(
    body: EvalRunCreateIn | None = None,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """触发 OpenEval 旁路跑次并持久化；actor_user_id = 会话用户（W0 演示用户）。

    旁路：失败不改写人闸；不进 machine_check；无 LangSmith 时 langsmith_degraded。
    """
    from missions.eval_run_persist import trigger_and_persist_eval_run
    from missions.openeval_langsmith import DEFAULT_DATASET_NAME

    session = _authorize("create_eval_run", authorization)
    if session is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": ErrorCode.AUTH_FAILED.value,
                "message": "触发评测跑次须登录会话",
            },
        )
    payload = body or EvalRunCreateIn()
    # 同进程黑盒：沿用 OpenEval 旁路 TestClient 接缝（非合门禁）
    http = TestClient(app)
    record = trigger_and_persist_eval_run(
        http,
        get_store(),
        actor_user_id=str(session["username"]),
        experiment_name=payload.experiment_name,
        dataset_name=payload.dataset_name or DEFAULT_DATASET_NAME,
    )
    return record.to_dict()


@app.get("/eval/runs")
def list_eval_runs(
    actor_user_id: str | None = None,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """列出已持久化评测跑次；可按 actor_user_id 过滤（多人互不覆盖）。"""
    from missions.eval_run_persist import list_persisted_eval_runs

    session = _authorize("list_eval_runs", authorization)
    if session is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": ErrorCode.AUTH_FAILED.value,
                "message": "查看评测跑次须登录会话",
            },
        )
    runs = list_persisted_eval_runs(get_store(), actor_user_id=actor_user_id)
    return {
        "runs": [r.to_dict() for r in runs],
        "filter_actor_user_id": actor_user_id,
        "gate_role": "bypass_not_machine_check",
        "blocks_track_a_gate": False,
    }


@app.get("/eval/leaderboard")
def list_eval_leaderboard(
    order: str = "desc",
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """评测排行榜：实验名 / 主指标 / 时间 / 提交者；可按主指标排序。

    单一真源：本地 SQLite eval_runs（不读 LangSmith 实验 API）。
    旁路：榜分不进 machine_check；不改写人闸。
    """
    from missions.eval_leaderboard import (
        DATA_SOURCE,
        PRIMARY_METRIC_NAME,
        build_leaderboard,
    )

    session = _authorize("list_eval_leaderboard", authorization)
    if session is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": ErrorCode.AUTH_FAILED.value,
                "message": "查看评测排行榜须登录会话",
            },
        )
    sort_order = (order or "desc").lower()
    if sort_order not in ("asc", "desc"):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": ErrorCode.VALIDATION_FAILED.value,
                "message": "order 仅支持 asc 或 desc",
            },
        )
    rows = build_leaderboard(
        get_store(),
        sort_by="primary_metric",
        order=sort_order,  # type: ignore[arg-type]
    )
    return {
        "rows": [r.to_dict() for r in rows],
        "sort_by": "primary_metric",
        "order": sort_order,
        "primary_metric_name": PRIMARY_METRIC_NAME,
        "data_source": DATA_SOURCE,
        "gate_role": "bypass_not_machine_check",
        "blocks_track_a_gate": False,
    }


@app.post("/eval/gold-labels/import")
def import_gold_labels(
    body: GoldLabelImportIn,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """金标/薄切片导入：记录须含 case_id；薄切片须双标+第三人角色占位。

    旁路：失败不改写人闸；不进 machine_check；不得宣称金标已达标或 ≥300。
    """
    from missions.gold_label_io import GoldLabelIoError, import_dataset, parse_dataset

    session = _authorize("import_gold_labels", authorization)
    if session is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": ErrorCode.AUTH_FAILED.value,
                "message": "导入金标数据集须登录会话",
            },
        )
    payload = body.model_dump(by_alias=True)
    if payload.get("dataset_schema") and not payload.get("schema"):
        payload["schema"] = payload["dataset_schema"]
    payload.pop("schema_id", None)
    try:
        dataset = parse_dataset(payload)
        result = import_dataset(
            get_store(),
            dataset,
            actor_user_id=str(session["username"]),
        )
    except GoldLabelIoError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": ErrorCode.VALIDATION_FAILED.value,
                "message": str(exc),
            },
        ) from exc
    return result.to_dict()


@app.get("/eval/gold-labels/export")
def export_gold_labels(
    dataset_id: str | None = None,
    case_id: str | None = None,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """金标/薄切片导出：可按 dataset_id / case_id 过滤；附带 h4_status。"""
    from missions.gold_label_io import EVAL_GATE_ROLE, export_dataset

    session = _authorize("export_gold_labels", authorization)
    if session is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": ErrorCode.AUTH_FAILED.value,
                "message": "导出金标数据集须登录会话",
            },
        )
    dataset = export_dataset(
        get_store(),
        dataset_id=dataset_id,
        case_id=case_id,
    )
    out = dataset.to_dict()
    out["gate_role"] = EVAL_GATE_ROLE
    out["blocks_track_a_gate"] = False
    out["filter_dataset_id"] = dataset_id
    out["filter_case_id"] = case_id
    return out

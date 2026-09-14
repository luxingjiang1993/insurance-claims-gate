"""理赔案件服务：材料齐全断言、一次补件、通赔建议、除外拒赔、效力栈减赔、人闸矩阵、Router/ledger。

Rewrote from: REF-MISSIONS（transfer_api/service.py 换垂直）；补件法义 REF-COURSE-03；
SC-02 拒赔分态 REF-MISSIONS；效力栈减赔 / calc_steps REF-CASE-KB, REF-COURSE-04；
金额档/通融/预赔/调查冻决/峰值降级 REF-MISSIONS（limits 表驱动换域，阈值取 PRD §7）；
Router 策略表 + ledger REF-COURSE-12, REF-CASE-HYBRID, REF-MISSIONS；
L2 出款就绪/结案回写模拟 REF-MISSIONS, REF-CASE-FC；
Issue 14 SQLite 持久化 + 种子 RBAC 登录 REF-MISSIONS；
Issue 19 AI 辅助建议降级/关键词/采纳再 evaluate REF-MISSIONS, REF-COURSE-03, REF-CASE-HYBRID, REF-RAG-CY；
Issue 21 本案流水 + 本地 JSONL span（LangSmith 仅配置位）REF-MISSIONS
"""

from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from missions.rag import KnowledgeBase
from missions.router import (
    CaseSignals,
    RouteDecision,
    assert_reject_not_handbook_alone,
    route as route_case,
)
from missions.track_llm_optional.pipeline import draft_assist

from .error_codes import ErrorCode
from .latch_matrix import is_fake_exgratia_clause_approve_citation, resolve_latch
from .local_trace import emit_span
from .user_text import absorb_user_controlled_text
from .models_domain import (
    ClaimCase,
    CoreMasterSnapshot,
    DecisionDraft,
    LatchEvent,
    LedgerEntry,
    SupplementItem,
)
from .sqlite_store import SqliteCaseStore

# 允许进入出款就绪的裁决类型（拒赔/补件/调查不得 PAYOUT_READY）
_PAYOUT_ELIGIBLE_DECISIONS: frozenset[str] = frozenset(
    {
        "approve_recommend",
        "reduce",
        "exgratia",
        "prepay",
    }
)


def _span_name_for_ledger(decision_type: str) -> str | None:
    """ledger decision_type → 本地 span 名；非关键动作不写 span。"""
    if decision_type == "assist_suggestion":
        return "assist"
    if decision_type.startswith("human_latch_"):
        return "latch"
    # L2 回写等非 W0 关键排障路径：不导出为 evaluate
    if decision_type.startswith("l2_"):
        return None
    return "evaluate"


def _ledger_retrieval_profile(case: ClaimCase) -> str:
    """ledger 用检索画像；缺省 clause_v_current。"""
    if case.latest_decision and case.latest_decision.retrieval_profile:
        return case.latest_decision.retrieval_profile
    return "clause_v_current"

# 《保险法》第22条一次性补正义务 — 法务审定锚点文案（轨 A 固定常量）
LEGAL_BASIS_ARTICLE_22 = (
    "依据《中华人民共和国保险法》第二十二条，保险人认为有关的证明和资料不完整的，"
    "应当及时一次性通知投保人、被保险人或者受益人补充提供。"
)

APPEAL_PATH_DEFAULT = "申诉/人工复核：拨打客服热线或通过保司线上异议工单提交；亦可向当地银保监局/消保渠道反映。本系统不构成不可申诉终局拒赔。"

# SC-01 夹具：个人意外医疗案必备材料目录（确定性规则）
REQUIRED_MATERIALS: dict[str, SupplementItem] = {
    "ID_CARD": SupplementItem(
        code="ID_CARD",
        name_zh="投保人/被保险人身份证件",
        required=True,
        example="身份证正反面清晰影像",
    ),
    "CLAIM_FORM": SupplementItem(
        code="CLAIM_FORM",
        name_zh="理赔申请书",
        required=True,
        example="签字齐全的理赔申请书扫描件",
    ),
    "MEDICAL_INVOICE": SupplementItem(
        code="MEDICAL_INVOICE",
        name_zh="医疗费用发票",
        required=True,
        example="医院开具的医疗费发票原件或电子发票",
    ),
    "DIAGNOSIS_REPORT": SupplementItem(
        code="DIAGNOSIS_REPORT",
        name_zh="诊断证明/病历",
        required=True,
        example="门诊病历或出院诊断证明",
    ),
}

# 材料码与预置影像 ID 的映射（夹具）
_SEED_IMAGE_TO_MATERIAL: dict[str, str] = {
    "IMG-ID-CARD": "ID_CARD",
    "IMG-CLAIM-FORM": "CLAIM_FORM",
}

_DEDUCT_RE = re.compile(r"免赔额\s*(\d+)\s*元")
_RATIO_RE = re.compile(r"赔付比例\s*(\d+)\s*%")

# SC-02 除外引用键
_SC02_EXCL = ("PA-ACC-MAIN", "ART-5-EXCL", "2024.1")
# SC-03 效力栈理算引用键
_SC03_MAIN_DEDUCT = ("PA-ACC-MAIN", "ART-6-DEDUCT", "2024.1")
_SC03_ENDO_DEDUCT = ("PA-ACC-END-001", "END-2-DEDUCT", "2025.3")

_DEFAULT_KB_ROOT = Path(__file__).resolve().parents[2] / "knowledge_base"

CitationValidator = Callable[[dict[str, Any]], bool]


class ClaimNotFoundError(LookupError):
    def __init__(self, case_id: str) -> None:
        super().__init__(case_id)
        self.case_id = case_id
        self.error_code = ErrorCode.VALIDATION_FAILED.value


class ClaimsDomainError(Exception):
    """领域拒绝：映射到 HTTP 错误码。"""

    def __init__(
        self,
        error_code: str,
        message: str,
        *,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.extra = extra or {}


class ClaimsService:
    """案件台账（默认 SQLite）；SC-01 缺发票；SC-02 疾病摔伤除外；SC-03 批单缩责减赔；人闸矩阵。"""

    def __init__(
        self,
        kb: KnowledgeBase | None = None,
        store: SqliteCaseStore | None = None,
    ) -> None:
        self._kb = kb if kb is not None else KnowledgeBase(_DEFAULT_KB_ROOT)
        self._citation_validator: CitationValidator | None = None
        self._store = store
        # 银企/支付适配器调用计数：L2 回写路径禁止递增（Demo 可观察）
        self.payment_adapter_calls: int = 0
        if store is not None and store.count_cases() > 0:
            self._cases = store.load_all_cases()
        else:
            self._cases = {}
            self._seed()
            if store is not None:
                store.save_all_cases(self._cases)

    def set_citation_validator(self, validator: CitationValidator) -> None:
        """注入条款落库校验（对外通知失败关闭）。"""
        self._citation_validator = validator

    def _persist(self, case: ClaimCase) -> None:
        """将单案写入 SQLite（若已注入 store）。"""
        if self._store is not None:
            self._store.save_case(case)

    def _record_latch_event(self, event: LatchEvent) -> None:
        """追加人闸事件并落库。"""
        case = self.get_claim(event.case_id)
        case.latch_events.append(event)
        if self._store is not None:
            self._store.append_latch_event(event)
        self._persist(case)

    def list_latch_events(self, case_id: str) -> list[dict[str, Any]]:
        """查询人闸事件；有 store 时以表为唯一权威。"""
        case = self.get_claim(case_id)
        if self._store is not None:
            return [e.to_dict() for e in self._store.list_latch_events(case_id)]
        return [e.to_dict() for e in case.latch_events]

    def _seed_complete_case(
        self,
        *,
        case_id: str,
        policy_no: str,
        claim_amount_claimed: int,
        endorsement_flags: list[str] | None = None,
        loss_cause: str = "accident",
    ) -> ClaimCase:
        """材料齐全夹具。"""
        all_codes = list(REQUIRED_MATERIALS.keys())
        flags = list(endorsement_flags or [])
        case = ClaimCase(
            case_id=case_id,
            policy_no=policy_no,
            product_code="PA-ACCIDENT-MED",
            clause_version="PA-ACC-2024.1",
            loss_date="2026-08-15",
            claim_amount_claimed=claim_amount_claimed,
            endorsement_flags=flags,
            image_ids=[f"IMG-{c}" for c in all_codes],
            material_codes=list(all_codes),
            loss_cause=loss_cause,
            gate_status="MATERIALS_INTAKE",
            inference_track="deterministic",
            core_master=CoreMasterSnapshot(
                case_id=case_id,
                policy_no=policy_no,
                product_code="PA-ACCIDENT-MED",
                clause_version="PA-ACC-2024.1",
                endorsement_flags=list(flags),
            ),
        )
        self._cases[case.case_id] = case
        return case

    def _seed(self) -> None:
        image_ids = ["IMG-ID-CARD", "IMG-CLAIM-FORM"]
        material_codes = [
            _SEED_IMAGE_TO_MATERIAL[i] for i in image_ids if i in _SEED_IMAGE_TO_MATERIAL
        ]
        case = ClaimCase(
            case_id="CLM-SC01-001",
            policy_no="PA-2026-000188",
            product_code="PA-ACCIDENT-MED",
            clause_version="PA-ACC-2024.1",
            loss_date="2026-08-01",
            claim_amount_claimed=350000,
            endorsement_flags=[],
            image_ids=list(image_ids),
            material_codes=list(material_codes),
            loss_cause="accident",
            gate_status="MATERIALS_INTAKE",
            inference_track="deterministic",
            core_master=CoreMasterSnapshot(
                case_id="CLM-SC01-001",
                policy_no="PA-2026-000188",
                product_code="PA-ACCIDENT-MED",
                clause_version="PA-ACC-2024.1",
                endorsement_flags=[],
            ),
        )
        self._cases[case.case_id] = case

        # SC-02：材料齐全 + 疾病摔伤除外
        self._seed_complete_case(
            case_id="CLM-SC02-001",
            policy_no="PA-2026-000202",
            claim_amount_claimed=280000,
            loss_cause="disease_fall",
        )

        # SC-03：材料齐全 + 批单缩责，索赔金额 10000 元（确定性理算）
        self._seed_complete_case(
            case_id="CLM-SC03-001",
            policy_no="PA-2026-000303",
            claim_amount_claimed=10000,
            endorsement_flags=["PA-ACC-END-001"],
        )

        # Issue 06：金额档 / 通融 / 调查夹具
        self._seed_complete_case(
            case_id="CLM-AMT-A-001",
            policy_no="PA-2026-000801",
            claim_amount_claimed=8000,
        )
        self._seed_complete_case(
            case_id="CLM-AMT-C-001",
            policy_no="PA-2026-000802",
            claim_amount_claimed=80000,
        )
        self._seed_complete_case(
            case_id="CLM-AMT-C-REDUCE-001",
            policy_no="PA-2026-000803",
            claim_amount_claimed=100000,
            endorsement_flags=["PA-ACC-END-001"],
        )
        self._seed_complete_case(
            case_id="CLM-LATCH-BASE-001",
            policy_no="PA-2026-000804",
            claim_amount_claimed=12000,
        )

        # Issue 08：主数据不一致夹具（案件侧与核心快照保单号不一致）
        mismatch = self._seed_complete_case(
            case_id="CLM-MISMATCH-001",
            policy_no="PA-2026-CLAIM-SIDE",
            claim_amount_claimed=80000,
        )
        assert mismatch.core_master is not None
        mismatch.core_master = CoreMasterSnapshot(
            case_id="CLM-MISMATCH-001",
            policy_no="PA-2026-CORE-OTHER",
            product_code=mismatch.product_code,
            clause_version=mismatch.clause_version,
            endorsement_flags=list(mismatch.endorsement_flags),
        )

    def _attach_latch_fields(
        self,
        decision: DecisionDraft,
        case: ClaimCase,
        recommended_amount: int,
    ) -> DecisionDraft:
        """按 PRD §7 矩阵写入人闸可观察字段。"""
        req = resolve_latch(
            decision.decision_type,
            recommended_amount,
            sensitivity_flags=case.sensitivity_flags,
        )
        decision.amount_tier = req.amount_tier
        decision.latch_tier = req.latch_tier
        decision.human_latch_required = req.human_latch_required
        decision.dual_token_required = req.dual_token_required
        decision.latch_level_label = req.latch_level_label
        decision.recommended_payout_amount = req.recommended_payout_amount
        decision.freeze_active = case.freeze_active
        decision.peak_degraded = case.peak_degraded
        decision.payout_ready = False
        return decision

    def _append_ledger(
        self,
        case: ClaimCase,
        *,
        route_id: str,
        retrieval_profile: str,
        decision_type: str,
        validator_score: float,
        arbitration_winner: str | None = None,
    ) -> LedgerEntry:
        """写入每案 ledger（最新在前）；可选本地 JSONL span。"""
        entry = LedgerEntry(
            case_id=case.case_id,
            route_id=route_id,
            retrieval_profile=retrieval_profile,
            decision_type=decision_type,
            validator_score=validator_score,
            ts=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            arbitration_winner=arbitration_winner,
        )
        case.ledger.insert(0, entry)
        span_name = _span_name_for_ledger(decision_type)
        if span_name is not None:
            emit_span(
                span_name,
                case_id=case.case_id,
                attributes={
                    "route_id": route_id,
                    "retrieval_profile": retrieval_profile,
                    "decision_type": decision_type,
                    "validator_score": validator_score,
                    "arbitration_winner": arbitration_winner,
                },
            )
        return entry

    def _stamp_route(
        self,
        decision: DecisionDraft,
        routed: RouteDecision,
        *,
        validator_score: float = 1.0,
    ) -> DecisionDraft:
        """裁决草案挂上 Router 可观察字段。"""
        decision.route_id = routed.route_id
        decision.retrieval_profile = routed.retrieval_profile
        decision.validator_score = validator_score
        return decision

    def list_ledger(self, case_id: str) -> list[dict[str, Any]]:
        """查询案件 ledger（最新在前）。"""
        case = self.get_claim(case_id)
        return [e.to_dict() for e in case.ledger]

    def get_claim(self, case_id: str) -> ClaimCase:
        case = self._cases.get(case_id)
        if case is None:
            raise ClaimNotFoundError(case_id)
        return case

    def list_claims(self) -> list[dict[str, Any]]:
        """案件列表摘要（作业壳只读浏览）；按 case_id 排序。"""
        items: list[dict[str, Any]] = []
        for case_id in sorted(self._cases.keys()):
            case = self._cases[case_id]
            items.append(self.claim_browse_summary(case))
        return items

    @staticmethod
    def claim_browse_summary(case: ClaimCase) -> dict[str, Any]:
        """列表/详情共用的门禁可读字段。"""
        decision = case.latest_decision
        return {
            "case_id": case.case_id,
            "policy_no": case.policy_no,
            "product_code": case.product_code,
            "claim_amount_claimed": case.claim_amount_claimed,
            "gate_status": case.gate_status,
            "inference_track": case.inference_track,
            "document_status": decision.document_status if decision else None,
            "payout_ready": bool(decision.payout_ready) if decision else False,
        }

    def _missing_items(self, case: ClaimCase) -> list[SupplementItem]:
        present = set(case.material_codes)
        return [
            item
            for code, item in REQUIRED_MATERIALS.items()
            if code not in present
        ]

    @staticmethod
    def _one_shot_hash(codes: list[str]) -> str:
        """清单指纹：排序后稳定哈希，同缺项集合同 hash。"""
        payload = "|".join(sorted(codes))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _parse_deduct_ratio(clause_text: str) -> tuple[int, float]:
        """从条款正文解析免赔额与赔付比例；缺字段则失败关闭。"""
        dm = _DEDUCT_RE.search(clause_text)
        rm = _RATIO_RE.search(clause_text)
        if not dm or not rm:
            raise ClaimsDomainError(
                ErrorCode.VALIDATION_FAILED.value,
                "条款未载明可解析的免赔额或赔付比例，禁止静默改数",
            )
        deductible = int(dm.group(1))
        ratio = int(rm.group(1)) / 100.0
        return deductible, ratio

    def _citation_dict(
        self,
        doc_id: str,
        clause_item: str,
        doc_version: str,
        *,
        overridden_by: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        chunk = self._kb.resolve_clause(doc_id, clause_item, doc_version)
        if chunk is None:
            raise ClaimsDomainError(
                ErrorCode.CITATION_NOT_IN_KB.value,
                f"引用未落库: {doc_id}/{clause_item}/{doc_version}",
            )
        body: dict[str, Any] = {
            "doc_id": chunk.doc_id,
            "clause_item": chunk.clause_item,
            "doc_version": chunk.doc_version,
            "effective_date": chunk.effective_date,
            "authority_rank": chunk.authority_rank,
            "quote": chunk.text[:160],
            "chunk_id": chunk.chunk_id,
            "clause_id": chunk.clause_id,
            "score": 1.0,
        }
        if overridden_by is not None:
            body["overridden_by"] = overridden_by
        return body

    def _assert_citations_in_kb(self, citations: list[dict[str, Any]]) -> None:
        """对外通知前：须有引用且每条 citation 过落库门。"""
        if not citations:
            raise ClaimsDomainError(
                ErrorCode.VALIDATION_FAILED.value,
                "拒赔对外通知缺少条款项引用",
            )
        if self._citation_validator is None:
            for c in citations:
                hit = self._kb.resolve_clause(
                    str(c.get("doc_id") or ""),
                    str(c.get("clause_item") or ""),
                    str(c.get("doc_version") or ""),
                )
                if hit is None:
                    raise ClaimsDomainError(
                        ErrorCode.CITATION_NOT_IN_KB.value,
                        "对外通知引用未落库",
                    )
            return
        for c in citations:
            if not self._citation_validator(
                {
                    "doc_id": c.get("doc_id", ""),
                    "clause_item": c.get("clause_item", ""),
                    "doc_version": c.get("doc_version", ""),
                    "quote": c.get("quote", ""),
                }
            ):
                raise ClaimsDomainError(
                    ErrorCode.CITATION_NOT_IN_KB.value,
                    "对外通知引用未落库",
                )

    def _build_reduction_calc(
        self,
        claimed: int,
        deductible: int,
        ratio: float,
        source_clause_item: str,
    ) -> list[dict[str, Any]]:
        after = claimed - deductible
        if after < 0:
            after = 0
        result = int(round(after * ratio))
        return [
            {
                "step": "claimed",
                "label": "索赔金额",
                "value": claimed,
                "unit": "CNY",
            },
            {
                "step": "deductible",
                "label": "免赔额",
                "value": deductible,
                "unit": "CNY",
                "source_clause_item": source_clause_item,
            },
            {
                "step": "after_deductible",
                "label": "扣除免赔后",
                "value": after,
                "unit": "CNY",
                "formula": f"{claimed}-{deductible}",
            },
            {
                "step": "ratio",
                "label": "赔付比例",
                "value": ratio,
                "source_clause_item": source_clause_item,
            },
            {
                "step": "result",
                "label": "建议赔付",
                "value": result,
                "unit": "CNY",
                "formula": f"{after}*{ratio}",
            },
        ]

    def _evaluate_rejection(
        self,
        case: ClaimCase,
        *,
        routed: RouteDecision | None = None,
    ) -> DecisionDraft:
        """SC-02：疾病摔伤除外 → 拒赔草案（无人闸前不得 EXTERNAL_NOTIFY）。"""
        doc_id, clause_item, doc_version = _SC02_EXCL
        citation = self._citation_dict(doc_id, clause_item, doc_version)
        reason = (
            "出险原因为疾病导致的摔伤，属于主险责任免除范围，"
            "建议出具拒赔草案；对外通知前须人闸批准。"
        )
        case.gate_status = "HUMAN_LATCH"
        case.human_latch_token = None
        case.human_approver = None
        decision = DecisionDraft(
            decision_type="reject_draft",
            gate_status=case.gate_status,
            document_status="DRAFT_EXPORT",
            payout_ready=False,
            inference_track="deterministic",
            human_latch_required=True,
            human_latch_token=None,
            citations=[citation],
            appeal_path=APPEAL_PATH_DEFAULT,
            reason_summary=reason,
        )
        self._attach_latch_fields(decision, case, recommended_amount=0)
        if routed is not None:
            # 真实拒赔路径：按引用实际文档类型校验 handbook_ops 不得独撑
            doc_types: list[str] = []
            for c in decision.citations:
                hit = self._kb.resolve_clause(
                    str(c.get("doc_id") or ""),
                    str(c.get("clause_item") or ""),
                    str(c.get("doc_version") or ""),
                )
                if hit is not None:
                    doc_types.append(hit.doc_type)
            try:
                assert_reject_not_handbook_alone(
                    retrieval_profile=routed.retrieval_profile,
                    citation_doc_types=doc_types,
                )
            except ValueError as exc:
                raise ClaimsDomainError(
                    ErrorCode.VALIDATION_FAILED.value,
                    str(exc),
                ) from exc
            self._stamp_route(decision, routed)
            self._append_ledger(
                case,
                route_id=routed.route_id,
                retrieval_profile=routed.retrieval_profile,
                decision_type=decision.decision_type,
                validator_score=1.0,
                arbitration_winner=routed.arbitration_winner,
            )
        case.latest_decision = decision
        self._persist(case)
        return decision

    def _evaluate_reduction(
        self,
        case: ClaimCase,
        *,
        proposed_deductible: int | None = None,
        proposed_ratio: float | None = None,
        routed: RouteDecision | None = None,
    ) -> DecisionDraft:
        """批单缩责减赔：效力栈消解 + 可复核 calc_steps。"""
        from missions.models import RoleName

        endo_doc, endo_item, endo_ver = _SC03_ENDO_DEDUCT
        main_doc, main_item, main_ver = _SC03_MAIN_DEDUCT

        # 检索层落实 endorsement_priority：先批单后主险，再精确落库
        hits = self._kb.retrieve(
            "免赔额 赔付比例 保险责任",
            role=RoleName.WORKER,
            profile="endorsement_priority",
            top_k=8,
        )
        endo_pos = next((i for i, h in enumerate(hits) if h.doc_id == endo_doc), None)
        main_pos = next((i for i, h in enumerate(hits) if h.doc_id == main_doc), None)
        if endo_pos is None:
            raise ClaimsDomainError(
                ErrorCode.VALIDATION_FAILED.value,
                "endorsement_priority 未召回批单，失败关闭",
            )
        if main_pos is not None and endo_pos > main_pos:
            raise ClaimsDomainError(
                ErrorCode.VALIDATION_FAILED.value,
                "endorsement_priority 未先批单后主险，失败关闭",
            )

        endo_chunk = self._kb.resolve_clause(endo_doc, endo_item, endo_ver)
        if endo_chunk is None:
            raise ClaimsDomainError(
                ErrorCode.CITATION_NOT_IN_KB.value,
                "批单免赔条款未落库，无法减赔",
            )
        win_deduct, win_ratio = self._parse_deduct_ratio(endo_chunk.text)

        # 条款冲突：提出与批单不一致的免赔/比例 → 失败关闭，禁止静默改数
        if proposed_deductible is not None or proposed_ratio is not None:
            pd = proposed_deductible if proposed_deductible is not None else win_deduct
            pr = proposed_ratio if proposed_ratio is not None else win_ratio
            if pd != win_deduct or abs(pr - win_ratio) > 1e-9:
                raise ClaimsDomainError(
                    ErrorCode.VALIDATION_FAILED.value,
                    "理算参数与批单条款冲突，失败关闭",
                )

        overridden_by = {
            "doc_id": endo_doc,
            "clause_item": endo_item,
            "doc_version": endo_ver,
        }
        citations = [
            self._citation_dict(endo_doc, endo_item, endo_ver),
            self._citation_dict(
                main_doc,
                main_item,
                main_ver,
                overridden_by=overridden_by,
            ),
        ]
        if citations[0]["authority_rank"] >= citations[1]["authority_rank"]:
            raise ClaimsDomainError(
                ErrorCode.VALIDATION_FAILED.value,
                "效力栈异常：批单未优于主险",
            )

        calc_steps = self._build_reduction_calc(
            case.claim_amount_claimed,
            win_deduct,
            win_ratio,
            endo_item,
        )
        recommended = int(calc_steps[-1]["value"])
        case.gate_status = "ADJUSTING"
        decision = DecisionDraft(
            decision_type="reduce",
            gate_status=case.gate_status,
            document_status="DRAFT_EXPORT",
            payout_ready=False,
            inference_track="deterministic",
            human_latch_required=True,
            citations=citations,
            calc_steps=calc_steps,
        )
        self._attach_latch_fields(decision, case, recommended_amount=recommended)
        if routed is not None:
            self._stamp_route(decision, routed)
            self._append_ledger(
                case,
                route_id=routed.route_id,
                retrieval_profile=routed.retrieval_profile,
                decision_type=decision.decision_type,
                validator_score=1.0,
                arbitration_winner=routed.arbitration_winner,
            )
        case.latest_decision = decision
        self._persist(case)
        return decision

    def evaluate(
        self,
        case_id: str,
        *,
        proposed_deductible: int | None = None,
        proposed_ratio: float | None = None,
        sensitivity_flags: list[str] | None = None,
        source_decisions: Mapping[str, str] | None = None,
        retrieval_profile: str | None = None,
        force_reject_with_handbook_only: bool = False,
        ocr_text: str | None = None,
        customer_remark: str | None = None,
    ) -> DecisionDraft:
        """材料齐全断言 → Router 表驱动补件 / 拒赔 / 减赔 / 通赔建议。"""
        case = self.get_claim(case_id)
        # OCR/备注仅收纳；不得改写人闸矩阵输入
        absorb_user_controlled_text(
            case, ocr_text=ocr_text, customer_remark=customer_remark
        )
        if sensitivity_flags is not None:
            case.sensitivity_flags = list(sensitivity_flags)

        # handbook_ops 独撑对外拒赔探针：必须失败关闭
        if force_reject_with_handbook_only:
            try:
                assert_reject_not_handbook_alone(
                    retrieval_profile=retrieval_profile or "handbook_ops",
                    citation_doc_types=["handbook"],
                )
            except ValueError as exc:
                raise ClaimsDomainError(
                    ErrorCode.VALIDATION_FAILED.value,
                    str(exc),
                ) from exc

        # 调查冻决期间：保持冻决态，禁止静默通赔/出款就绪
        if case.freeze_active:
            decision = DecisionDraft(
                decision_type="investigating",
                gate_status="INVESTIGATING",
                document_status="DRAFT_EXPORT",
                payout_ready=False,
                inference_track="deterministic",
                human_latch_required=True,
                freeze_active=True,
                reason_summary="调查冻决中，解除冻决须人闸",
            )
            self._attach_latch_fields(decision, case, recommended_amount=0)
            decision.freeze_active = True
            case.gate_status = "INVESTIGATING"
            case.latest_decision = decision
            self._persist(case)
            return decision

        # 峰值降级：禁止静默通赔，仅补件+人审队列
        if case.peak_degraded:
            return self._peak_degrade_decision(case)

        missing = self._missing_items(case)
        missing_codes = [m.code for m in missing]

        routed = route_case(
            CaseSignals(
                materials_missing=bool(missing),
                loss_cause=case.loss_cause,
                endorsement_flags=tuple(case.endorsement_flags),
                source_decisions=source_decisions,
                retrieval_profile_override=retrieval_profile,
            )
        )

        # 规则 vs RAG 冲突：fail-closed 进人闸，写 ledger，不静默采信
        if routed.fail_closed:
            self._append_ledger(
                case,
                route_id=routed.route_id,
                retrieval_profile=routed.retrieval_profile,
                decision_type="fail_closed_human_latch",
                validator_score=0.0,
                arbitration_winner=None,
            )
            case.gate_status = "HUMAN_LATCH"
            self._persist(case)
            raise ClaimsDomainError(
                ErrorCode.LATCH_REQUIRED.value,
                "规则与条款 RAG 冲突，失败关闭进人闸",
                extra={
                    "route_id": routed.route_id,
                    "retrieval_profile": routed.retrieval_profile,
                    "human_latch_required": True,
                    "decision_type": "fail_closed_human_latch",
                    "validator_score": 0.0,
                },
            )

        if missing:
            if case.frozen_one_shot_hash is not None:
                frozen = set(case.frozen_checklist_codes)
                old_still_missing = [
                    c for c in case.frozen_checklist_codes if c not in case.material_codes
                ]
                if old_still_missing:
                    extras = set(missing_codes) - frozen
                    if extras:
                        raise ClaimsDomainError(
                            ErrorCode.VALIDATION_FAILED.value,
                            "同 one_shot_hash 下禁止新增缺项；须客户先补齐已通知项",
                        )
                    one_shot = case.frozen_one_shot_hash
                    checklist_codes = list(case.frozen_checklist_codes)
                else:
                    one_shot = self._one_shot_hash(missing_codes)
                    checklist_codes = list(missing_codes)
                    case.frozen_one_shot_hash = one_shot
                    case.frozen_checklist_codes = checklist_codes
            else:
                one_shot = self._one_shot_hash(missing_codes)
                checklist_codes = list(missing_codes)
                case.frozen_one_shot_hash = one_shot
                case.frozen_checklist_codes = checklist_codes

            remaining = [
                REQUIRED_MATERIALS[c]
                for c in checklist_codes
                if c not in case.material_codes
            ]
            case.gate_status = "PENDING_SUPPLEMENT"
            decision = DecisionDraft(
                decision_type="supplement",
                gate_status=case.gate_status,
                document_status="DRAFT_EXPORT",
                payout_ready=False,
                inference_track="deterministic",
                supplement_checklist=[REQUIRED_MATERIALS[c] for c in checklist_codes],
                remaining_missing=remaining,
                one_shot_hash=one_shot,
                human_latch_required=False,
            )
            self._attach_latch_fields(decision, case, recommended_amount=0)
            self._stamp_route(decision, routed)
            self._append_ledger(
                case,
                route_id=routed.route_id,
                retrieval_profile=routed.retrieval_profile,
                decision_type=decision.decision_type,
                validator_score=1.0,
                arbitration_winner=routed.arbitration_winner,
            )
            case.latest_decision = decision
            self._persist(case)
            return decision

        case.frozen_one_shot_hash = None
        case.frozen_checklist_codes = []

        if routed.action == "reject_draft":
            return self._evaluate_rejection(case, routed=routed)

        if routed.action == "reduce":
            return self._evaluate_reduction(
                case,
                proposed_deductible=proposed_deductible,
                proposed_ratio=proposed_ratio,
                routed=routed,
            )

        case.gate_status = "PRIMARY_REVIEW"
        decision = DecisionDraft(
            decision_type="approve_recommend",
            gate_status=case.gate_status,
            document_status="DRAFT_EXPORT",
            payout_ready=False,
            inference_track="deterministic",
            human_latch_required=True,
        )
        self._attach_latch_fields(
            decision, case, recommended_amount=case.claim_amount_claimed
        )
        if decision.human_latch_required:
            case.gate_status = "HUMAN_LATCH"
            decision.gate_status = case.gate_status
        self._stamp_route(decision, routed)
        self._append_ledger(
            case,
            route_id=routed.route_id,
            retrieval_profile=routed.retrieval_profile,
            decision_type=decision.decision_type,
            validator_score=1.0,
            arbitration_winner=routed.arbitration_winner,
        )
        case.latest_decision = decision
        self._persist(case)
        return decision

    def _peak_degrade_decision(self, case: ClaimCase) -> DecisionDraft:
        """峰值降级：仅补件 + 排队人审，禁止静默通赔。"""
        peak_item = SupplementItem(
            code="PEAK_HUMAN_REVIEW",
            name_zh="峰值降级人工复核材料包",
            required=True,
            example="按人审队列指引提交完整材料与说明",
        )
        case.gate_status = "HUMAN_LATCH"
        case.peak_degraded = True
        decision = DecisionDraft(
            decision_type="supplement",
            gate_status=case.gate_status,
            document_status="DRAFT_EXPORT",
            payout_ready=False,
            inference_track="deterministic",
            supplement_checklist=[peak_item],
            remaining_missing=[peak_item],
            one_shot_hash=self._one_shot_hash([peak_item.code]),
            human_latch_required=True,
            peak_degraded=True,
            reason_summary="峰值降级：仅允许补件+排队人审，禁止静默自动通赔",
        )
        self._attach_latch_fields(decision, case, recommended_amount=0)
        decision.human_latch_required = True
        decision.peak_degraded = True
        case.latest_decision = decision
        self._persist(case)
        return decision

    def decide_exgratia(
        self,
        case_id: str,
        *,
        reason: str,
        recommended_amount: int,
        citations: list[dict[str, Any]] | None = None,
    ) -> DecisionDraft:
        """通融决定：必闸；禁止伪主险条款通赔 citation。"""
        case = self.get_claim(case_id)
        cites = list(citations or [])
        for c in cites:
            if is_fake_exgratia_clause_approve_citation(c):
                raise ClaimsDomainError(
                    ErrorCode.VALIDATION_FAILED.value,
                    "通融不得使用主险条款通赔伪 citation，失败关闭",
                )
        if "exgratia" not in case.sensitivity_flags:
            case.sensitivity_flags.append("exgratia")
        case.gate_status = "HUMAN_LATCH"
        case.human_latch_token = None
        decision = DecisionDraft(
            decision_type="exgratia",
            gate_status=case.gate_status,
            document_status="DRAFT_EXPORT",
            payout_ready=False,
            inference_track="deterministic",
            human_latch_required=True,
            citations=cites,
            reason_summary=reason,
        )
        self._attach_latch_fields(decision, case, recommended_amount=recommended_amount)
        decision.human_latch_required = True
        case.latest_decision = decision
        self._persist(case)
        return decision

    def decide_prepay(
        self,
        case_id: str,
        *,
        reason: str,
        recommended_amount: int,
    ) -> DecisionDraft:
        """预赔：默认必闸，无人闸不得出款就绪。"""
        case = self.get_claim(case_id)
        case.gate_status = "HUMAN_LATCH"
        case.human_latch_token = None
        decision = DecisionDraft(
            decision_type="prepay",
            gate_status=case.gate_status,
            document_status="DRAFT_EXPORT",
            payout_ready=False,
            inference_track="deterministic",
            human_latch_required=True,
            reason_summary=reason,
        )
        self._attach_latch_fields(decision, case, recommended_amount=recommended_amount)
        decision.human_latch_required = True
        case.latest_decision = decision
        self._persist(case)
        return decision

    def enter_investigation(
        self,
        case_id: str,
        *,
        reason: str,
        risk_score: float,
    ) -> DecisionDraft:
        """风险超阈进入调查中：自动冻决，payout_ready=false。"""
        case = self.get_claim(case_id)
        case.freeze_active = True
        case.gate_status = "INVESTIGATING"
        case.human_latch_token = None
        case.human_approver = None
        decision = DecisionDraft(
            decision_type="investigating",
            gate_status=case.gate_status,
            document_status="DRAFT_EXPORT",
            payout_ready=False,
            inference_track="deterministic",
            human_latch_required=True,
            freeze_active=True,
            reason_summary=f"{reason}（risk_score={risk_score}）；冻决中不得出款就绪",
        )
        self._attach_latch_fields(decision, case, recommended_amount=0)
        decision.freeze_active = True
        decision.human_latch_required = True
        case.latest_decision = decision
        self._persist(case)
        return decision

    def unfreeze_investigation(
        self,
        case_id: str,
        *,
        human_latch_token: str | None,
    ) -> dict[str, Any]:
        """解除调查冻决：必须持有有效人闸令牌。"""
        case = self.get_claim(case_id)
        if not case.freeze_active:
            raise ClaimsDomainError(
                ErrorCode.VALIDATION_FAILED.value,
                "当前案件未处于调查冻决",
            )
        if not human_latch_token or human_latch_token != case.human_latch_token:
            raise ClaimsDomainError(
                ErrorCode.LATCH_REQUIRED.value,
                "解除调查冻决须有效人闸令牌",
            )
        case.freeze_active = False
        case.gate_status = "PRIMARY_REVIEW"
        if case.latest_decision is not None:
            case.latest_decision.freeze_active = False
            case.latest_decision.payout_ready = False
            case.latest_decision.gate_status = case.gate_status
        self._persist(case)
        return {
            "case_id": case.case_id,
            "freeze_active": False,
            "payout_ready": False,
            "gate_status": case.gate_status,
            "human_latch_token": case.human_latch_token,
        }

    def peak_degrade(self, case_id: str, *, reason: str) -> DecisionDraft:
        """峰值降级入口：仅补件+人审队列。"""
        case = self.get_claim(case_id)
        case.peak_degraded = True
        decision = self._peak_degrade_decision(case)
        if reason:
            decision.reason_summary = reason
        self._persist(case)
        return decision

    def register_materials(
        self,
        case_id: str,
        *,
        material_codes: list[str],
        image_ids: list[str] | None = None,
        ocr_text: str | None = None,
        customer_remark: str | None = None,
    ) -> ClaimCase:
        """客户补传材料元数据；OCR/备注可观察收纳，不改人闸规则。"""
        case = self.get_claim(case_id)
        absorb_user_controlled_text(
            case, ocr_text=ocr_text, customer_remark=customer_remark
        )
        for code in material_codes:
            if code not in REQUIRED_MATERIALS:
                raise ClaimsDomainError(
                    ErrorCode.VALIDATION_FAILED.value,
                    f"未知材料码: {code}",
                )
            if code not in case.material_codes:
                case.material_codes.append(code)
        if image_ids:
            for img in image_ids:
                if img not in case.image_ids:
                    case.image_ids.append(img)
        self._persist(case)
        return case

    def notify_supplement(
        self,
        case_id: str,
        *,
        one_shot_hash: str,
        missing_item_codes: list[str],
    ) -> dict[str, Any]:
        """补件通知出口：同 hash 下清单必须与冻结完整清单一致，否则拆轮失败。"""
        case = self.get_claim(case_id)
        if case.frozen_one_shot_hash is None:
            raise ClaimsDomainError(
                ErrorCode.VALIDATION_FAILED.value,
                "尚无冻结的一次补件清单，请先 evaluate",
            )
        if one_shot_hash != case.frozen_one_shot_hash:
            raise ClaimsDomainError(
                ErrorCode.VALIDATION_FAILED.value,
                "one_shot_hash 与案件冻结指纹不一致",
            )
        frozen = set(case.frozen_checklist_codes)
        offered = set(missing_item_codes)
        if offered != frozen:
            raise ClaimsDomainError(
                ErrorCode.VALIDATION_FAILED.value,
                "同 one_shot_hash 禁止拆轮补件：通知清单须与一次完整缺项一致",
            )
        return self.export_document(
            case_id,
            document_type="supplement_notice",
            document_status="DRAFT_EXPORT",
        )

    def approve_human_latch(
        self,
        case_id: str,
        *,
        approved_by: str,
        second_approver: str | None = None,
    ) -> dict[str, Any]:
        """人闸批准：发出令牌；D 档上浮双人令牌；拒赔案仍不得出款就绪。"""
        case = self.get_claim(case_id)
        if case.latest_decision is None:
            raise ClaimsDomainError(
                ErrorCode.VALIDATION_FAILED.value,
                "尚无裁决草案，请先 evaluate",
            )
        if not case.latest_decision.human_latch_required:
            raise ClaimsDomainError(
                ErrorCode.VALIDATION_FAILED.value,
                "当前裁决不要求人闸",
            )
        if case.latest_decision.dual_token_required:
            if not second_approver or second_approver.strip() == approved_by.strip():
                raise ClaimsDomainError(
                    ErrorCode.LATCH_REQUIRED.value,
                    "已是 D 档上浮须双人令牌：second_approver 须为不同批准人",
                )
        token = f"HLT-{secrets.token_hex(8)}"
        case.human_latch_token = token
        case.human_approver = approved_by
        case.latest_decision.human_latch_token = token
        case.latest_decision.payout_ready = False
        case.gate_status = "HUMAN_LATCH"
        case.latest_decision.gate_status = case.gate_status
        body: dict[str, Any] = {
            "case_id": case.case_id,
            "human_latch_token": token,
            "human_approver": approved_by,
            "payout_ready": False,
            "gate_status": case.gate_status,
            "decision_type": case.latest_decision.decision_type,
            "dual_token_required": case.latest_decision.dual_token_required,
        }
        if case.latest_decision.dual_token_required:
            body["second_approver"] = second_approver
        self._append_ledger(
            case,
            route_id="LATCH-APPROVE",
            retrieval_profile=_ledger_retrieval_profile(case),
            decision_type="human_latch_approve",
            validator_score=1.0,
        )
        self._record_latch_event(
            LatchEvent(
                case_id=case.case_id,
                event_type="approve",
                actor=approved_by,
                ts=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                human_latch_token=token,
                second_approver=second_approver,
            )
        )
        return body

    def reject_human_latch(
        self,
        case_id: str,
        *,
        rejected_by: str,
        reason: str = "",
    ) -> dict[str, Any]:
        """人闸驳回：回编辑态，可再 evaluate 提审。"""
        case = self.get_claim(case_id)
        case.human_latch_token = None
        case.human_approver = None
        case.gate_status = "PRIMARY_REVIEW"
        if case.latest_decision is not None:
            case.latest_decision.human_latch_token = None
            case.latest_decision.payout_ready = False
            case.latest_decision.gate_status = case.gate_status
        self._append_ledger(
            case,
            route_id="LATCH-REJECT",
            retrieval_profile=_ledger_retrieval_profile(case),
            decision_type="human_latch_reject",
            validator_score=0.0,
        )
        self._record_latch_event(
            LatchEvent(
                case_id=case.case_id,
                event_type="reject",
                actor=rejected_by,
                ts=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                reason=reason,
            )
        )
        return {
            "case_id": case.case_id,
            "gate_status": case.gate_status,
            "human_latch_token": None,
            "payout_ready": False,
            "rejected_by": rejected_by,
            "reason": reason,
        }

    def _assert_master_data_aligned(self, case: ClaimCase) -> None:
        """保单/险别/条款/批单/案件号与核心快照不一致则禁止出款就绪。"""
        snap = case.core_master
        if snap is None:
            return
        if (
            snap.case_id != case.case_id
            or snap.policy_no != case.policy_no
            or snap.product_code != case.product_code
            or snap.clause_version != case.clause_version
            or list(snap.endorsement_flags) != list(case.endorsement_flags)
        ):
            raise ClaimsDomainError(
                ErrorCode.MASTER_DATA_MISMATCH.value,
                "保单/批单/案件主数据与核心不一致，禁止出款就绪",
                extra={
                    "case_policy_no": case.policy_no,
                    "core_policy_no": snap.policy_no,
                },
            )

    def writeback_payout_ready(
        self,
        case_id: str,
        *,
        human_latch_token: str | None,
    ) -> dict[str, Any]:
        """L2 模拟回写出款就绪：须人闸令牌；不触发银企支付。"""
        case = self.get_claim(case_id)
        if case.freeze_active:
            raise ClaimsDomainError(
                ErrorCode.LATCH_REQUIRED.value,
                "调查冻决中禁止出款就绪",
            )
        if not human_latch_token or human_latch_token != case.human_latch_token:
            raise ClaimsDomainError(
                ErrorCode.LATCH_REQUIRED.value,
                "写入出款就绪须有效人闸令牌",
            )
        decision = case.latest_decision
        if decision is None:
            raise ClaimsDomainError(
                ErrorCode.VALIDATION_FAILED.value,
                "尚无裁决草案，禁止出款就绪",
            )
        if decision.decision_type not in _PAYOUT_ELIGIBLE_DECISIONS:
            raise ClaimsDomainError(
                ErrorCode.VALIDATION_FAILED.value,
                f"裁决类型 {decision.decision_type} 不得进入出款就绪",
            )
        self._assert_master_data_aligned(case)

        # 明确不调用银企/支付适配器（payment_adapter_calls 保持不变）
        case.gate_status = "PAYOUT_READY"
        decision.gate_status = "PAYOUT_READY"
        decision.payout_ready = True
        self._append_ledger(
            case,
            route_id="L2-PAYOUT-READY",
            retrieval_profile=decision.retrieval_profile or "clause_v_current",
            decision_type="l2_payout_ready",
            validator_score=1.0,
        )
        self._persist(case)
        return {
            "case_id": case.case_id,
            "gate_status": case.gate_status,
            "payout_ready": True,
            "payment_adapter_called": False,
            "decision_type": decision.decision_type,
            "human_latch_token": case.human_latch_token,
            "inference_track": "deterministic",
        }

    def writeback_close(
        self,
        case_id: str,
        *,
        close_opinion: str,
    ) -> dict[str, Any]:
        """L2 结案回写：可达 CLOSED；载荷不含自动支付指令；与出款解耦。"""
        case = self.get_claim(case_id)
        if case.freeze_active:
            raise ClaimsDomainError(
                ErrorCode.LATCH_REQUIRED.value,
                "调查冻决中禁止结案回写",
            )
        if not close_opinion or not close_opinion.strip():
            raise ClaimsDomainError(
                ErrorCode.VALIDATION_FAILED.value,
                "结案意见不能为空",
            )
        case.gate_status = "CLOSED"
        case.close_opinion = close_opinion.strip()
        if case.latest_decision is not None:
            case.latest_decision.gate_status = "CLOSED"
        self._append_ledger(
            case,
            route_id="L2-CLOSE",
            retrieval_profile=(
                case.latest_decision.retrieval_profile
                if case.latest_decision and case.latest_decision.retrieval_profile
                else "clause_v_current"
            ),
            decision_type="l2_close",
            validator_score=1.0,
        )
        self._persist(case)
        # 故意不包含 auto_pay / payment_instruction / bank_transfer
        return {
            "case_id": case.case_id,
            "gate_status": "CLOSED",
            "close_opinion": case.close_opinion,
            "payout_ready": bool(
                case.latest_decision.payout_ready if case.latest_decision else False
            ),
            "payment_adapter_called": False,
            "inference_track": "deterministic",
        }

    def export_document(
        self,
        case_id: str,
        *,
        document_type: str,
        document_status: str,
        human_latch_token: str | None = None,
    ) -> dict[str, Any]:
        """文书导出；补件/减赔/拒赔草稿分态；拒赔 EXTERNAL_NOTIFY 须人闸。"""
        case = self.get_claim(case_id)

        if document_type == "reduction_notice":
            return self._export_reduction_notice(case, document_status=document_status)

        if document_type == "reject_notice":
            return self._export_reject_notice(
                case,
                document_status=document_status,
                human_latch_token=human_latch_token,
            )

        if document_type != "supplement_notice":
            raise ClaimsDomainError(
                ErrorCode.VALIDATION_FAILED.value,
                f"不支持的 document_type: {document_type}",
            )
        if document_status not in ("DRAFT_EXPORT", "EXTERNAL_NOTIFY"):
            raise ClaimsDomainError(
                ErrorCode.DOCUMENT_STATUS_FORBIDDEN.value,
                f"不支持的 document_status: {document_status}",
            )

        if case.latest_decision is None or case.latest_decision.decision_type != "supplement":
            if not case.frozen_checklist_codes:
                raise ClaimsDomainError(
                    ErrorCode.VALIDATION_FAILED.value,
                    "无补件清单可导出，请先 evaluate",
                )

        codes = case.frozen_checklist_codes or [
            i.code
            for i in (
                case.latest_decision.supplement_checklist if case.latest_decision else []
            )
        ]
        items = [REQUIRED_MATERIALS[c].to_dict() for c in codes]
        one_shot = case.frozen_one_shot_hash or (
            case.latest_decision.one_shot_hash if case.latest_decision else None
        )
        now = datetime.now(timezone.utc).replace(microsecond=0)
        deadline = now + timedelta(days=10)
        return {
            "document_type": "supplement_notice",
            "document_status": document_status,
            "case_id": case.case_id,
            "policy_no": case.policy_no,
            "notify_time": now.isoformat(),
            "missing_items": items,
            "legal_basis": LEGAL_BASIS_ARTICLE_22,
            "supplement_deadline": deadline.date().isoformat(),
            "contact": "核赔初审岗-演示承办",
            "one_shot_hash": one_shot,
            "inference_track": "deterministic",
        }

    def _export_reduction_notice(
        self,
        case: ClaimCase,
        *,
        document_status: str,
    ) -> dict[str, Any]:
        """减赔通知：复用 citations 与 calc_steps；无人闸前不得出款就绪。"""
        if document_status != "DRAFT_EXPORT":
            raise ClaimsDomainError(
                ErrorCode.DOCUMENT_STATUS_FORBIDDEN.value,
                f"减赔本票仅支持 DRAFT_EXPORT，收到: {document_status}",
            )
        decision = case.latest_decision
        if decision is None or decision.decision_type != "reduce":
            raise ClaimsDomainError(
                ErrorCode.VALIDATION_FAILED.value,
                "无减赔草案可导出，请先 evaluate",
            )
        now = datetime.now(timezone.utc).replace(microsecond=0)
        return {
            "document_type": "reduction_notice",
            "document_status": document_status,
            "case_id": case.case_id,
            "policy_no": case.policy_no,
            "notify_time": now.isoformat(),
            "decision_type": decision.decision_type,
            "citations": list(decision.citations),
            "calc_steps": list(decision.calc_steps),
            "payout_ready": False,
            "inference_track": "deterministic",
            "contact": "核赔初审岗-演示承办",
        }

    def _export_reject_notice(
        self,
        case: ClaimCase,
        *,
        document_status: str,
        human_latch_token: str | None,
    ) -> dict[str, Any]:
        """拒赔通知：DRAFT_EXPORT 可无人闸；EXTERNAL_NOTIFY 须令牌且引用落库。"""
        decision = case.latest_decision
        if decision is None or decision.decision_type != "reject_draft":
            raise ClaimsDomainError(
                ErrorCode.VALIDATION_FAILED.value,
                "无拒赔草案可导出，请先 evaluate",
            )
        if document_status == "EXTERNAL_NOTIFY":
            if not human_latch_token or human_latch_token != case.human_latch_token:
                raise ClaimsDomainError(
                    ErrorCode.LATCH_REQUIRED.value,
                    "拒赔升 EXTERNAL_NOTIFY 须有效人闸令牌",
                )
            self._assert_citations_in_kb(decision.citations)
        elif document_status != "DRAFT_EXPORT":
            raise ClaimsDomainError(
                ErrorCode.DOCUMENT_STATUS_FORBIDDEN.value,
                f"不支持的 document_status: {document_status}",
            )

        now = datetime.now(timezone.utc).replace(microsecond=0)
        body: dict[str, Any] = {
            "document_type": "reject_notice",
            "document_status": document_status,
            "case_id": case.case_id,
            "policy_no": case.policy_no,
            "notify_time": now.isoformat(),
            "decision": "拒绝赔偿/拒绝给付",
            "reason_summary": decision.reason_summary or "",
            "citations": list(decision.citations),
            "evidence_refs": list(case.image_ids),
            "appeal_path": decision.appeal_path or APPEAL_PATH_DEFAULT,
            "notify_deadline_anchor": (now + timedelta(days=3)).date().isoformat(),
            "payout_ready": False,
            "inference_track": "deterministic",
        }
        if document_status == "EXTERNAL_NOTIFY":
            body["human_approver"] = case.human_approver
            body["human_latch_token"] = case.human_latch_token
        return body

    def assist(
        self,
        case_id: str,
        *,
        query: str,
        retrieval_profile: str | None = None,
        top_k: int = 3,
        enable_llm: bool = True,
    ) -> dict[str, Any]:
        """AI 辅助建议：关键词提名 + 可选 LLM；永不写 payout_ready / 人闸令牌。

        enable_llm=True 表示作业员显式请求辅助；无 Key 时 pipeline 明确降级。
        """
        case = self.get_claim(case_id)
        profile = retrieval_profile or "clause_v_current"
        # 查询仅用于关键词提名；不得解析改 latch / payout_ready
        result = draft_assist(
            query,
            retrieval_profile=profile,
            enable_llm=enable_llm,
            top_k=top_k,
        )
        # 审计：assist 调用入 ledger；不改权威裁决草案
        self._append_ledger(
            case,
            route_id="ASSIST-LLM-OPTIONAL",
            retrieval_profile=result.retrieval_profile,
            decision_type="assist_suggestion",
            validator_score=0.0,
        )
        self._persist(case)
        body = result.to_dict()
        body["case_id"] = case_id
        # 再次硬钉：assist 路径不得签发人闸或出款就绪
        body["payout_ready"] = False
        body["human_latch_token"] = None
        return body

    def adopt_assist(
        self,
        case_id: str,
        *,
        draft_text: str | None = None,
        suggested_stance: str | None = None,
        retrieval_profile: str | None = None,
        assist_invocation_id: str | None = None,
        proposed_deductible: int | None = None,
        proposed_ratio: float | None = None,
        sensitivity_flags: list[str] | None = None,
        source_decisions: Mapping[str, str] | None = None,
        ocr_text: str | None = None,
        customer_remark: str | None = None,
        force_reject_with_handbook_only: bool = False,
    ) -> DecisionDraft:
        """采纳辅助建议：必须再过规则 evaluate，不得直写权威裁决字段。

        suggested_stance / draft_text 仅作可观察输入（经 absorb），
        不得绕过门禁改 decision_type / payout_ready / 人闸令牌。
        """
        case = self.get_claim(case_id)
        # 采纳重写草案前作废既有人闸令牌，防止旧令牌解锁 L2
        case.human_latch_token = None
        case.human_approver = None
        if case.latest_decision is not None:
            case.latest_decision.human_latch_token = None
            case.latest_decision.payout_ready = False

        # suggested_stance / assist_invocation_id 刻意不写入 DecisionDraft 权威字段
        _ = suggested_stance
        remark = customer_remark
        if draft_text:
            remark = f"{remark}\n{draft_text}".strip() if remark else draft_text
        if assist_invocation_id:
            tag = f"[assist_invocation_id={assist_invocation_id}]"
            remark = f"{tag}\n{remark}" if remark else tag

        decision = self.evaluate(
            case_id,
            proposed_deductible=proposed_deductible,
            proposed_ratio=proposed_ratio,
            sensitivity_flags=sensitivity_flags,
            source_decisions=source_decisions,
            retrieval_profile=retrieval_profile,
            force_reject_with_handbook_only=force_reject_with_handbook_only,
            ocr_text=ocr_text,
            customer_remark=remark,
        )
        # evaluate 已保证 payout_ready=False（非 L2 路径）；采纳不得签发人闸
        decision.payout_ready = False
        decision.human_latch_token = None
        return decision


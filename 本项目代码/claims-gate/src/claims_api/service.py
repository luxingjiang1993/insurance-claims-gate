"""理赔案件服务：材料齐全断言、一次补件、通赔建议、除外拒赔、效力栈减赔。

Rewrote from: REF-MISSIONS（transfer_api/service.py 换垂直）；补件法义 REF-COURSE-03；
SC-02 拒赔分态 REF-MISSIONS；效力栈减赔 / calc_steps REF-CASE-KB, REF-COURSE-04
"""

from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from missions.rag import KnowledgeBase

from .error_codes import ErrorCode
from .models_domain import ClaimCase, DecisionDraft, SupplementItem

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

    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


class ClaimsService:
    """内存案件台账；SC-01 缺发票；SC-02 疾病摔伤除外；SC-03 批单缩责减赔。"""

    def __init__(self, kb: KnowledgeBase | None = None) -> None:
        self._kb = kb if kb is not None else KnowledgeBase(_DEFAULT_KB_ROOT)
        self._citation_validator: CitationValidator | None = None
        self._cases: dict[str, ClaimCase] = {}
        self._seed()

    def set_citation_validator(self, validator: CitationValidator) -> None:
        """注入条款落库校验（对外通知失败关闭）。"""
        self._citation_validator = validator

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
        )
        self._cases[case.case_id] = case

        # SC-02：材料齐全 + 疾病摔伤除外
        all_codes = list(REQUIRED_MATERIALS.keys())
        sc02 = ClaimCase(
            case_id="CLM-SC02-001",
            policy_no="PA-2026-000202",
            product_code="PA-ACCIDENT-MED",
            clause_version="PA-ACC-2024.1",
            loss_date="2026-07-20",
            claim_amount_claimed=280000,
            endorsement_flags=[],
            image_ids=[f"IMG-{c}" for c in all_codes],
            material_codes=list(all_codes),
            loss_cause="disease_fall",
            gate_status="MATERIALS_INTAKE",
            inference_track="deterministic",
        )
        self._cases[sc02.case_id] = sc02

        # SC-03：材料齐全 + 批单缩责，索赔金额 10000 元（确定性理算）
        sc03 = ClaimCase(
            case_id="CLM-SC03-001",
            policy_no="PA-2026-000303",
            product_code="PA-ACCIDENT-MED",
            clause_version="PA-ACC-2024.1",
            loss_date="2026-08-15",
            claim_amount_claimed=10000,
            endorsement_flags=["PA-ACC-END-001"],
            image_ids=[f"IMG-{c}" for c in all_codes],
            material_codes=list(all_codes),
            loss_cause="accident",
            gate_status="MATERIALS_INTAKE",
            inference_track="deterministic",
        )
        self._cases[sc03.case_id] = sc03

    def get_claim(self, case_id: str) -> ClaimCase:
        case = self._cases.get(case_id)
        if case is None:
            raise ClaimNotFoundError(case_id)
        return case

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

    def _evaluate_rejection(self, case: ClaimCase) -> DecisionDraft:
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
        case.latest_decision = decision
        return decision

    def _evaluate_reduction(
        self,
        case: ClaimCase,
        *,
        proposed_deductible: int | None = None,
        proposed_ratio: float | None = None,
    ) -> DecisionDraft:
        """批单缩责减赔：效力栈消解 + 可复核 calc_steps。"""
        endo_doc, endo_item, endo_ver = _SC03_ENDO_DEDUCT
        main_doc, main_item, main_ver = _SC03_MAIN_DEDUCT

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
        case.latest_decision = decision
        return decision

    def evaluate(
        self,
        case_id: str,
        *,
        proposed_deductible: int | None = None,
        proposed_ratio: float | None = None,
    ) -> DecisionDraft:
        """材料齐全断言 → 补件 / 拒赔 / 减赔 / 通赔建议。"""
        case = self.get_claim(case_id)
        missing = self._missing_items(case)
        missing_codes = [m.code for m in missing]

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
            case.latest_decision = decision
            return decision

        case.frozen_one_shot_hash = None
        case.frozen_checklist_codes = []

        if case.loss_cause == "disease_fall":
            return self._evaluate_rejection(case)

        if case.endorsement_flags:
            return self._evaluate_reduction(
                case,
                proposed_deductible=proposed_deductible,
                proposed_ratio=proposed_ratio,
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
        case.latest_decision = decision
        return decision

    def register_materials(
        self,
        case_id: str,
        *,
        material_codes: list[str],
        image_ids: list[str] | None = None,
    ) -> ClaimCase:
        """客户补传材料元数据（确定性登记，无 OCR）。"""
        case = self.get_claim(case_id)
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

    def approve_human_latch(self, case_id: str, *, approved_by: str) -> dict[str, Any]:
        """人闸批准：发出令牌；拒赔案仍不得出款就绪。"""
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
        token = f"HLT-{secrets.token_hex(8)}"
        case.human_latch_token = token
        case.human_approver = approved_by
        case.latest_decision.human_latch_token = token
        case.latest_decision.payout_ready = False
        case.gate_status = "HUMAN_LATCH"
        case.latest_decision.gate_status = case.gate_status
        return {
            "case_id": case.case_id,
            "human_latch_token": token,
            "human_approver": approved_by,
            "payout_ready": False,
            "gate_status": case.gate_status,
            "decision_type": case.latest_decision.decision_type,
        }

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
        return {
            "case_id": case.case_id,
            "gate_status": case.gate_status,
            "human_latch_token": None,
            "payout_ready": False,
            "rejected_by": rejected_by,
            "reason": reason,
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


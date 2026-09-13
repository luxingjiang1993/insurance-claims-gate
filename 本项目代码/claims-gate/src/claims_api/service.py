"""理赔案件服务：材料齐全断言、一次补件、通赔建议草案。

Rewrote from: REF-MISSIONS（transfer_api/service.py 换垂直）；补件法义 REF-COURSE-03
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

from .error_codes import ErrorCode
from .models_domain import ClaimCase, DecisionDraft, SupplementItem

# 《保险法》第22条一次性补正义务 — 法务审定锚点文案（轨 A 固定常量）
LEGAL_BASIS_ARTICLE_22 = (
    "依据《中华人民共和国保险法》第二十二条，保险人认为有关的证明和资料不完整的，"
    "应当及时一次性通知投保人、被保险人或者受益人补充提供。"
)

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
    """内存案件台账；SC-01 夹具缺发票+诊断证明。"""

    def __init__(self) -> None:
        self._cases: dict[str, ClaimCase] = {}
        self._seed()

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
            gate_status="MATERIALS_INTAKE",
            inference_track="deterministic",
        )
        self._cases[case.case_id] = case

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

    def evaluate(self, case_id: str) -> DecisionDraft:
        """材料齐全断言 → 补件或通赔建议；同 hash 禁止静默扩清单。"""
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
                    # 部分补传：保持冻结完整清单与原 hash
                    one_shot = case.frozen_one_shot_hash
                    checklist_codes = list(case.frozen_checklist_codes)
                else:
                    # 旧项已齐，出现新缺项：开启新一次补件
                    one_shot = self._one_shot_hash(missing_codes)
                    checklist_codes = list(missing_codes)
                    case.frozen_one_shot_hash = one_shot
                    case.frozen_checklist_codes = checklist_codes
            else:
                # 首次一次补件：冻结完整缺项与 hash
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

        # 材料齐：通赔建议草案；未人闸前不得出款就绪
        case.gate_status = "PRIMARY_REVIEW"
        case.frozen_one_shot_hash = None
        case.frozen_checklist_codes = []
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
        # 成功通知：返回与 PRD §11.1 同构字段（DRAFT_EXPORT 可无人闸）
        return self.export_document(
            case_id,
            document_type="supplement_notice",
            document_status="DRAFT_EXPORT",
        )

    def export_document(
        self,
        case_id: str,
        *,
        document_type: str,
        document_status: str,
    ) -> dict[str, Any]:
        """文书导出；补件 DRAFT_EXPORT 可无人闸。"""
        case = self.get_claim(case_id)
        if document_type != "supplement_notice":
            raise ClaimsDomainError(
                ErrorCode.VALIDATION_FAILED.value,
                f"本票仅支持 supplement_notice，收到: {document_type}",
            )
        if document_status != "DRAFT_EXPORT":
            # 补件升 EXTERNAL_NOTIFY 默认可自动，但本票验收焦点为草稿字段
            if document_status != "EXTERNAL_NOTIFY":
                raise ClaimsDomainError(
                    ErrorCode.DOCUMENT_STATUS_FORBIDDEN.value,
                    f"不支持的 document_status: {document_status}",
                )

        if case.latest_decision is None or case.latest_decision.decision_type != "supplement":
            # 允许仅冻结清单时导出
            if not case.frozen_checklist_codes:
                raise ClaimsDomainError(
                    ErrorCode.VALIDATION_FAILED.value,
                    "无补件清单可导出，请先 evaluate",
                )

        codes = case.frozen_checklist_codes or [
            i.code for i in (case.latest_decision.supplement_checklist if case.latest_decision else [])
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

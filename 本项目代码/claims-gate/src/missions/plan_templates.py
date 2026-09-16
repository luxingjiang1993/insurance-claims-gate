"""Schema-bound 规划模板目录：契约源按 template_id 精确查找。

Rewrote from: REF-MISSIONS（契约断言外形）；禁止用 goal 字符串 if/elif 作为主规划源。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .models import Assertion, MachineCheck


@dataclass(frozen=True)
class PlanTemplate:
    """预登记规划模板：template_id → 契约/feature 外形。"""

    template_id: str
    title: str
    clause_id: str
    feature_title: str
    milestone: str
    owns_paths: tuple[str, ...]
    rewrote_from: str
    build_assertions: Callable[[str], list[Assertion]]


def _scaffold_assertions(clause_id: str) -> list[Assertion]:
    return [
        Assertion(
            id="A-001",
            behavior="L1 只读返回案件头且门禁态为 MATERIALS_INTAKE",
            policy_clause_id=clause_id,
            acceptance="GET /claims/{case_id} 含最低字段且 gate_status=MATERIALS_INTAKE",
            machine_check=MachineCheck(
                type="claim_header_l1",
                params={"case_id": "CLM-SC01-001", "gate_status": "MATERIALS_INTAKE"},
            ),
            claimed_by_features=["F-001"],
        )
    ]


def _sc01_assertions(clause_id: str) -> list[Assertion]:
    return [
        Assertion(
            id="A-001",
            behavior="同 one_shot_hash 拆轮补件必须失败关闭",
            policy_clause_id=clause_id,
            acceptance="supplement/notify 子集缺项返回 VALIDATION_FAILED",
            machine_check=MachineCheck(
                type="one_shot_split_round_rejected",
                params={"case_id": "CLM-SC01-001"},
            ),
            claimed_by_features=["F-001"],
        ),
        Assertion(
            id="A-002",
            behavior="SC-01：缺发票一次补件后补传，产出通赔建议且未人闸前不出款就绪",
            policy_clause_id=clause_id,
            acceptance="HTTP：evaluate→export→materials→evaluate；payout_ready=false",
            machine_check=MachineCheck(
                type="sc01_one_shot_supplement_approve",
                params={"case_id": "CLM-SC01-001"},
            ),
            claimed_by_features=["F-001"],
        ),
    ]


def _sc02_assertions(clause_id: str) -> list[Assertion]:
    return [
        Assertion(
            id="A-001",
            behavior="SC-02：疾病摔伤拒赔草案须条款项落库引用；DRAFT 可无人闸；人闸后方可 EXTERNAL_NOTIFY",
            policy_clause_id=clause_id,
            acceptance="HTTP：evaluate→DRAFT→approve→EXTERNAL；payout_ready=false",
            machine_check=MachineCheck(
                type="sc02_exclusion_reject_latch",
                params={"case_id": "CLM-SC02-001"},
            ),
            claimed_by_features=["F-001"],
        ),
        Assertion(
            id="A-002",
            behavior="拒赔升 EXTERNAL_NOTIFY 无人闸必须失败关闭",
            policy_clause_id=clause_id,
            acceptance="documents/export EXTERNAL_NOTIFY 返回 LATCH_REQUIRED 或 DOCUMENT_STATUS_FORBIDDEN",
            machine_check=MachineCheck(
                type="sc02_external_notify_requires_latch",
                params={"case_id": "CLM-SC02-001"},
            ),
            claimed_by_features=["F-001"],
        ),
    ]


def _sc03_assertions(clause_id: str) -> list[Assertion]:
    return [
        Assertion(
            id="A-001",
            behavior="SC-03：批单缩责减赔须效力栈引用与可复核 calc_steps；冲突 fail-closed",
            policy_clause_id=clause_id,
            acceptance="HTTP：evaluate→reduce；overridden_by；export reduction_notice；payout_ready=false",
            machine_check=MachineCheck(
                type="sc03_endorsement_stack_reduction",
                params={"case_id": "CLM-SC03-001"},
            ),
            claimed_by_features=["F-001"],
        ),
    ]


def _router_assertions(clause_id: str) -> list[Assertion]:
    return [
        Assertion(
            id="A-001",
            behavior="Router 表驱动：同夹具轨 A 重复跑可复现；ledger 含 route_id/retrieval_profile/decision_type/validator_score",
            policy_clause_id=clause_id,
            acceptance="evaluate 两次 route 一致；GET ledger 含四字段",
            machine_check=MachineCheck(
                type="router_ledger_reproducible",
                params={"case_id": "CLM-SC02-001"},
            ),
            claimed_by_features=["F-001"],
        ),
    ]


PLAN_TEMPLATES: dict[str, PlanTemplate] = {
    "scaffold": PlanTemplate(
        template_id="scaffold",
        title="条款门禁脚手架：案件头只读",
        clause_id="POL-CLAIM-001",
        feature_title="实现 L1 案件头只读与 MATERIALS_INTAKE",
        milestone="M0-scaffold",
        owns_paths=(
            "src/claims_api/api.py",
            "src/claims_api/service.py",
            "src/claims_api/error_codes.py",
        ),
        rewrote_from="REF-MISSIONS, REF-COURSE-03",
        build_assertions=_scaffold_assertions,
    ),
    "sc01": PlanTemplate(
        template_id="sc01",
        title="SC-01 一次补件 → 通赔建议（轨 A）",
        clause_id="POL-CLAIM-002",
        feature_title="实现 SC-01 一次补件与通赔建议确定性轨",
        milestone="M1-sc01",
        owns_paths=(
            "src/claims_api/api.py",
            "src/claims_api/service.py",
            "src/claims_api/models_domain.py",
            "src/missions/checks.py",
        ),
        rewrote_from="REF-MISSIONS, REF-COURSE-03",
        build_assertions=_sc01_assertions,
    ),
    "sc02": PlanTemplate(
        template_id="sc02",
        title="SC-02 除外拒赔草案 + 文书分态 + 人闸（轨 A）",
        clause_id="POL-CLAIM-003",
        feature_title="实现 SC-02 除外拒赔与人闸文书分态",
        milestone="M1-sc02",
        owns_paths=(
            "src/claims_api/api.py",
            "src/claims_api/service.py",
            "src/claims_api/models_domain.py",
            "src/missions/checks.py",
        ),
        rewrote_from="REF-MISSIONS, REF-COURSE-03",
        build_assertions=_sc02_assertions,
    ),
    "sc03": PlanTemplate(
        template_id="sc03",
        title="SC-03 效力栈减赔 + 理算步骤（轨 A）",
        clause_id="POL-CLAIM-004",
        feature_title="实现 SC-03 效力栈减赔与 calc_steps",
        milestone="M1-sc03",
        owns_paths=(
            "src/claims_api/api.py",
            "src/claims_api/service.py",
            "src/missions/rag.py",
            "src/missions/checks.py",
        ),
        rewrote_from="REF-CASE-KB, REF-MISSIONS, REF-COURSE-04, REF-COURSE-03",
        build_assertions=_sc03_assertions,
    ),
    "router": PlanTemplate(
        template_id="router",
        title="Router 确定性策略表 + ledger（轨 A）",
        clause_id="POL-CLAIM-005",
        feature_title="实现 Router 策略表、冲突 fail-closed 与每案 ledger",
        milestone="M1-router",
        owns_paths=(
            "src/missions/router.py",
            "src/claims_api/service.py",
            "src/claims_api/api.py",
            "src/missions/checks.py",
        ),
        rewrote_from="REF-COURSE-12, REF-CASE-HYBRID, REF-MISSIONS, REF-COURSE-03",
        build_assertions=_router_assertions,
    ),
}


def get_plan_template(template_id: str) -> PlanTemplate:
    """按 template_id 精确查找；未知 ID 应由 plan schema 先硬停。"""
    try:
        return PLAN_TEMPLATES[template_id]
    except KeyError as exc:
        raise KeyError(f"未知 plan template_id: {template_id}") from exc

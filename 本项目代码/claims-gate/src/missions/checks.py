"""Contract 驱动的黑盒检查：按 machine_check.type 分发，不按 assertion.id 写死。

Rewrote from: REF-MISSIONS（missions/checks.py；检查体换理赔域）；
SC-01 补件/拆轮/通赔建议 REF-COURSE-03；SC-02 拒赔引用/文书分态/人闸 REF-MISSIONS；
SC-03 效力栈减赔 / calc_steps REF-CASE-KB, REF-COURSE-04
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi.testclient import TestClient

from claims_api.error_codes import ErrorCode

from .models import Assertion, CommandResult, MachineCheck


@dataclass
class CheckOutcome:
    ok: bool
    detail: str
    command: CommandResult


def _check_claim_header_l1(client: TestClient, params: dict[str, Any]) -> CheckOutcome:
    case_id = params.get("case_id", "CLM-SC01-001")
    expect_status = params.get("gate_status", "MATERIALS_INTAKE")
    resp = client.get(f"/claims/{case_id}")
    if resp.status_code != 200:
        return CheckOutcome(
            ok=False,
            detail=f"status={resp.status_code}",
            command=CommandResult(
                cmd=f"GET /claims/{case_id}",
                exit_code=1,
                stdout_tail=str(resp.json())[:400],
            ),
        )
    body = resp.json()
    required = [
        "case_id",
        "policy_no",
        "product_code",
        "clause_version",
        "loss_date",
        "gate_status",
        "inference_track",
    ]
    missing = [k for k in required if k not in body or body[k] in (None, "")]
    ok = (
        not missing
        and body.get("gate_status") == expect_status
        and body.get("inference_track") == "deterministic"
    )
    return CheckOutcome(
        ok=ok,
        detail=(
            f"missing={missing} gate_status={body.get('gate_status')} "
            f"inference_track={body.get('inference_track')}"
        ),
        command=CommandResult(
            cmd=f"GET /claims/{case_id}",
            exit_code=0 if ok else 1,
            stdout_tail=str(body)[:400],
        ),
    )


def _check_citation_in_kb(client: TestClient, params: dict[str, Any]) -> CheckOutcome:
    """条款项落库门：HTTP 黑盒验收幻觉条款不过门。"""
    payload = {
        "doc_id": params.get("doc_id", ""),
        "clause_item": params.get("clause_item", ""),
        "doc_version": params.get("doc_version", ""),
    }
    if params.get("quote"):
        payload["quote"] = params["quote"]
    resp = client.post("/kb/citations/validate", json=payload)
    body = resp.json() if resp.content else {}
    if resp.status_code == 200 and body.get("ok") is True:
        return CheckOutcome(
            ok=True,
            detail="citation_in_kb ok",
            command=CommandResult(
                cmd="POST /kb/citations/validate",
                exit_code=0,
                stdout_tail=str(body)[:400],
            ),
        )
    detail = body.get("detail", body)
    if isinstance(detail, dict):
        err = detail.get("error_code", ErrorCode.CITATION_NOT_IN_KB.value)
        msg = detail.get("message", str(detail))
    else:
        err = ErrorCode.CITATION_NOT_IN_KB.value
        msg = str(detail)
    return CheckOutcome(
        ok=False,
        detail=f"{err}: {msg}",
        command=CommandResult(
            cmd="POST /kb/citations/validate",
            exit_code=1,
            stdout_tail=str(body)[:400],
        ),
    )


def _error_code(resp) -> str | None:
    if resp.status_code < 400:
        return None
    detail = resp.json().get("detail")
    if isinstance(detail, dict):
        return detail.get("error_code")
    return None


def _reset_claims_fixture() -> None:
    """断言间隔离：同一夹具案会被补传污染，须在检查入口重建台账。"""
    from claims_api.api import reset_service

    reset_service()


def _check_sc01_one_shot_supplement_approve(
    client: TestClient, params: dict[str, Any]
) -> CheckOutcome:
    """SC-01 主路径：缺件补件 → 文书 → 补传 → 通赔建议且 payout_ready=false。"""
    _reset_claims_fixture()
    case_id = params.get("case_id", "CLM-SC01-001")
    steps: list[str] = []

    ev = client.post(f"/claims/{case_id}/evaluate")
    if ev.status_code != 200:
        return CheckOutcome(
            False,
            f"evaluate failed status={ev.status_code}",
            CommandResult(cmd=f"POST /claims/{case_id}/evaluate", exit_code=1, stdout_tail=str(ev.json())[:400]),
        )
    body = ev.json()
    steps.append("evaluate_supplement")
    if body.get("decision_type") != "supplement" or body.get("gate_status") != "PENDING_SUPPLEMENT":
        return CheckOutcome(
            False,
            f"expect supplement/PENDING_SUPPLEMENT got {body.get('decision_type')}/{body.get('gate_status')}",
            CommandResult(cmd="evaluate", exit_code=1, stdout_tail=str(body)[:400]),
        )
    if not body.get("one_shot_hash") or not body.get("supplement_checklist"):
        return CheckOutcome(
            False,
            "missing one_shot_hash or checklist",
            CommandResult(cmd="evaluate", exit_code=1, stdout_tail=str(body)[:400]),
        )
    if body.get("payout_ready") is not False or body.get("inference_track") != "deterministic":
        return CheckOutcome(
            False,
            f"payout_ready/inference_track bad: {body.get('payout_ready')}/{body.get('inference_track')}",
            CommandResult(cmd="evaluate", exit_code=1, stdout_tail=str(body)[:400]),
        )

    full_codes = [item["code"] for item in body["supplement_checklist"]]
    notify = client.post(
        f"/claims/{case_id}/supplement/notify",
        json={"one_shot_hash": body["one_shot_hash"], "missing_item_codes": full_codes},
    )
    if notify.status_code != 200:
        return CheckOutcome(
            False,
            f"notify failed status={notify.status_code}",
            CommandResult(cmd="supplement/notify", exit_code=1, stdout_tail=str(notify.json())[:400]),
        )
    nbody = notify.json()
    steps.append("notify")
    if not nbody.get("legal_basis") or not nbody.get("missing_items"):
        return CheckOutcome(
            False,
            "notify missing legal_basis or missing_items",
            CommandResult(cmd="supplement/notify", exit_code=1, stdout_tail=str(nbody)[:400]),
        )

    doc = client.post(
        f"/claims/{case_id}/documents/export",
        json={"document_type": "supplement_notice", "document_status": "DRAFT_EXPORT"},
    )
    if doc.status_code != 200:
        return CheckOutcome(
            False,
            f"export failed status={doc.status_code}",
            CommandResult(cmd="documents/export", exit_code=1, stdout_tail=str(doc.json())[:400]),
        )
    dbody = doc.json()
    steps.append("draft_export")
    legal = dbody.get("legal_basis") or ""
    if "第二十二条" not in legal and "第22条" not in legal:
        return CheckOutcome(
            False,
            "legal_basis missing 第22条锚点",
            CommandResult(cmd="documents/export", exit_code=1, stdout_tail=str(dbody)[:400]),
        )
    for key in ("case_id", "policy_no", "notify_time", "supplement_deadline", "contact", "one_shot_hash"):
        if not dbody.get(key):
            return CheckOutcome(
                False,
                f"export missing field {key}",
                CommandResult(cmd="documents/export", exit_code=1, stdout_tail=str(dbody)[:400]),
            )
    missing_items = dbody.get("missing_items") or []
    if not missing_items:
        return CheckOutcome(
            False,
            "export missing_items empty",
            CommandResult(cmd="documents/export", exit_code=1, stdout_tail=str(dbody)[:400]),
        )
    for item in missing_items:
        if not item.get("name_zh") or "required" not in item or not item.get("example"):
            return CheckOutcome(
                False,
                f"missing_item incomplete: {item}",
                CommandResult(cmd="documents/export", exit_code=1, stdout_tail=str(dbody)[:400]),
            )

    codes = [item["code"] for item in body["supplement_checklist"]]
    up = client.post(
        f"/claims/{case_id}/materials",
        json={"material_codes": codes, "image_ids": [f"IMG-{c}" for c in codes]},
    )
    if up.status_code != 200:
        return CheckOutcome(
            False,
            f"materials failed status={up.status_code}",
            CommandResult(cmd="materials", exit_code=1, stdout_tail=str(up.json())[:400]),
        )
    steps.append("materials")

    again = client.post(f"/claims/{case_id}/evaluate")
    if again.status_code != 200:
        return CheckOutcome(
            False,
            f"re-evaluate failed status={again.status_code}",
            CommandResult(cmd="re-evaluate", exit_code=1, stdout_tail=str(again.json())[:400]),
        )
    abody = again.json()
    steps.append("approve_recommend")
    ok = (
        abody.get("decision_type") == "approve_recommend"
        and abody.get("payout_ready") is False
        and abody.get("document_status") == "DRAFT_EXPORT"
        and abody.get("inference_track") == "deterministic"
        and abody.get("gate_status") in ("PRIMARY_REVIEW", "HUMAN_LATCH", "PENDING_APPROVAL")
    )
    return CheckOutcome(
        ok=ok,
        detail=f"steps={steps} decision={abody.get('decision_type')} payout_ready={abody.get('payout_ready')}",
        command=CommandResult(
            cmd=f"SC-01 flow case={case_id}",
            exit_code=0 if ok else 1,
            stdout_tail=str(abody)[:400],
        ),
    )


def _check_one_shot_split_round_rejected(
    client: TestClient, params: dict[str, Any]
) -> CheckOutcome:
    """同 one_shot_hash 拆轮补件必须失败。"""
    _reset_claims_fixture()
    case_id = params.get("case_id", "CLM-SC01-001")
    ev = client.post(f"/claims/{case_id}/evaluate")
    if ev.status_code != 200:
        return CheckOutcome(
            False,
            f"evaluate failed status={ev.status_code}",
            CommandResult(cmd="evaluate", exit_code=1, stdout_tail=str(ev.json())[:400]),
        )
    body = ev.json()
    one_shot = body.get("one_shot_hash")
    codes = [item["code"] for item in body.get("supplement_checklist") or []]
    if not one_shot or len(codes) < 2:
        return CheckOutcome(
            False,
            f"need hash and >=2 missing items, got hash={one_shot} codes={codes}",
            CommandResult(cmd="evaluate", exit_code=1, stdout_tail=str(body)[:400]),
        )
    resp = client.post(
        f"/claims/{case_id}/supplement/notify",
        json={"one_shot_hash": one_shot, "missing_item_codes": [codes[0]]},
    )
    got = _error_code(resp)
    ok = resp.status_code == 422 and got == ErrorCode.VALIDATION_FAILED.value
    return CheckOutcome(
        ok=ok,
        detail=f"status={resp.status_code} error_code={got}",
        command=CommandResult(
            cmd="POST supplement/notify subset",
            exit_code=0 if ok else 1,
            stdout_tail=str(resp.json())[:400],
        ),
    )


def _check_sc02_exclusion_reject_latch(
    client: TestClient, params: dict[str, Any]
) -> CheckOutcome:
    """SC-02：疾病摔伤拒赔草案 + 落库引用 + DRAFT 可无人闸 + 人闸后可 EXTERNAL_NOTIFY。"""
    _reset_claims_fixture()
    case_id = params.get("case_id", "CLM-SC02-001")
    steps: list[str] = []

    ev = client.post(f"/claims/{case_id}/evaluate")
    if ev.status_code != 200:
        return CheckOutcome(
            False,
            f"evaluate failed status={ev.status_code}",
            CommandResult(cmd="evaluate", exit_code=1, stdout_tail=str(ev.json())[:400]),
        )
    body = ev.json()
    steps.append("reject_draft")
    if body.get("decision_type") != "reject_draft":
        return CheckOutcome(
            False,
            f"expect reject_draft got {body.get('decision_type')}",
            CommandResult(cmd="evaluate", exit_code=1, stdout_tail=str(body)[:400]),
        )
    if body.get("payout_ready") is not False or not body.get("appeal_path"):
        return CheckOutcome(
            False,
            f"payout_ready/appeal_path bad: {body.get('payout_ready')}/{body.get('appeal_path')}",
            CommandResult(cmd="evaluate", exit_code=1, stdout_tail=str(body)[:400]),
        )
    if "秒赔" in str(body):
        return CheckOutcome(
            False,
            "narrative contains forbidden 秒赔",
            CommandResult(cmd="evaluate", exit_code=1, stdout_tail=str(body)[:400]),
        )
    citations = body.get("citations") or []
    if not citations:
        return CheckOutcome(
            False,
            "missing citations",
            CommandResult(cmd="evaluate", exit_code=1, stdout_tail=str(body)[:400]),
        )
    for c in citations:
        v = client.post(
            "/kb/citations/validate",
            json={
                "doc_id": c.get("doc_id", ""),
                "clause_item": c.get("clause_item", ""),
                "doc_version": c.get("doc_version", ""),
                "quote": c.get("quote", ""),
            },
        )
        if v.status_code != 200:
            return CheckOutcome(
                False,
                f"citation gate fail: {c}",
                CommandResult(cmd="citations/validate", exit_code=1, stdout_tail=str(v.json())[:400]),
            )
    steps.append("citations_ok")

    draft = client.post(
        f"/claims/{case_id}/documents/export",
        json={"document_type": "reject_notice", "document_status": "DRAFT_EXPORT"},
    )
    if draft.status_code != 200 or not draft.json().get("appeal_path"):
        return CheckOutcome(
            False,
            f"DRAFT_EXPORT failed status={draft.status_code}",
            CommandResult(cmd="export DRAFT", exit_code=1, stdout_tail=str(draft.json())[:400]),
        )
    steps.append("draft_export")

    bare = client.post(
        f"/claims/{case_id}/documents/export",
        json={"document_type": "reject_notice", "document_status": "EXTERNAL_NOTIFY"},
    )
    err = _error_code(bare)
    if bare.status_code not in (403, 422) or err not in (
        ErrorCode.LATCH_REQUIRED.value,
        ErrorCode.DOCUMENT_STATUS_FORBIDDEN.value,
    ):
        return CheckOutcome(
            False,
            f"expect latch fail, status={bare.status_code} err={err}",
            CommandResult(cmd="export EXTERNAL bare", exit_code=1, stdout_tail=str(bare.json())[:400]),
        )
    steps.append("external_without_latch_rejected")

    appr = client.post(
        f"/claims/{case_id}/human-latch/approve",
        json={"approved_by": "machine-check-supervisor"},
    )
    if appr.status_code != 200 or not appr.json().get("human_latch_token"):
        return CheckOutcome(
            False,
            f"approve failed status={appr.status_code}",
            CommandResult(cmd="human-latch/approve", exit_code=1, stdout_tail=str(appr.json())[:400]),
        )
    token = appr.json()["human_latch_token"]
    if appr.json().get("payout_ready") is not False:
        return CheckOutcome(
            False,
            "approve must keep payout_ready=false",
            CommandResult(cmd="human-latch/approve", exit_code=1, stdout_tail=str(appr.json())[:400]),
        )
    steps.append("latch_approved")

    ext = client.post(
        f"/claims/{case_id}/documents/export",
        json={
            "document_type": "reject_notice",
            "document_status": "EXTERNAL_NOTIFY",
            "human_latch_token": token,
        },
    )
    if ext.status_code != 200:
        return CheckOutcome(
            False,
            f"EXTERNAL_NOTIFY with token failed status={ext.status_code}",
            CommandResult(cmd="export EXTERNAL", exit_code=1, stdout_tail=str(ext.json())[:400]),
        )
    ebody = ext.json()
    ok = (
        ebody.get("document_status") == "EXTERNAL_NOTIFY"
        and bool(ebody.get("appeal_path"))
        and bool(ebody.get("human_approver"))
        and ebody.get("payout_ready") is False
        and "秒赔" not in str(ebody)
    )
    steps.append("external_notify")
    return CheckOutcome(
        ok=ok,
        detail=f"steps={steps}",
        command=CommandResult(
            cmd=f"SC-02 flow case={case_id}",
            exit_code=0 if ok else 1,
            stdout_tail=str(ebody)[:400],
        ),
    )


def _check_sc02_external_notify_requires_latch(
    client: TestClient, params: dict[str, Any]
) -> CheckOutcome:
    """负例检查：无人闸升 EXTERNAL_NOTIFY 必须被 API 拒绝（检查通过=正确拒绝）。"""
    _reset_claims_fixture()
    case_id = params.get("case_id", "CLM-SC02-001")
    ev = client.post(f"/claims/{case_id}/evaluate")
    if ev.status_code != 200:
        return CheckOutcome(
            False,
            f"evaluate failed status={ev.status_code}",
            CommandResult(cmd="evaluate", exit_code=1, stdout_tail=str(ev.json())[:400]),
        )
    resp = client.post(
        f"/claims/{case_id}/documents/export",
        json={"document_type": "reject_notice", "document_status": "EXTERNAL_NOTIFY"},
    )
    got = _error_code(resp)
    ok = resp.status_code in (403, 422) and got in (
        ErrorCode.LATCH_REQUIRED.value,
        ErrorCode.DOCUMENT_STATUS_FORBIDDEN.value,
    )
    return CheckOutcome(
        ok=ok,
        detail=f"status={resp.status_code} error_code={got}",
        command=CommandResult(
            cmd="POST documents/export EXTERNAL_NOTIFY without latch",
            exit_code=0 if ok else 1,
            stdout_tail=str(resp.json())[:400],
        ),
    )


def _check_sc03_endorsement_stack_reduction(
    client: TestClient, params: dict[str, Any]
) -> CheckOutcome:
    """SC-03：批单缩责减赔 + 效力栈 citations + calc_steps。"""
    _reset_claims_fixture()
    case_id = params.get("case_id", "CLM-SC03-001")
    ev = client.post(f"/claims/{case_id}/evaluate")
    if ev.status_code != 200:
        return CheckOutcome(
            False,
            f"evaluate failed status={ev.status_code}",
            CommandResult(cmd="evaluate", exit_code=1, stdout_tail=str(ev.json())[:400]),
        )
    body = ev.json()
    if body.get("decision_type") != "reduce" or body.get("payout_ready") is not False:
        return CheckOutcome(
            False,
            f"expect reduce/payout_ready=false got {body.get('decision_type')}/{body.get('payout_ready')}",
            CommandResult(cmd="evaluate", exit_code=1, stdout_tail=str(body)[:400]),
        )
    if body.get("gate_status") != "ADJUSTING" or body.get("inference_track") != "deterministic":
        return CheckOutcome(
            False,
            f"gate/track bad: {body.get('gate_status')}/{body.get('inference_track')}",
            CommandResult(cmd="evaluate", exit_code=1, stdout_tail=str(body)[:400]),
        )
    citations = body.get("citations") or []
    if len(citations) < 2:
        return CheckOutcome(
            False,
            "need >=2 citations for stack",
            CommandResult(cmd="evaluate", exit_code=1, stdout_tail=str(body)[:400]),
        )
    for c in citations:
        if "authority_rank" not in c:
            return CheckOutcome(
                False,
                f"citation missing authority_rank: {c}",
                CommandResult(cmd="evaluate", exit_code=1, stdout_tail=str(body)[:400]),
            )
    ranks = {c["clause_item"]: c["authority_rank"] for c in citations}
    if ranks.get("END-2-DEDUCT", 99) >= ranks.get("ART-6-DEDUCT", 0):
        return CheckOutcome(
            False,
            f"endorsement must outrank main: {ranks}",
            CommandResult(cmd="evaluate", exit_code=1, stdout_tail=str(body)[:400]),
        )
    overridden = [c for c in citations if c.get("overridden_by")]
    if not overridden:
        return CheckOutcome(
            False,
            "missing overridden_by on superseded citation",
            CommandResult(cmd="evaluate", exit_code=1, stdout_tail=str(body)[:400]),
        )
    steps = {s["step"]: s for s in (body.get("calc_steps") or [])}
    if steps.get("deductible", {}).get("value") != 500 or steps.get("result", {}).get("value") != 7600:
        return CheckOutcome(
            False,
            f"calc_steps unexpected: {steps}",
            CommandResult(cmd="evaluate", exit_code=1, stdout_tail=str(body)[:400]),
        )
    # 冲突探针：主险数字不得静默通过
    conflict = client.post(
        f"/claims/{case_id}/evaluate",
        json={"proposed_deductible": 100, "proposed_ratio": 1.0},
    )
    if conflict.status_code != 422 or _error_code(conflict) != ErrorCode.VALIDATION_FAILED.value:
        return CheckOutcome(
            False,
            f"calc conflict should fail-closed, status={conflict.status_code}",
            CommandResult(cmd="evaluate conflict", exit_code=1, stdout_tail=str(conflict.json())[:400]),
        )
    # 冲突后重评干净路径
    _reset_claims_fixture()
    ev2 = client.post(f"/claims/{case_id}/evaluate")
    if ev2.status_code != 200:
        return CheckOutcome(
            False,
            f"re-evaluate after reset failed status={ev2.status_code}",
            CommandResult(cmd="re-evaluate", exit_code=1, stdout_tail=str(ev2.json())[:400]),
        )
    doc = client.post(
        f"/claims/{case_id}/documents/export",
        json={"document_type": "reduction_notice", "document_status": "DRAFT_EXPORT"},
    )
    if doc.status_code != 200:
        return CheckOutcome(
            False,
            f"export failed status={doc.status_code}",
            CommandResult(cmd="export", exit_code=1, stdout_tail=str(doc.json())[:400]),
        )
    dbody = doc.json()
    ok = (
        dbody.get("payout_ready") is False
        and bool(dbody.get("calc_steps"))
        and bool(dbody.get("citations"))
    )
    return CheckOutcome(
        ok=ok,
        detail="sc03 endorsement stack ok",
        command=CommandResult(
            cmd=f"SC-03 flow case={case_id}",
            exit_code=0 if ok else 1,
            stdout_tail=str(dbody)[:400],
        ),
    )


def run_machine_check(client: TestClient, check: MachineCheck) -> CheckOutcome:
    """仅按 type + params 分发。"""
    t = check.type
    p = check.params

    if t == "claim_header_l1":
        return _check_claim_header_l1(client, p)
    if t == "citation_in_kb":
        return _check_citation_in_kb(client, p)
    if t == "sc01_one_shot_supplement_approve":
        return _check_sc01_one_shot_supplement_approve(client, p)
    if t == "one_shot_split_round_rejected":
        return _check_one_shot_split_round_rejected(client, p)
    if t == "sc02_exclusion_reject_latch":
        return _check_sc02_exclusion_reject_latch(client, p)
    if t == "sc02_external_notify_requires_latch":
        return _check_sc02_external_notify_requires_latch(client, p)
    if t == "sc03_endorsement_stack_reduction":
        return _check_sc03_endorsement_stack_reduction(client, p)

    return CheckOutcome(
        ok=False,
        detail=f"unknown machine_check.type={t}",
        command=CommandResult(cmd=f"check:{t}", exit_code=1, stdout_tail="unsupported"),
    )


def run_assertion_checks(client: TestClient, assertions: list[Assertion]) -> dict[str, Any]:
    """按 contract.assertions 顺序执行 machine_check。"""
    results: dict[str, CheckOutcome] = {}
    for assertion in assertions:
        results[assertion.id] = run_machine_check(client, assertion.machine_check)
    return results


"""Contract 驱动的黑盒检查：按 machine_check.type 分发，不按 assertion.id 写死。

Rewrote from: REF-MISSIONS（missions/checks.py；检查体换理赔域）
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


def run_machine_check(client: TestClient, check: MachineCheck) -> CheckOutcome:
    """仅按 type + params 分发。"""
    t = check.type
    p = check.params

    if t == "claim_header_l1":
        return _check_claim_header_l1(client, p)
    if t == "citation_in_kb":
        return _check_citation_in_kb(client, p)

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

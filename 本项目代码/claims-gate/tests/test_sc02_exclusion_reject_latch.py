"""接缝：理赔 HTTP API — SC-02 疾病摔伤除外拒赔 + 文书分态 + 人闸（轨 A）。

主缝对齐 SPEC 决策 7/8/16：外部可观察 HTTP + machine_check(type, params)。
Rewrote from: REF-MISSIONS
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from claims_api.api import app, get_service, reset_service
from claims_api.error_codes import ErrorCode
from missions.checks import run_machine_check
from missions.models import MachineCheck

CASE_ID = "CLM-SC02-001"
EXCL_DOC = "PA-ACC-MAIN"
EXCL_ITEM = "ART-5-EXCL"
EXCL_VER = "2024.1"


def _client() -> TestClient:
    reset_service()
    return TestClient(app)


def _supervisor_headers(client: TestClient) -> dict[str, str]:
    resp = client.post(
        "/auth/login",
        json={"username": "supervisor", "password": "supervisor"},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['session_token']}"}


def test_sc02_disease_fall_evaluate_to_reject_draft_with_citations() -> None:
    client = _client()
    resp = client.post(f"/claims/{CASE_ID}/evaluate")
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision_type"] == "reject_draft"
    assert body["gate_status"] in ("HUMAN_LATCH", "PENDING_APPROVAL")
    assert body["document_status"] == "DRAFT_EXPORT"
    assert body["payout_ready"] is False
    assert body["inference_track"] == "deterministic"
    assert body["human_latch_required"] is True
    assert body["human_latch_token"] is None
    assert body["appeal_path"]
    citations = body["citations"]
    assert isinstance(citations, list) and len(citations) >= 1
    hit = False
    for c in citations:
        assert c.get("doc_id")
        assert c.get("clause_item")
        assert c.get("doc_version")
        assert c.get("quote")
        if (
            c["doc_id"] == EXCL_DOC
            and c["clause_item"] == EXCL_ITEM
            and c["doc_version"] == EXCL_VER
        ):
            hit = True
        # 落库门：每条除外引用须可校验
        v = client.post(
            "/kb/citations/validate",
            json={
                "doc_id": c["doc_id"],
                "clause_item": c["clause_item"],
                "doc_version": c["doc_version"],
                "quote": c.get("quote", ""),
            },
        )
        assert v.status_code == 200, v.text
    assert hit, "须含主险疾病摔伤除外条款项引用"
    # 禁止「秒赔」包装责任争议案
    blob = str(body)
    assert "秒赔" not in blob


def test_sc02_reject_draft_export_without_latch_ok() -> None:
    client = _client()
    assert client.post(f"/claims/{CASE_ID}/evaluate").status_code == 200

    resp = client.post(
        f"/claims/{CASE_ID}/documents/export",
        json={
            "document_type": "reject_notice",
            "document_status": "DRAFT_EXPORT",
        },
    )
    assert resp.status_code == 200
    doc = resp.json()
    assert doc["document_status"] == "DRAFT_EXPORT"
    assert doc["case_id"] == CASE_ID
    assert doc["policy_no"]
    assert doc["decision"]
    assert doc["reason_summary"]
    assert doc["appeal_path"]
    assert doc["citations"]
    assert doc["evidence_refs"]
    assert doc["notify_deadline_anchor"]
    assert "秒赔" not in str(doc)


def test_sc02_external_notify_without_latch_fails() -> None:
    client = _client()
    assert client.post(f"/claims/{CASE_ID}/evaluate").status_code == 200

    resp = client.post(
        f"/claims/{CASE_ID}/documents/export",
        json={
            "document_type": "reject_notice",
            "document_status": "EXTERNAL_NOTIFY",
        },
    )
    assert resp.status_code in (403, 422)
    detail = resp.json()["detail"]
    assert detail["error_code"] in (
        ErrorCode.DOCUMENT_STATUS_FORBIDDEN.value,
        ErrorCode.LATCH_REQUIRED.value,
    )


def test_sc02_approve_latch_then_external_notify_ok_still_no_payout() -> None:
    client = _client()
    ev = client.post(f"/claims/{CASE_ID}/evaluate")
    assert ev.status_code == 200
    assert ev.json()["payout_ready"] is False

    appr = client.post(
        f"/claims/{CASE_ID}/human-latch/approve",
        json={"approved_by": "supervisor-demo"},
        headers=_supervisor_headers(client),
    )
    assert appr.status_code == 200
    token = appr.json()["human_latch_token"]
    assert token
    assert appr.json()["payout_ready"] is False

    # 人闸后仍不得出款就绪（拒赔案不触发银企）
    dec = client.get(f"/claims/{CASE_ID}/decision")
    assert dec.status_code == 200
    assert dec.json()["human_latch_token"] == token
    assert dec.json()["payout_ready"] is False

    ext = client.post(
        f"/claims/{CASE_ID}/documents/export",
        json={
            "document_type": "reject_notice",
            "document_status": "EXTERNAL_NOTIFY",
            "human_latch_token": token,
        },
    )
    assert ext.status_code == 200
    body = ext.json()
    assert body["document_status"] == "EXTERNAL_NOTIFY"
    assert body["appeal_path"]
    assert body["human_approver"] == "supervisor-demo"
    assert "秒赔" not in str(body)


def test_sc02_reject_latch_returns_to_edit_then_resubmit() -> None:
    client = _client()
    assert client.post(f"/claims/{CASE_ID}/evaluate").status_code == 200

    rej = client.post(
        f"/claims/{CASE_ID}/human-latch/reject",
        json={"rejected_by": "supervisor-demo", "reason": "需补充病历摘要"},
        headers=_supervisor_headers(client),
    )
    assert rej.status_code == 200
    body = rej.json()
    assert body["gate_status"] in ("PRIMARY_REVIEW", "EDITABLE", "MATERIALS_INTAKE")
    assert body.get("human_latch_token") in (None, "")
    assert body["payout_ready"] is False

    # 回编辑态后再提：重新 evaluate 再进人闸
    again = client.post(f"/claims/{CASE_ID}/evaluate")
    assert again.status_code == 200
    assert again.json()["decision_type"] == "reject_draft"
    assert again.json()["human_latch_required"] is True
    assert again.json()["human_latch_token"] is None
    assert again.json()["payout_ready"] is False


def test_sc02_fake_citation_cannot_external_notify() -> None:
    """伪 citation 不得升 EXTERNAL_NOTIFY。"""
    client = _client()
    assert client.post(f"/claims/{CASE_ID}/evaluate").status_code == 200

    appr = client.post(
        f"/claims/{CASE_ID}/human-latch/approve",
        json={"approved_by": "supervisor-demo"},
        headers=_supervisor_headers(client),
    )
    token = appr.json()["human_latch_token"]

    # 污染裁决引用为库外伪条款
    svc = get_service()
    case = svc.get_claim(CASE_ID)
    assert case.latest_decision is not None
    case.latest_decision.citations = [
        {
            "doc_id": "PA-GHOST",
            "clause_item": "ART-X",
            "doc_version": "1.0",
            "quote": "幻觉除外",
            "chunk_id": "ghost",
            "clause_id": "ghost",
            "score": 1.0,
        }
    ]

    ext = client.post(
        f"/claims/{CASE_ID}/documents/export",
        json={
            "document_type": "reject_notice",
            "document_status": "EXTERNAL_NOTIFY",
            "human_latch_token": token,
        },
    )
    assert ext.status_code in (403, 422)
    detail = ext.json()["detail"]
    assert detail["error_code"] in (
        ErrorCode.CITATION_NOT_IN_KB.value,
        ErrorCode.VALIDATION_FAILED.value,
        ErrorCode.DOCUMENT_STATUS_FORBIDDEN.value,
    )


def test_sc02_empty_citations_cannot_external_notify() -> None:
    """缺 citation 不得升 EXTERNAL_NOTIFY。"""
    client = _client()
    assert client.post(f"/claims/{CASE_ID}/evaluate").status_code == 200
    appr = client.post(
        f"/claims/{CASE_ID}/human-latch/approve",
        json={"approved_by": "supervisor-demo"},
        headers=_supervisor_headers(client),
    )
    token = appr.json()["human_latch_token"]
    svc = get_service()
    case = svc.get_claim(CASE_ID)
    assert case.latest_decision is not None
    case.latest_decision.citations = []

    ext = client.post(
        f"/claims/{CASE_ID}/documents/export",
        json={
            "document_type": "reject_notice",
            "document_status": "EXTERNAL_NOTIFY",
            "human_latch_token": token,
        },
    )
    assert ext.status_code in (403, 422)
    detail = ext.json()["detail"]
    assert detail["error_code"] in (
        ErrorCode.VALIDATION_FAILED.value,
        ErrorCode.CITATION_NOT_IN_KB.value,
    )


def test_machine_check_sc02_exclusion_reject_latch_passes() -> None:
    """轨 A：SC-02 拒赔引用 + 文书分态 + 人闸门稳定绿。"""
    reset_service()
    client = TestClient(app)
    outcome = run_machine_check(
        client,
        MachineCheck(
            type="sc02_exclusion_reject_latch",
            params={"case_id": CASE_ID},
        ),
    )
    assert outcome.ok, outcome.detail


def test_machine_check_sc02_external_notify_without_latch_fails_as_check() -> None:
    """machine_check 负例：无人闸升 EXTERNAL_NOTIFY 须被检出为失败场景（检查本身 ok=绿表示正确拒绝）。"""
    reset_service()
    client = TestClient(app)
    outcome = run_machine_check(
        client,
        MachineCheck(
            type="sc02_external_notify_requires_latch",
            params={"case_id": CASE_ID},
        ),
    )
    assert outcome.ok, outcome.detail

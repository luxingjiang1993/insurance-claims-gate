"""接缝 S0/S1：人闸 RBAC 硬门 + 负例机检。

主缝：HTTP 黑盒 + machine_check(type, params)。
Rewrote from: REF-MISSIONS
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from claims_api.api import app, reset_service
from claims_api.error_codes import ErrorCode
from missions.checks import run_machine_check
from missions.models import MachineCheck

CASE_ID = "CLM-SC02-001"


def _client() -> TestClient:
    reset_service()
    return TestClient(app)


def _login(client: TestClient, username: str) -> dict[str, str]:
    resp = client.post(
        "/auth/login",
        json={"username": username, "password": username},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['session_token']}"}


def test_supervisor_can_approve_outward_latch_and_get_token() -> None:
    client = _client()
    assert client.post(f"/claims/{CASE_ID}/evaluate").status_code == 200
    headers = _login(client, "supervisor")
    appr = client.post(
        f"/claims/{CASE_ID}/human-latch/approve",
        json={"approved_by": "supervisor"},
        headers=headers,
    )
    assert appr.status_code == 200, appr.text
    body = appr.json()
    assert body["human_latch_token"]
    assert body["payout_ready"] is False


def test_adjuster_approve_rejected_no_token() -> None:
    client = _client()
    assert client.post(f"/claims/{CASE_ID}/evaluate").status_code == 200
    headers = _login(client, "adjuster")
    appr = client.post(
        f"/claims/{CASE_ID}/human-latch/approve",
        json={"approved_by": "adjuster"},
        headers=headers,
    )
    assert appr.status_code == 403, appr.text
    detail = appr.json()["detail"]
    assert detail["error_code"] == ErrorCode.PERMISSION_DENIED.value
    assert appr.json().get("human_latch_token") in (None, "")
    decision = client.get(f"/claims/{CASE_ID}/decision")
    assert decision.status_code == 200
    assert decision.json().get("human_latch_token") in (None, "")


def test_viewer_approve_rejected_no_token() -> None:
    client = _client()
    assert client.post(f"/claims/{CASE_ID}/evaluate").status_code == 200
    headers = _login(client, "viewer")
    appr = client.post(
        f"/claims/{CASE_ID}/human-latch/approve",
        json={"approved_by": "viewer"},
        headers=headers,
    )
    assert appr.status_code == 403, appr.text
    assert appr.json()["detail"]["error_code"] == ErrorCode.PERMISSION_DENIED.value
    decision = client.get(f"/claims/{CASE_ID}/decision")
    assert decision.json().get("human_latch_token") in (None, "")


def test_anonymous_approve_rejected_no_token() -> None:
    """人闸硬门：无会话不得批闸签发令牌。"""
    client = _client()
    assert client.post(f"/claims/{CASE_ID}/evaluate").status_code == 200
    appr = client.post(
        f"/claims/{CASE_ID}/human-latch/approve",
        json={"approved_by": "anonymous-supervisor"},
    )
    assert appr.status_code in (401, 403), appr.text
    decision = client.get(f"/claims/{CASE_ID}/decision")
    assert decision.json().get("human_latch_token") in (None, "")


def test_viewer_write_materials_rejected() -> None:
    client = _client()
    headers = _login(client, "viewer")
    resp = client.post(
        "/claims/CLM-SC01-001/materials",
        json={"material_codes": ["MEDICAL_INVOICE"], "image_ids": ["IMG-1"]},
        headers=headers,
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"]["error_code"] == ErrorCode.PERMISSION_DENIED.value


def test_machine_check_latch_rbac_negatives() -> None:
    client = _client()
    outcome = run_machine_check(
        client,
        MachineCheck(type="latch_rbac_negatives", params={}),
    )
    assert outcome.ok, outcome.detail

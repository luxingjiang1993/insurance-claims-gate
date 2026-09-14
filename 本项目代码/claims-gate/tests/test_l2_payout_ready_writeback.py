"""接缝：L2 出款就绪 / 结案回写（HTTP 黑盒 + machine_check）。

验收：人闸令牌后可置 PAYOUT_READY 且无银企调用；无人闸失败；
主数据不一致 → MASTER_DATA_MISMATCH；CLOSED 载荷无自动支付指令；
支付类工具 ACL 默认拒绝。

Rewrote from: REF-MISSIONS, REF-CASE-FC
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from claims_api.api import app, get_service, reset_service
from claims_api.error_codes import ErrorCode
from claims_api.tools_acl import ToolPermissionError, assert_tool_allowed
from missions.checks import run_machine_check
from missions.models import MachineCheck

CASE_LATCH = "CLM-AMT-C-001"
CASE_MISMATCH = "CLM-MISMATCH-001"


def _client() -> TestClient:
    reset_service()
    return TestClient(app)


def _error_code(resp) -> str | None:
    if resp.status_code < 400:
        return None
    detail = resp.json().get("detail")
    if isinstance(detail, dict):
        return detail.get("error_code")
    return None


def _approve_token(client: TestClient, case_id: str) -> str:
    ev = client.post(f"/claims/{case_id}/evaluate")
    assert ev.status_code == 200, ev.text
    assert ev.json()["human_latch_required"] is True
    login = client.post(
        "/auth/login",
        json={"username": "supervisor", "password": "supervisor"},
    )
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['session_token']}"}
    appr = client.post(
        f"/claims/{case_id}/human-latch/approve",
        json={"approved_by": "supervisor-l2"},
        headers=headers,
    )
    assert appr.status_code == 200, appr.text
    token = appr.json()["human_latch_token"]
    assert token
    assert appr.json()["payout_ready"] is False
    return token


def test_payout_ready_requires_latch_token() -> None:
    """无人闸令牌写入出款就绪失败；payout_ready 保持 false。"""
    client = _client()
    client.post(f"/claims/{CASE_LATCH}/evaluate")

    denied = client.post(
        f"/claims/{CASE_LATCH}/l2/payout-ready",
        json={},
    )
    assert denied.status_code == 403, denied.text
    assert _error_code(denied) == ErrorCode.LATCH_REQUIRED.value

    dec = client.get(f"/claims/{CASE_LATCH}/decision")
    assert dec.status_code == 200
    assert dec.json()["payout_ready"] is False
    assert dec.json()["gate_status"] != "PAYOUT_READY"

    header = client.get(f"/claims/{CASE_LATCH}")
    assert header.json()["gate_status"] != "PAYOUT_READY"


def test_payout_ready_after_latch_no_payment_adapter() -> None:
    """人闸后可置 PAYOUT_READY；不触发银企/支付适配器。"""
    client = _client()
    token = _approve_token(client, CASE_LATCH)
    svc = get_service()
    before = svc.payment_adapter_calls

    ok = client.post(
        f"/claims/{CASE_LATCH}/l2/payout-ready",
        json={"human_latch_token": token},
    )
    assert ok.status_code == 200, ok.text
    body = ok.json()
    assert body["gate_status"] == "PAYOUT_READY"
    assert body["payout_ready"] is True
    assert body.get("payment_adapter_called") is False
    assert "auto_pay" not in body
    assert "payment_instruction" not in body
    assert svc.payment_adapter_calls == before

    dec = client.get(f"/claims/{CASE_LATCH}/decision")
    assert dec.json()["gate_status"] == "PAYOUT_READY"
    assert dec.json()["payout_ready"] is True

    led = client.get(f"/claims/{CASE_LATCH}/ledger")
    assert led.status_code == 200
    types = [i.get("decision_type") for i in led.json()["items"]]
    assert "l2_payout_ready" in types


def test_master_data_mismatch_blocks_payout_ready() -> None:
    """主数据不一致夹具禁止出款就绪。"""
    client = _client()
    token = _approve_token(client, CASE_MISMATCH)

    bad = client.post(
        f"/claims/{CASE_MISMATCH}/l2/payout-ready",
        json={"human_latch_token": token},
    )
    assert bad.status_code == 422, bad.text
    assert _error_code(bad) == ErrorCode.MASTER_DATA_MISMATCH.value

    dec = client.get(f"/claims/{CASE_MISMATCH}/decision")
    assert dec.json()["payout_ready"] is False
    assert dec.json()["gate_status"] != "PAYOUT_READY"


def test_close_writeback_decoupled_from_payment() -> None:
    """结案回写可达 CLOSED；载荷不含自动支付指令。"""
    client = _client()
    token = _approve_token(client, CASE_LATCH)
    client.post(
        f"/claims/{CASE_LATCH}/l2/payout-ready",
        json={"human_latch_token": token},
    )

    closed = client.post(
        f"/claims/{CASE_LATCH}/l2/close",
        json={"close_opinion": "核赔结案：同意给付，支付由核心人工办理"},
    )
    assert closed.status_code == 200, closed.text
    body = closed.json()
    assert body["gate_status"] == "CLOSED"
    assert body["close_opinion"]
    assert "auto_pay" not in body
    assert "payment_instruction" not in body
    assert "bank_transfer" not in body
    assert body.get("auto_payment") is not True
    assert get_service().payment_adapter_calls == 0

    header = client.get(f"/claims/{CASE_LATCH}")
    assert header.json()["gate_status"] == "CLOSED"


def test_payment_tools_still_denied_by_acl() -> None:
    """支付类工具在 ACL 下默认拒绝。"""
    for name in (
        "bank_payout_transfer",
        "silver_enterprise_direct_pay",
        "auto_payout",
        "l3_payment_adapter",
    ):
        try:
            assert_tool_allowed(name)
            raise AssertionError(f"应拒绝支付工具: {name}")
        except ToolPermissionError:
            pass
    assert_tool_allowed("l2_payout_ready")
    assert_tool_allowed("l2_close")


def test_machine_check_l2_payout_ready_latch_and_mismatch() -> None:
    client = _client()
    outcome = run_machine_check(
        client,
        MachineCheck(type="l2_payout_ready_writeback", params={}),
    )
    assert outcome.ok, outcome.detail


def test_machine_check_l2_close_no_auto_pay() -> None:
    client = _client()
    outcome = run_machine_check(
        client,
        MachineCheck(type="l2_close_without_payment", params={}),
    )
    assert outcome.ok, outcome.detail

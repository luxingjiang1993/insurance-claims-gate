"""接缝 S1：登录/会话角色可识别；SQLite 重启后案件域仍可读。

Rewrote from: REF-MISSIONS（HTTP TestClient 黑盒接缝）
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from claims_api.api import app, reset_service


def _client(db_path: Path | None = None) -> TestClient:
    reset_service(db_path=db_path)
    return TestClient(app)


def _supervisor_headers(client: TestClient) -> dict[str, str]:
    resp = client.post(
        "/auth/login",
        json={"username": "supervisor", "password": "supervisor"},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['session_token']}"}


def test_seed_roles_can_login_and_session_exposes_role() -> None:
    client = _client()
    for username, role in (
        ("viewer", "viewer"),
        ("adjuster", "adjuster"),
        ("supervisor", "supervisor"),
    ):
        resp = client.post(
            "/auth/login",
            json={"username": username, "password": username},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["username"] == username
        assert body["role"] == role
        assert body["session_token"]
        me = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {body['session_token']}"},
        )
        assert me.status_code == 200, me.text
        assert me.json()["username"] == username
        assert me.json()["role"] == role


def test_login_rejects_bad_password() -> None:
    client = _client()
    resp = client.post(
        "/auth/login",
        json={"username": "adjuster", "password": "wrong"},
    )
    assert resp.status_code == 401
    detail = resp.json()["detail"]
    assert detail["error_code"] == "AUTH_FAILED"


def test_case_materials_and_decision_survive_process_restart(tmp_path: Path) -> None:
    """同一 SQLite 文件上重建服务 = 进程重启后仍可读。"""
    db = tmp_path / "claims_gate.sqlite"
    client = _client(db_path=db)

    missing = ["MEDICAL_INVOICE", "DIAGNOSIS_REPORT"]
    reg = client.post(
        "/claims/CLM-SC01-001/materials",
        json={"material_codes": missing, "image_ids": [f"IMG-{c}" for c in missing]},
    )
    assert reg.status_code == 200, reg.text

    ev = client.post("/claims/CLM-SC01-001/evaluate")
    assert ev.status_code == 200, ev.text
    assert ev.json()["decision_type"] == "approve_recommend"

    # 模拟进程重启：同库路径重建服务
    client2 = _client(db_path=db)
    claim = client2.get("/claims/CLM-SC01-001")
    assert claim.status_code == 200
    body = claim.json()
    for code in missing:
        assert code in body["material_codes"]

    decision = client2.get("/claims/CLM-SC01-001/decision")
    assert decision.status_code == 200
    assert decision.json()["decision_type"] == "approve_recommend"

    ledger = client2.get("/claims/CLM-SC01-001/ledger")
    assert ledger.status_code == 200
    assert len(ledger.json()["items"]) >= 1


def test_latch_events_survive_restart(tmp_path: Path) -> None:
    db = tmp_path / "claims_gate.sqlite"
    client = _client(db_path=db)

    assert client.post("/claims/CLM-SC02-001/evaluate").status_code == 200
    approved = client.post(
        "/claims/CLM-SC02-001/human-latch/approve",
        json={"approved_by": "supervisor"},
        headers=_supervisor_headers(client),
    )
    assert approved.status_code == 200, approved.text
    token = approved.json()["human_latch_token"]
    assert token

    client2 = _client(db_path=db)
    events = client2.get("/claims/CLM-SC02-001/latch-events")
    assert events.status_code == 200, events.text
    items = events.json()["items"]
    assert any(e.get("event_type") == "approve" for e in items)
    decision = client2.get("/claims/CLM-SC02-001/decision")
    assert decision.json()["human_latch_token"] == token

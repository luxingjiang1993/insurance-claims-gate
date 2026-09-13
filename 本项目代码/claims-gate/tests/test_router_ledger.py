"""接缝：理赔 HTTP — Router 表驱动裁决 + 每案 ledger。

验收：evaluate 响应含 route_id/retrieval_profile；
Rules vs RAG 冲突 fail-closed 进人闸；
handbook_ops 单独拒赔失败；
GET /claims/{id}/ledger 含 route_id、retrieval_profile、decision_type、validator_score。
轨 A 同夹具重复跑 Router 结果可复现。

Rewrote from: REF-COURSE-12, REF-CASE-HYBRID, REF-MISSIONS
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from claims_api.api import app, reset_service
from claims_api.error_codes import ErrorCode
from missions.checks import run_machine_check
from missions.models import MachineCheck

SC01 = "CLM-SC01-001"
SC02 = "CLM-SC02-001"
SC03 = "CLM-SC03-001"


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


def test_evaluate_sc02_includes_route_and_profile() -> None:
    client = _client()
    resp = client.post(f"/claims/{SC02}/evaluate")
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision_type"] == "reject_draft"
    assert body["route_id"] == "R-EXCLUSION-REJECT"
    assert body["retrieval_profile"] == "clause_v_current"
    assert body["validator_score"] == 1.0


def test_evaluate_sc03_uses_endorsement_priority_route() -> None:
    client = _client()
    resp = client.post(f"/claims/{SC03}/evaluate")
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision_type"] == "reduce"
    assert body["route_id"] == "R-ENDORSEMENT-REDUCE"
    assert body["retrieval_profile"] == "endorsement_priority"


def test_ledger_records_required_fields_after_evaluate() -> None:
    client = _client()
    ev = client.post(f"/claims/{SC02}/evaluate")
    assert ev.status_code == 200
    led = client.get(f"/claims/{SC02}/ledger")
    assert led.status_code == 200
    items = led.json()["items"]
    assert len(items) >= 1
    last = items[0]
    assert last["route_id"] == "R-EXCLUSION-REJECT"
    assert last["retrieval_profile"] == "clause_v_current"
    assert last["decision_type"] == "reject_draft"
    assert last["validator_score"] == 1.0
    assert last["case_id"] == SC02


def test_rules_vs_rag_conflict_fail_closed_human_latch() -> None:
    client = _client()
    resp = client.post(
        f"/claims/{SC01}/evaluate",
        json={
            "signal_sources": ["rules", "rag"],
            "source_decisions": {
                "rules": "reject_draft",
                "rag": "approve_recommend",
            },
        },
    )
    assert resp.status_code == 403
    assert _error_code(resp) == ErrorCode.LATCH_REQUIRED.value
    body = resp.json()["detail"]
    assert body.get("route_id") == "R-CONFLICT-RULES-RAG"
    assert body.get("human_latch_required") is True

    led = client.get(f"/claims/{SC01}/ledger")
    assert led.status_code == 200
    items = led.json()["items"]
    assert any(
        i["route_id"] == "R-CONFLICT-RULES-RAG"
        and i["decision_type"] == "fail_closed_human_latch"
        and i["validator_score"] == 0.0
        for i in items
    )


def test_handbook_ops_alone_reject_fails() -> None:
    client = _client()
    # 材料齐全的 SC-01 通赔路径上强制 handbook_ops 独撑拒赔意图
    client.post(
        f"/claims/{SC01}/materials",
        json={
            "material_codes": ["MEDICAL_INVOICE", "DIAGNOSIS_REPORT"],
            "image_ids": ["IMG-MEDICAL_INVOICE", "IMG-DIAGNOSIS_REPORT"],
        },
    )
    resp = client.post(
        f"/claims/{SC01}/evaluate",
        json={
            "retrieval_profile": "handbook_ops",
            "force_reject_with_handbook_only": True,
        },
    )
    assert resp.status_code == 422
    assert _error_code(resp) == ErrorCode.VALIDATION_FAILED.value
    msg = resp.json()["detail"].get("message", "")
    assert "handbook_ops" in msg


def test_sc02_with_handbook_ops_profile_ok_when_clause_citations() -> None:
    """真实拒赔路径：handbook_ops 画像但引用含条款类时可通过。"""
    client = _client()
    resp = client.post(
        f"/claims/{SC02}/evaluate",
        json={"retrieval_profile": "handbook_ops"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision_type"] == "reject_draft"
    assert body["retrieval_profile"] == "handbook_ops"
    assert body["citations"]


def test_track_a_router_reproducible_same_fixture() -> None:
    client = _client()
    first = client.post(f"/claims/{SC02}/evaluate").json()
    reset_service()
    client2 = TestClient(app)
    second = client2.post(f"/claims/{SC02}/evaluate").json()
    assert first["route_id"] == second["route_id"]
    assert first["retrieval_profile"] == second["retrieval_profile"]
    assert first["decision_type"] == second["decision_type"]
    assert first["validator_score"] == second["validator_score"]


def test_machine_check_router_ledger_reproducible() -> None:
    client = _client()
    outcome = run_machine_check(
        client,
        MachineCheck(type="router_ledger_reproducible", params={"case_id": SC02}),
    )
    assert outcome.ok, outcome.detail

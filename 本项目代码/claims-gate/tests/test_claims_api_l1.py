"""接缝：Claims HTTP API — L1 只读案件头，门禁态可达 MATERIALS_INTAKE。"""

from __future__ import annotations

from fastapi.testclient import TestClient

from claims_api.api import app, reset_service


def test_get_claim_header_returns_l1_fields_and_materials_intake() -> None:
    reset_service()
    client = TestClient(app)
    resp = client.get("/claims/CLM-SC01-001")
    assert resp.status_code == 200
    body = resp.json()
    assert body["case_id"] == "CLM-SC01-001"
    assert body["policy_no"]
    assert body["product_code"]
    assert body["clause_version"]
    assert body["loss_date"]
    assert "endorsement_flags" in body
    assert "claim_amount_claimed" in body
    assert "image_ids" in body
    assert body["gate_status"] == "MATERIALS_INTAKE"
    assert body["inference_track"] == "deterministic"
    assert body["document_status"] is None
    assert body["payout_ready"] is False


def test_list_claims_returns_seed_summaries() -> None:
    reset_service()
    client = TestClient(app)
    resp = client.get("/claims")
    assert resp.status_code == 200
    items = resp.json()["items"]
    ids = {row["case_id"] for row in items}
    assert "CLM-SC01-001" in ids
    assert "CLM-SC02-001" in ids
    assert "CLM-SC03-001" in ids
    for row in items:
        assert "gate_status" in row
        assert "inference_track" in row
        assert "document_status" in row
        assert "payout_ready" in row


def test_health_endpoint() -> None:
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

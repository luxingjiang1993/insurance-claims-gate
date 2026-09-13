"""接缝：理赔 HTTP API — SC-01 一次补件 → 补传 → 通赔建议（轨 A 确定性）。

主缝对齐 SPEC：外部可观察 HTTP 行为 + machine_check(type, params)。
Rewrote from: REF-MISSIONS, REF-COURSE-03
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from claims_api.api import app, reset_service
from missions.checks import run_machine_check
from missions.models import MachineCheck

CASE_ID = "CLM-SC01-001"
LEGAL_ANCHOR = "保险法》第二十二条"
LEGAL_ANCHOR_ALT = "保险法》第22条"


def _client() -> TestClient:
    reset_service()
    return TestClient(app)


def test_sc01_missing_invoice_evaluate_to_pending_supplement() -> None:
    client = _client()
    resp = client.post(f"/claims/{CASE_ID}/evaluate")
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision_type"] == "supplement"
    assert body["gate_status"] == "PENDING_SUPPLEMENT"
    assert body["document_status"] == "DRAFT_EXPORT"
    assert body["payout_ready"] is False
    assert body["inference_track"] == "deterministic"
    assert body["one_shot_hash"]
    checklist = body["supplement_checklist"]
    assert isinstance(checklist, list) and len(checklist) >= 1
    codes = {item["code"] for item in checklist}
    assert "MEDICAL_INVOICE" in codes
    # 一次补件须列出全部缺项（夹具至少两项，便于拆轮负例）
    assert len(codes) >= 2
    for item in checklist:
        assert item["name_zh"]
        assert "required" in item
        assert item["example"]


def test_sc01_supplement_draft_export_fields_complete() -> None:
    client = _client()
    ev = client.post(f"/claims/{CASE_ID}/evaluate")
    assert ev.status_code == 200
    one_shot = ev.json()["one_shot_hash"]

    resp = client.post(
        f"/claims/{CASE_ID}/documents/export",
        json={
            "document_type": "supplement_notice",
            "document_status": "DRAFT_EXPORT",
        },
    )
    assert resp.status_code == 200
    doc = resp.json()
    assert doc["document_status"] == "DRAFT_EXPORT"
    assert doc["case_id"] == CASE_ID
    assert doc["policy_no"]
    assert doc["notify_time"]
    assert doc["supplement_deadline"]
    assert doc["contact"]
    assert doc["one_shot_hash"] == one_shot
    assert doc["legal_basis"]
    assert LEGAL_ANCHOR in doc["legal_basis"] or LEGAL_ANCHOR_ALT in doc["legal_basis"]
    missing = doc["missing_items"]
    assert isinstance(missing, list) and missing
    for item in missing:
        assert item["code"]
        assert item["name_zh"]
        assert "required" in item
        assert item["example"]


def test_sc01_same_hash_split_round_rejected() -> None:
    client = _client()
    ev = client.post(f"/claims/{CASE_ID}/evaluate")
    assert ev.status_code == 200
    one_shot = ev.json()["one_shot_hash"]

    full_codes = [item["code"] for item in ev.json()["supplement_checklist"]]
    assert len(full_codes) >= 2
    # 同 hash 下拆轮：只通知部分缺项
    resp = client.post(
        f"/claims/{CASE_ID}/supplement/notify",
        json={
            "one_shot_hash": one_shot,
            "missing_item_codes": [full_codes[0]],
        },
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert detail["error_code"] == "VALIDATION_FAILED"


def test_sc01_upload_invoice_then_approve_recommend() -> None:
    client = _client()
    ev = client.post(f"/claims/{CASE_ID}/evaluate")
    assert ev.status_code == 200
    assert ev.json()["decision_type"] == "supplement"
    missing_codes = [item["code"] for item in ev.json()["supplement_checklist"]]

    up = client.post(
        f"/claims/{CASE_ID}/materials",
        json={
            "material_codes": missing_codes,
            "image_ids": [f"IMG-{c}" for c in missing_codes],
        },
    )
    assert up.status_code == 200

    again = client.post(f"/claims/{CASE_ID}/evaluate")
    assert again.status_code == 200
    body = again.json()
    assert body["decision_type"] == "approve_recommend"
    assert body["gate_status"] in ("PRIMARY_REVIEW", "HUMAN_LATCH", "PENDING_APPROVAL")
    assert body["document_status"] == "DRAFT_EXPORT"
    assert body["payout_ready"] is False
    assert body["inference_track"] == "deterministic"


def test_machine_check_sc01_one_shot_flow_passes() -> None:
    """轨 A：SC-01 主路径 machine_check 稳定绿，不依赖 LLM。"""
    reset_service()
    client = TestClient(app)
    outcome = run_machine_check(
        client,
        MachineCheck(
            type="sc01_one_shot_supplement_approve",
            params={"case_id": CASE_ID},
        ),
    )
    assert outcome.ok, outcome.detail


def test_machine_check_one_shot_split_round_fails() -> None:
    reset_service()
    client = TestClient(app)
    outcome = run_machine_check(
        client,
        MachineCheck(
            type="one_shot_split_round_rejected",
            params={"case_id": CASE_ID},
        ),
    )
    assert outcome.ok, outcome.detail

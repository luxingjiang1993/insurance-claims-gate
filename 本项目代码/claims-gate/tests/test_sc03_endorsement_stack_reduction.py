"""接缝：SC-03 效力栈减赔 + calc_steps（轨 A 确定性）。

主缝：HTTP evaluate/export + machine_check；检索 endorsement_priority 顺序；
条款冲突 fail-closed。
Rewrote from: REF-CASE-KB, REF-MISSIONS, REF-COURSE-04
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from claims_api.api import app, reset_service
from claims_api.error_codes import ErrorCode
from missions.checks import run_machine_check
from missions.models import MachineCheck, RoleName
from missions.rag import KnowledgeBase

ROOT = Path(__file__).resolve().parents[1]
KB_ROOT = ROOT / "knowledge_base"
CASE_ID = "CLM-SC03-001"


def _client() -> TestClient:
    reset_service()
    return TestClient(app)


def test_endorsement_priority_retrieve_orders_endorsement_before_main() -> None:
    """endorsement_priority 画像下先批单再主险。"""
    kb = KnowledgeBase(KB_ROOT)
    hits = kb.retrieve(
        "免赔额 赔付比例 保险责任",
        role=RoleName.WORKER,
        profile="endorsement_priority",
        top_k=5,
    )
    assert hits, "应召回批单与主险候选"
    types_in_order: list[str] = []
    for cite in hits:
        chunk = kb.resolve_clause(cite.doc_id, cite.clause_item, cite.doc_version)
        assert chunk is not None
        types_in_order.append(chunk.doc_type)
    assert "endorsement" in types_in_order
    assert "main_policy" in types_in_order
    assert types_in_order.index("endorsement") < types_in_order.index("main_policy")


def test_sc03_evaluate_reduce_with_authority_stack_and_calc_steps() -> None:
    """批单缩责 → 减赔草案；citations 含 authority_rank / overridden_by；calc_steps 可复核。"""
    client = _client()
    resp = client.post(f"/claims/{CASE_ID}/evaluate")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["decision_type"] == "reduce"
    assert body["gate_status"] == "ADJUSTING"
    assert body["document_status"] == "DRAFT_EXPORT"
    assert body["payout_ready"] is False
    assert body["inference_track"] == "deterministic"
    assert body["human_latch_required"] is True

    citations = body["citations"]
    assert isinstance(citations, list) and len(citations) >= 2
    for c in citations:
        assert c.get("doc_id")
        assert c.get("clause_item")
        assert c.get("doc_version") or c.get("effective_date")
        assert "authority_rank" in c

    ranks = {c["clause_item"]: c["authority_rank"] for c in citations}
    assert ranks.get("END-2-DEDUCT", 99) < ranks.get("ART-6-DEDUCT", 0)

    overridden = [c for c in citations if c.get("overridden_by")]
    assert overridden, "主险被批单覆盖时应暴露 overridden_by"
    for c in overridden:
        ob = c["overridden_by"]
        assert ob.get("doc_id") == "PA-ACC-END-001"
        assert ob.get("clause_item") == "END-2-DEDUCT"

    steps = body["calc_steps"]
    assert isinstance(steps, list) and steps
    by_step = {s["step"]: s for s in steps}
    assert by_step["claimed"]["value"] == 10000
    assert by_step["deductible"]["value"] == 500
    assert by_step["ratio"]["value"] == 0.8
    assert by_step["result"]["value"] == 7600
    assert by_step["deductible"].get("source_clause_item") == "END-2-DEDUCT"


def test_sc03_reduction_export_reuses_citations_and_calc_steps() -> None:
    """减赔导出复用 citations 与 calc_steps；不得谎称出款就绪。"""
    client = _client()
    ev = client.post(f"/claims/{CASE_ID}/evaluate")
    assert ev.status_code == 200
    decision = ev.json()

    resp = client.post(
        f"/claims/{CASE_ID}/documents/export",
        json={
            "document_type": "reduction_notice",
            "document_status": "DRAFT_EXPORT",
        },
    )
    assert resp.status_code == 200, resp.text
    doc = resp.json()
    assert doc["document_type"] == "reduction_notice"
    assert doc["document_status"] == "DRAFT_EXPORT"
    assert doc["case_id"] == CASE_ID
    assert doc["citations"] == decision["citations"]
    assert doc["calc_steps"] == decision["calc_steps"]
    assert doc.get("payout_ready") is False
    assert doc.get("inference_track") == "deterministic"


def test_sc03_calc_conflict_with_clause_fails_closed() -> None:
    """提出与批单条款冲突的免赔/比例时失败关闭，不静默改金额。"""
    client = _client()
    # 主险数字 100 / 100%，与批单 500 / 80% 冲突
    resp = client.post(
        f"/claims/{CASE_ID}/evaluate",
        json={"proposed_deductible": 100, "proposed_ratio": 1.0},
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert detail["error_code"] == ErrorCode.VALIDATION_FAILED.value


def test_machine_check_sc03_endorsement_stack_reduction_passes() -> None:
    """轨 A：SC-03 主路径 machine_check 稳定绿。"""
    reset_service()
    client = TestClient(app)
    outcome = run_machine_check(
        client,
        MachineCheck(
            type="sc03_endorsement_stack_reduction",
            params={"case_id": CASE_ID},
        ),
    )
    assert outcome.ok, outcome.detail

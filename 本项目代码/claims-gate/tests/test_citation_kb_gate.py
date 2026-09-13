"""接缝：条款项级 citation 落库门（doc_id + clause_item + doc_version）。

Rewrote from: REF-CASE-KB, REF-MISSIONS
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from claims_api.api import app, reset_service
from claims_api.error_codes import ErrorCode
from missions.checks import run_machine_check
from missions.models import MachineCheck
from missions.rag import KnowledgeBase
from missions.retrieval_profiles import RETRIEVAL_PROFILES

ROOT = Path(__file__).resolve().parents[1]
KB_ROOT = ROOT / "knowledge_base"


def test_resolve_clause_hits_triple() -> None:
    """合法三联键可解析到条款项条目。"""
    kb = KnowledgeBase(KB_ROOT)
    chunk = kb.resolve_clause(
        doc_id="PA-ACC-MAIN",
        clause_item="ART-5-EXCL",
        doc_version="2024.1",
    )
    assert chunk is not None
    assert chunk.clause_item == "ART-5-EXCL"
    assert chunk.doc_version == "2024.1"


def test_resolve_clause_rejects_doc_only_or_wrong_item_or_version() -> None:
    """文档存在但条款项错/版本错 → 不得通过（非文档级门）。"""
    kb = KnowledgeBase(KB_ROOT)
    assert kb.resolve_clause("PA-ACC-MAIN", "ART-5-EXCL", "2024.1") is not None
    # 库外文档
    assert kb.resolve_clause("PA-FAKE-DOC", "ART-5-EXCL", "2024.1") is None
    # 错条款项（文档存在）
    assert kb.resolve_clause("PA-ACC-MAIN", "ART-999-HALLUCINATION", "2024.1") is None
    # 版本不匹配
    assert kb.resolve_clause("PA-ACC-MAIN", "ART-5-EXCL", "2099.9") is None


def test_http_validate_citation_ok_and_fail_maps_error_code() -> None:
    reset_service()
    client = TestClient(app)

    ok = client.post(
        "/kb/citations/validate",
        json={
            "doc_id": "PA-ACC-MAIN",
            "clause_item": "ART-5-EXCL",
            "doc_version": "2024.1",
            "quote": "疾病",
        },
    )
    assert ok.status_code == 200, ok.text
    body = ok.json()
    assert body["ok"] is True

    bad = client.post(
        "/kb/citations/validate",
        json={
            "doc_id": "PA-ACC-MAIN",
            "clause_item": "ART-999-HALLUCINATION",
            "doc_version": "2024.1",
            "quote": "幻觉条款",
        },
    )
    assert bad.status_code == 422
    detail = bad.json()["detail"]
    assert detail["error_code"] == ErrorCode.CITATION_NOT_IN_KB.value


def test_machine_check_citation_in_kb_hallucination_fails() -> None:
    """machine_check 独立验收：幻觉条款不过门。"""
    reset_service()
    client = TestClient(app)
    outcome = run_machine_check(
        client,
        MachineCheck(
            type="citation_in_kb",
            params={
                "doc_id": "PA-GHOST",
                "clause_item": "ART-X",
                "doc_version": "1.0",
            },
        ),
    )
    assert not outcome.ok
    assert ErrorCode.CITATION_NOT_IN_KB.value in outcome.detail

    wrong_item = run_machine_check(
        client,
        MachineCheck(
            type="citation_in_kb",
            params={
                "doc_id": "PA-ACC-MAIN",
                "clause_item": "ART-999-HALLUCINATION",
                "doc_version": "2024.1",
            },
        ),
    )
    assert not wrong_item.ok
    assert ErrorCode.CITATION_NOT_IN_KB.value in wrong_item.detail

    wrong_ver = run_machine_check(
        client,
        MachineCheck(
            type="citation_in_kb",
            params={
                "doc_id": "PA-ACC-MAIN",
                "clause_item": "ART-5-EXCL",
                "doc_version": "2099.9",
            },
        ),
    )
    assert not wrong_ver.ok
    assert ErrorCode.CITATION_NOT_IN_KB.value in wrong_ver.detail

    good = run_machine_check(
        client,
        MachineCheck(
            type="citation_in_kb",
            params={
                "doc_id": "PA-ACC-END-001",
                "clause_item": "END-1-NARROW",
                "doc_version": "2025.3",
            },
        ),
    )
    assert good.ok, good.detail


def test_effective_date_as_version_key() -> None:
    """生效日可作为 doc_version 的等价键。"""
    kb = KnowledgeBase(KB_ROOT)
    chunk = kb.resolve_clause("PA-ACC-MAIN", "ART-5-EXCL", "2024-01-01")
    assert chunk is not None
    assert kb.validate_citation(
        {
            "doc_id": "PA-ACC-MAIN",
            "clause_item": "ART-5-EXCL",
            "effective_date": "2024-01-01",
        }
    ).ok


def test_gate_does_not_use_max_similarity_for_pass() -> None:
    """全文最大相似不得冒充条款项落库通过。"""
    kb = KnowledgeBase(KB_ROOT)
    # 摘录与除外条文高度相似，但三联键错误 → 仍失败
    assert (
        kb.validate_citation(
            {
                "doc_id": "PA-ACC-MAIN",
                "clause_item": "WRONG-ITEM",
                "doc_version": "2024.1",
                "quote": "因疾病导致的摔伤或意外伤害不在保险责任范围内",
            }
        ).ok
        is False
    )


def test_retrieval_profiles_distinguish_current_and_endorsement() -> None:
    assert "clause_v_current" in RETRIEVAL_PROFILES
    assert "endorsement_priority" in RETRIEVAL_PROFILES
    assert RETRIEVAL_PROFILES["clause_v_current"]["id"] != RETRIEVAL_PROFILES[
        "endorsement_priority"
    ]["id"]


def test_kb_has_main_and_endorsement_samples_with_version() -> None:
    """至少支撑 SC-02/SC-03 的主险与批单样例。"""
    kb = KnowledgeBase(KB_ROOT)
    main = kb.resolve_clause("PA-ACC-MAIN", "ART-5-EXCL", "2024.1")
    endo = kb.resolve_clause("PA-ACC-END-001", "END-1-NARROW", "2025.3")
    assert main is not None and main.effective_date
    assert endo is not None and endo.effective_date
    assert endo.authority_rank < main.authority_rank

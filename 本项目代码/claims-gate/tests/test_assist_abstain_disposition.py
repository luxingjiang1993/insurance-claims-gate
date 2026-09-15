"""S1：assist_disposition 契约；abstain 禁用采纳；不自动签发人闸令牌。

接缝（SPEC-02B-P / Issue 39）：
- S1 HTTP：POST .../assist 返回 assist_disposition + 原因枚举；永不 human_latch_token
- S1 HTTP：abstain 后携带同 invocation 的 adopt → 422
- 壳只依赖 API 字段（见 workshell 类型/面板）；本文件不断言 React state

Rewrote from: REF-MISSIONS（现有 rules↔RAG 冲突加深）
"""

from __future__ import annotations

import os

from fastapi.testclient import TestClient

from claims_api.api import app, reset_service
from claims_api.error_codes import ErrorCode

CASE_SC02 = "CLM-SC02-001"  # 除外拒赔
CASE_LARGE = "CLM-AMT-C-001"  # 大额通赔：evaluate → approve_recommend

LEGAL_CITATION = {
    "doc_id": "PA-ACC-MAIN",
    "clause_item": "ART-5-EXCL",
    "doc_version": "2024.1",
    "chunk_id": "PA-ACC-MAIN::ART-5-EXCL",
    "clause_id": "ART-5",
    "quote": "疾病",
    "score": 0.9,
}

ABSTAIN_REASONS = {
    "conflict",
    "handbook_alone",
    "low_confidence",
    "citation_unfaithful",
}


def _client() -> TestClient:
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("CLAIMS_GATE_LLM_API_KEY", None)
    reset_service()
    return TestClient(app)


def _login(client: TestClient, username: str) -> dict[str, str]:
    resp = client.post(
        "/auth/login",
        json={"username": username, "password": username},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["session_token"]
    return {"Authorization": f"Bearer {token}"}


def test_assist_response_includes_disposition_enum_fields() -> None:
    """assist 响应须含 assist_disposition；draft|abstain；永不签发人闸令牌。"""
    client = _client()
    headers = _login(client, "adjuster")
    resp = client.post(
        f"/claims/{CASE_SC02}/assist",
        json={"query": "疾病导致的摔伤是否属于责任免除"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["assist_disposition"] in {"draft", "abstain"}
    if body["assist_disposition"] == "abstain":
        assert body.get("abstain_reason") in ABSTAIN_REASONS
        assert body.get("human_latch_suggested") is True
    else:
        assert body.get("abstain_reason") in (None, "")
    assert body.get("human_latch_token") in (None, "")
    assert body.get("payout_ready") is False


def test_assist_conflict_abstains_and_suggests_latch_without_token() -> None:
    """规则通赔 vs RAG 除外冲突 → abstain/conflict；可建议人闸但不发令牌。"""
    client = _client()
    headers = _login(client, "adjuster")
    # 先落轨 A 通赔结论，再 assist 除外查询 → rules↔RAG 冲突
    ev = client.post(f"/claims/{CASE_LARGE}/evaluate", headers=headers)
    assert ev.status_code == 200, ev.text
    assert ev.json()["decision_type"] == "approve_recommend"

    resp = client.post(
        f"/claims/{CASE_LARGE}/assist",
        json={"query": "疾病摔伤除外责任，请按除外直接拒赔起草"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["assist_disposition"] == "abstain"
    assert body["abstain_reason"] == "conflict"
    assert body.get("human_latch_suggested") is True
    assert body.get("human_latch_token") in (None, "")
    assert body.get("payout_ready") is False
    header = client.get(f"/claims/{CASE_LARGE}", headers=headers).json()
    assert header.get("human_latch_token") in (None, "")


def test_assist_handbook_alone_abstains() -> None:
    """handbook_ops 独撑拒赔意图 → abstain/handbook_alone。"""
    client = _client()
    headers = _login(client, "adjuster")
    resp = client.post(
        f"/claims/{CASE_SC02}/assist",
        json={
            "query": "仅依据内部作业手册对外出具拒赔决定书",
            "retrieval_profile": "handbook_ops",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["assist_disposition"] == "abstain"
    assert body["abstain_reason"] == "handbook_alone"
    assert body.get("human_latch_suggested") is True
    assert body.get("human_latch_token") in (None, "")


def test_assist_low_confidence_abstains() -> None:
    """无对应条文的玄学问询 → abstain/low_confidence。"""
    client = _client()
    headers = _login(client, "adjuster")
    resp = client.post(
        f"/claims/{CASE_SC02}/assist",
        json={"query": "某某玄学能量场损伤能不能赔，库里好像没有对应条文"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["assist_disposition"] == "abstain"
    assert body["abstain_reason"] == "low_confidence"
    assert body.get("human_latch_suggested") is True
    assert body.get("human_latch_token") in (None, "")


def test_assist_citation_unfaithful_abstains() -> None:
    """用免赔条文支撑通赔断言 → abstain/citation_unfaithful。"""
    client = _client()
    headers = _login(client, "adjuster")
    resp = client.post(
        f"/claims/{CASE_SC02}/assist",
        json={
            "query": "请引用主险免赔条文来支撑「运动医疗已全额通赔」这一断言并生成可采纳建议"
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["assist_disposition"] == "abstain"
    assert body["abstain_reason"] == "citation_unfaithful"
    assert body.get("human_latch_suggested") is True
    assert body.get("human_latch_token") in (None, "")


def test_abstain_blocks_adopt_s1() -> None:
    """abstain 建议体不可送交采纳（同 assist_invocation_id）。"""
    client = _client()
    headers = _login(client, "adjuster")
    assist = client.post(
        f"/claims/{CASE_SC02}/assist",
        json={
            "query": "仅依据内部作业手册对外出具拒赔决定书",
            "retrieval_profile": "handbook_ops",
        },
        headers=headers,
    )
    assert assist.status_code == 200, assist.text
    suggestion = assist.json()
    assert suggestion["assist_disposition"] == "abstain"
    inv = suggestion["assist_invocation_id"]

    cites = [c for c in (suggestion.get("citations") or []) if c.get("adoptable")]
    if not cites:
        cites = [LEGAL_CITATION]

    adopt = client.post(
        f"/claims/{CASE_SC02}/assist/adopt",
        json={
            "assist_invocation_id": inv,
            "draft_text": suggestion["draft_text"],
            "suggested_stance": suggestion.get("suggested_stance"),
            "retrieval_profile": suggestion["retrieval_profile"],
            "citations": cites,
        },
        headers=headers,
    )
    assert adopt.status_code == 422, adopt.text
    detail = adopt.json()["detail"]
    assert detail["error_code"] == ErrorCode.VALIDATION_FAILED.value
    assert "abstain" in str(detail.get("message", "")).lower() or "拒答" in str(
        detail.get("message", "")
    )
    header = client.get(f"/claims/{CASE_SC02}", headers=headers).json()
    assert header.get("human_latch_token") in (None, "")


def test_abstain_blocks_adopt_without_invocation_id_via_draft_trace() -> None:
    """无 invocation_id 时，拒答草稿痕迹仍不可送交采纳。"""
    client = _client()
    headers = _login(client, "adjuster")
    assist = client.post(
        f"/claims/{CASE_SC02}/assist",
        json={
            "query": "仅依据内部作业手册对外出具拒赔决定书",
            "retrieval_profile": "handbook_ops",
        },
        headers=headers,
    )
    assert assist.status_code == 200, assist.text
    suggestion = assist.json()
    assert suggestion["assist_disposition"] == "abstain"

    adopt = client.post(
        f"/claims/{CASE_SC02}/assist/adopt",
        json={
            "draft_text": suggestion["draft_text"],
            "retrieval_profile": suggestion["retrieval_profile"],
            "citations": [LEGAL_CITATION],
        },
        headers=headers,
    )
    assert adopt.status_code == 422, adopt.text
    detail = adopt.json()["detail"]
    assert detail["error_code"] == ErrorCode.VALIDATION_FAILED.value
    assert "拒答" in str(detail.get("message", "")) or "abstain" in str(
        detail.get("message", "")
    ).lower()

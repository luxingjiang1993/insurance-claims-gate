"""S1：assist citation Schema 槽 + 三联门；非法不可采纳；采纳仍 evaluate。

接缝（SPEC-02B-P / Issue 37）：
- Schema：assist 建议体 citation 槽须含 doc_id+clause_item+doc_version
- S1 HTTP：POST .../assist/adopt 非法 citation → 422，H3=0
- S1 HTTP：合法 citation 采纳后 inference_track=deterministic（仍 evaluate）

Rewrote from: REF-COURSE-03
"""

from __future__ import annotations

import os

from fastapi.testclient import TestClient

from claims_api.api import app, reset_service
from claims_api.error_codes import ErrorCode
from missions.assist_schema import AssistSchemaError, validate_assist_suggestion_dict

CASE_SC02 = "CLM-SC02-001"

# 库外幻觉三联键（H3 负例）
ILLEGAL_CITATION = {
    "doc_id": "PA-GHOST",
    "clause_item": "ART-999-HALLUCINATION",
    "doc_version": "2099.9",
    "chunk_id": "ghost-chunk",
    "clause_id": "ART-999",
    "quote": "幻觉除外责任条款",
    "score": 0.99,
}

# 缺槽：有 doc_id 无 clause_item / doc_version
MISSING_SLOT_CITATION = {
    "doc_id": "PA-ACC-MAIN",
    "chunk_id": "c1",
    "clause_id": "ART-5",
    "quote": "疾病",
    "score": 0.8,
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


def _adoptable_citations(assist_body: dict) -> list[dict]:
    """从 assist 响应取可采纳 citation（须含三联键）。"""
    out = []
    for c in assist_body.get("citations") or []:
        if c.get("adoptable") is True:
            out.append(c)
    return out


# --- Schema 契约接缝 ---


def test_assist_schema_rejects_citation_missing_triple_slots() -> None:
    """citation 槽缺 clause_item 或 doc_version → Schema 硬停。"""
    bad = {
        "assist_invocation_id": "inv-1",
        "inference_track": "llm_optional",
        "query": "q",
        "retrieval_profile": "clause_v_current",
        "draft_text": "辅助建议",
        "used_llm": False,
        "degraded": True,
        "citations": [MISSING_SLOT_CITATION],
    }
    try:
        validate_assist_suggestion_dict(bad)
        raise AssertionError("expected AssistSchemaError")
    except AssistSchemaError as exc:
        assert "clause_item" in str(exc) or "doc_version" in str(exc)


def test_assist_schema_rejects_illegal_shape_empty_doc_id() -> None:
    """doc_id 空串不得过 Schema。"""
    bad = {
        "assist_invocation_id": "inv-2",
        "inference_track": "llm_optional",
        "query": "q",
        "retrieval_profile": "clause_v_current",
        "draft_text": "辅助建议",
        "used_llm": False,
        "degraded": True,
        "citations": [
            {
                "doc_id": "",
                "clause_item": "ART-5-EXCL",
                "doc_version": "2024.1",
                "chunk_id": "c",
                "clause_id": "ART-5",
                "quote": "疾病",
                "score": 0.5,
            }
        ],
    }
    try:
        validate_assist_suggestion_dict(bad)
        raise AssertionError("expected AssistSchemaError")
    except AssistSchemaError:
        pass


def test_assist_schema_accepts_minimal_with_triple() -> None:
    """最小合法建议体：citation 含三联键即可过 Schema（落库门另测）。"""
    good = {
        "assist_invocation_id": "inv-ok",
        "inference_track": "llm_optional",
        "query": "疾病除外",
        "retrieval_profile": "clause_v_current",
        "draft_text": "【辅助建议】仅供人审",
        "used_llm": False,
        "degraded": True,
        "assist_disposition": "draft",
        "citations": [
            {
                "doc_id": "PA-ACC-MAIN",
                "clause_item": "ART-5-EXCL",
                "doc_version": "2024.1",
                "chunk_id": "PA-ACC-MAIN::1",
                "clause_id": "ART-5",
                "quote": "疾病",
                "score": 0.9,
                "adoptable": True,
            }
        ],
    }
    validate_assist_suggestion_dict(good)


# --- S1 HTTP：assist 响应槽 + 非法不可采纳 + 合法仍 evaluate ---


def test_assist_response_citations_carry_schema_triple_slots() -> None:
    """POST /assist 返回的每条 citation 须含 Schema 三联槽。"""
    client = _client()
    headers = _login(client, "adjuster")
    resp = client.post(
        f"/claims/{CASE_SC02}/assist",
        json={"query": "疾病导致的摔伤是否属于责任免除"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    validate_assist_suggestion_dict(body)
    assert body["citations"], "须有 citation 提名"
    for c in body["citations"]:
        assert c.get("doc_id"), c
        assert c.get("clause_item"), c
        assert c.get("doc_version"), c


def test_adopt_empty_citations_rejected() -> None:
    """S1：采纳不带 citation / 空数组 → 不可采纳。"""
    client = _client()
    headers = _login(client, "adjuster")
    for payload in (
        {
            "draft_text": "无引用采纳",
            "retrieval_profile": "clause_v_current",
        },
        {
            "draft_text": "空引用采纳",
            "retrieval_profile": "clause_v_current",
            "citations": [],
        },
    ):
        adopt = client.post(
            f"/claims/{CASE_SC02}/assist/adopt",
            json=payload,
            headers=headers,
        )
        assert adopt.status_code == 422, adopt.text
        assert adopt.json()["detail"]["error_code"] == ErrorCode.VALIDATION_FAILED.value


def test_adopt_illegal_citation_rejected_h3() -> None:
    """H3：采纳路径提交幻觉 citation → 422，不得写成权威草案。"""
    client = _client()
    headers = _login(client, "adjuster")
    adopt = client.post(
        f"/claims/{CASE_SC02}/assist/adopt",
        json={
            "draft_text": "试图用假引用采纳",
            "retrieval_profile": "clause_v_current",
            "citations": [ILLEGAL_CITATION],
        },
        headers=headers,
    )
    assert adopt.status_code == 422, adopt.text
    detail = adopt.json()["detail"]
    assert detail["error_code"] == ErrorCode.CITATION_NOT_IN_KB.value
    # 不得留下 payout / 人闸令牌
    header = client.get(f"/claims/{CASE_SC02}", headers=headers).json()
    assert header.get("payout_ready") is False
    assert header.get("human_latch_token") in (None, "")


def test_adopt_missing_triple_slot_rejected() -> None:
    """缺 Schema 槽的 citation 不可采纳。"""
    client = _client()
    headers = _login(client, "adjuster")
    adopt = client.post(
        f"/claims/{CASE_SC02}/assist/adopt",
        json={
            "draft_text": "缺槽引用",
            "retrieval_profile": "clause_v_current",
            "citations": [MISSING_SLOT_CITATION],
        },
        headers=headers,
    )
    assert adopt.status_code == 422, adopt.text
    detail = adopt.json()["detail"]
    assert detail["error_code"] in {
        ErrorCode.CITATION_NOT_IN_KB.value,
        ErrorCode.VALIDATION_FAILED.value,
    }


def test_adopt_legal_citations_still_evaluates() -> None:
    """合法 citation 可采纳，但权威结果须来自 evaluate（deterministic）。"""
    client = _client()
    headers = _login(client, "adjuster")
    assist = client.post(
        f"/claims/{CASE_SC02}/assist",
        json={"query": "疾病摔伤除外责任"},
        headers=headers,
    )
    assert assist.status_code == 200, assist.text
    suggestion = assist.json()
    cites = _adoptable_citations(suggestion)
    assert cites, "测试前置：须有可采纳 citation"

    adopt = client.post(
        f"/claims/{CASE_SC02}/assist/adopt",
        json={
            "assist_invocation_id": suggestion["assist_invocation_id"],
            "draft_text": suggestion["draft_text"],
            "suggested_stance": suggestion["suggested_stance"],
            "retrieval_profile": suggestion["retrieval_profile"],
            "citations": cites,
        },
        headers=headers,
    )
    assert adopt.status_code == 200, adopt.text
    decision = adopt.json()
    assert decision["inference_track"] == "deterministic"
    assert decision["payout_ready"] is False
    assert decision["decision_type"] == "reject_draft"
    assert "suggested_stance" not in decision

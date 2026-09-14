"""S2：真 LangSmith 上报（有 Key）或显式跳过。

Mock 不得冒充 Pilot Complete。本文件用真实 Client 校验
evaluate / assist / latch 三笔 span；无真实 Key 时 skip。

运行：pytest -m langsmith_integration -q

Rewrote from: REF-CASE-EVAL-ADVISOR, REF-MISSIONS
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from claims_api import langsmith_trace
from claims_api.api import app, reset_service

pytestmark = pytest.mark.langsmith_integration

CASE_SC02 = "CLM-SC02-001"


def _has_real_key() -> bool:
    key = (
        os.environ.get("LANGCHAIN_API_KEY")
        or os.environ.get("LANGSMITH_API_KEY")
        or ""
    ).strip()
    if not key:
        return False
    # 排除明显 mock 占位（含 mock 字样）；真 Key 仍可通过
    lower = key.lower()
    return "mock" not in lower and "not_real" not in lower


@pytest.mark.skipif(not _has_real_key(), reason="需要真实 LANGCHAIN_API_KEY")
def test_real_langsmith_evaluate_assist_latch_spans_and_ledger() -> None:
    """真 Key：三关键动作 ledger 含 trace_id，且 LangSmith 可读回同名 run。"""
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_PROJECT", "claims-gate-s2")
    langsmith_trace.reset_client_override()
    reset_service()
    client = TestClient(app)
    adj_login = client.post(
        "/auth/login",
        json={"username": "adjuster", "password": "adjuster"},
    )
    assert adj_login.status_code == 200
    adj = {"Authorization": f"Bearer {adj_login.json()['session_token']}"}
    sup_login = client.post(
        "/auth/login",
        json={"username": "supervisor", "password": "supervisor"},
    )
    assert sup_login.status_code == 200
    sup = {"Authorization": f"Bearer {sup_login.json()['session_token']}"}

    assert client.post(f"/claims/{CASE_SC02}/evaluate", headers=adj).status_code == 200
    assert (
        client.post(
            f"/claims/{CASE_SC02}/assist",
            json={"query": "除外责任"},
            headers=adj,
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/claims/{CASE_SC02}/human-latch/approve",
            json={"approved_by": "supervisor"},
            headers=sup,
        ).status_code
        == 200
    )

    led = client.get(f"/claims/{CASE_SC02}/ledger", headers=adj)
    by_type = {i["decision_type"]: i for i in led.json()["items"]}
    expected = {
        "reject_draft": "evaluate",
        "assist_suggestion": "assist",
        "human_latch_approve": "latch",
    }
    from langsmith import Client

    ls = Client()
    for decision_type, span_name in expected.items():
        assert decision_type in by_type
        item = by_type[decision_type]
        assert item.get("retrieval_profile")
        tid = item.get("trace_id")
        assert tid, f"{decision_type} 须有 trace_id"
        # 优先新 API；旧 Client 回退 read_run
        if hasattr(ls, "runs") and hasattr(ls.runs, "retrieve"):
            run = ls.runs.retrieve(tid)
        else:
            run = ls.read_run(tid)
        assert run is not None
        assert getattr(run, "name", None) == span_name

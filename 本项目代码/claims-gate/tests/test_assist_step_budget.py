"""接缝：assist 步数预算≤4（票 49 / P-A4）。

S0：预算常量、有序强制、超步/未知步拒绝、架构 app-owned、Rewrote from。
S1：draft_assist 跑满 retrieve→gate→draft→self-check；响应可测步迹。

Rewrote from: REF-CASE-DELIBERATIVE
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def test_module_declares_app_owned_and_rewrote_from() -> None:
    """架构声明 app-owned；handoff 含 Rewrote from: REF-CASE-DELIBERATIVE。"""
    text = (SRC / "missions" / "assist_step_budget.py").read_text(encoding="utf-8")
    assert "Rewrote from" in text
    assert "REF-CASE-DELIBERATIVE" in text
    assert "app-owned" in text
    assert "LangGraph" in text  # 口头边界：可用图库但不卖第二套平台

    from missions.assist_step_budget import (
        ASSIST_ORCHESTRATION_OWNER,
        ASSIST_STEP_BUDGET,
        ASSIST_ORCHESTRATION_STEPS,
        REWROTE_FROM,
    )

    assert ASSIST_STEP_BUDGET == 4
    assert ASSIST_ORCHESTRATION_STEPS == (
        "retrieve",
        "gate",
        "draft",
        "self-check",
    )
    assert ASSIST_ORCHESTRATION_OWNER == "app-owned"
    assert REWROTE_FROM == "REF-CASE-DELIBERATIVE"


def test_budget_records_four_steps_in_order() -> None:
    """接缝：恰 4 步按 retrieve→gate→draft→self-check 记录并可完成。"""
    from missions.assist_step_budget import AssistStepBudget

    budget = AssistStepBudget()
    for step in ("retrieve", "gate", "draft", "self-check"):
        budget.record(step)
    budget.assert_complete()
    assert budget.steps == ("retrieve", "gate", "draft", "self-check")
    payload = budget.to_dict()
    assert payload["orchestration_step_budget"] == 4
    assert payload["orchestration_owner"] == "app-owned"
    assert payload["orchestration_steps"] == [
        "retrieve",
        "gate",
        "draft",
        "self-check",
    ]


def test_budget_rejects_unknown_step() -> None:
    """接缝：未知步名强制失败。"""
    from missions.assist_step_budget import AssistStepBudget, AssistStepBudgetError

    budget = AssistStepBudget()
    with pytest.raises(AssistStepBudgetError, match="未知"):
        budget.record("fan-out")


def test_budget_rejects_out_of_order() -> None:
    """接缝：步序错误强制失败。"""
    from missions.assist_step_budget import AssistStepBudget, AssistStepBudgetError

    budget = AssistStepBudget()
    budget.record("retrieve")
    with pytest.raises(AssistStepBudgetError, match="步序"):
        budget.record("draft")


def test_budget_rejects_fifth_step() -> None:
    """接缝：超出预算≤4 强制失败。"""
    from missions.assist_step_budget import AssistStepBudget, AssistStepBudgetError

    budget = AssistStepBudget()
    for step in ("retrieve", "gate", "draft", "self-check"):
        budget.record(step)
    with pytest.raises(AssistStepBudgetError, match="预算"):
        budget.record("retrieve")


def test_budget_incomplete_assert_fails() -> None:
    """接缝：未跑满 4 步不得宣称完成。"""
    from missions.assist_step_budget import AssistStepBudget, AssistStepBudgetError

    budget = AssistStepBudget()
    budget.record("retrieve")
    with pytest.raises(AssistStepBudgetError, match="未完成"):
        budget.assert_complete()


def test_draft_assist_enforces_four_step_budget() -> None:
    """S1：draft_assist 编排步迹恰为 4 步；owner=app-owned。"""
    from missions.track_llm_optional.pipeline import draft_assist

    result = draft_assist(
        "疾病除外责任",
        retrieval_profile="clause_v_current",
        enable_llm=False,
        top_k=2,
    )
    body = result.to_dict()
    assert body["orchestration_step_budget"] == 4
    assert body["orchestration_owner"] == "app-owned"
    assert body["orchestration_steps"] == [
        "retrieve",
        "gate",
        "draft",
        "self-check",
    ]
    # 既有契约字段保持
    assert body["inference_track"] == "llm_optional"
    assert body["payout_ready"] is False
    assert body["human_latch_token"] is None
    assert body["assist_disposition"] in {"draft", "abstain"}


def test_assist_http_exposes_orchestration_budget() -> None:
    """S1 HTTP：POST .../assist 暴露四步预算字段（Decision 2）。"""
    import os

    from fastapi.testclient import TestClient

    from claims_api.api import app, reset_service

    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("CLAIMS_GATE_LLM_API_KEY", None)
    reset_service()
    client = TestClient(app)
    login = client.post(
        "/auth/login",
        json={"username": "adjuster", "password": "adjuster"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['session_token']}"}
    resp = client.post(
        "/claims/CLM-SC02-001/assist",
        headers=headers,
        json={"query": "疾病除外", "enable_llm": False},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["orchestration_step_budget"] == 4
    assert body["orchestration_owner"] == "app-owned"
    assert body["orchestration_steps"] == [
        "retrieve",
        "gate",
        "draft",
        "self-check",
    ]
    assert body["payout_ready"] is False
    assert body.get("human_latch_token") is None

"""接缝 S0：本案流水 + 本地 JSONL span（无 LangSmith）。

验收：
- GET /claims/{id}/ledger 可回放 evaluate / assist / latch 关键动作
- CLAIMS_GATE_LOCAL_TRACE 开启时写入 JSONL span；默认关闭不写文件
- LangSmith 仅配置位；无 Key 不阻塞；默认 pytest 不要求 LangSmith

Rewrote from: REF-MISSIONS
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi.testclient import TestClient

from claims_api.api import app, reset_service

CASE_SC02 = "CLM-SC02-001"


def _client(*, clear_local_trace: bool = True) -> TestClient:
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("CLAIMS_GATE_LLM_API_KEY", None)
    os.environ.pop("LANGCHAIN_API_KEY", None)
    if clear_local_trace:
        os.environ.pop("CLAIMS_GATE_LOCAL_TRACE", None)
        os.environ.pop("CLAIMS_GATE_LOCAL_TRACE_PATH", None)
    reset_service()
    return TestClient(app)


def _login(client: TestClient, username: str) -> dict[str, str]:
    resp = client.post(
        "/auth/login",
        json={"username": username, "password": username},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['session_token']}"}


def _decision_types(items: list[dict]) -> list[str]:
    return [str(i.get("decision_type") or "") for i in items]


def test_env_example_reserves_langsmith_and_local_trace() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / ".env.example").read_text(encoding="utf-8")
    assert "LANGCHAIN_TRACING_V2" in text
    assert "LANGCHAIN_API_KEY" in text
    assert "LANGCHAIN_PROJECT" in text
    assert "CLAIMS_GATE_LOCAL_TRACE" in text
    assert "CLAIMS_GATE_LOCAL_TRACE_PATH" in text


def test_ledger_records_evaluate_assist_and_latch() -> None:
    """本案流水可回放评估 / AI 辅助 / 人闸批准。"""
    client = _client()
    adj = _login(client, "adjuster")
    sup = _login(client, "supervisor")

    ev = client.post(f"/claims/{CASE_SC02}/evaluate", headers=adj)
    assert ev.status_code == 200, ev.text

    assist = client.post(
        f"/claims/{CASE_SC02}/assist",
        json={"query": "疾病摔伤是否除外"},
        headers=adj,
    )
    assert assist.status_code == 200, assist.text

    appr = client.post(
        f"/claims/{CASE_SC02}/human-latch/approve",
        json={"approved_by": "supervisor"},
        headers=sup,
    )
    assert appr.status_code == 200, appr.text

    led = client.get(f"/claims/{CASE_SC02}/ledger", headers=adj)
    assert led.status_code == 200, led.text
    items = led.json()["items"]
    types = _decision_types(items)
    assert "reject_draft" in types
    assert "assist_suggestion" in types
    assert "human_latch_approve" in types
    # 最新在前：人闸批准应靠前
    assert types.index("human_latch_approve") < types.index("assist_suggestion")

    rej = client.post(
        f"/claims/{CASE_SC02}/human-latch/reject",
        json={"rejected_by": "supervisor", "reason": "需补材料后再审"},
        headers=sup,
    )
    assert rej.status_code == 200, rej.text
    led2 = client.get(f"/claims/{CASE_SC02}/ledger", headers=adj)
    assert "human_latch_reject" in _decision_types(led2.json()["items"])


def test_local_trace_jsonl_exports_evaluate_assist_latch(
    tmp_path: Path, monkeypatch
) -> None:
    """开启本地 trace 后，evaluate / assist / latch 写入 JSONL span。"""
    trace_file = tmp_path / "spans.jsonl"
    # 无 LangSmith Key 仍可跑
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
    monkeypatch.setenv("CLAIMS_GATE_LOCAL_TRACE", "1")
    monkeypatch.setenv("CLAIMS_GATE_LOCAL_TRACE_PATH", str(trace_file))

    client = _client(clear_local_trace=False)
    adj = _login(client, "adjuster")
    sup = _login(client, "supervisor")

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

    assert trace_file.is_file()
    lines = [ln for ln in trace_file.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) >= 3
    spans = [json.loads(ln) for ln in lines]
    names = {s.get("name") for s in spans}
    assert "evaluate" in names
    assert "assist" in names
    assert "latch" in names
    for span in spans:
        assert span.get("case_id") == CASE_SC02
        assert "ts" in span
        # 本地 exporter；不依赖 LangSmith run_id
        assert span.get("exporter") == "local_jsonl"


def test_local_trace_disabled_by_default_writes_nothing(
    tmp_path: Path, monkeypatch
) -> None:
    """路径已配置但未开启：业务路径不得写 JSONL。"""
    trace_file = tmp_path / "should_not_exist.jsonl"
    monkeypatch.setenv("CLAIMS_GATE_LOCAL_TRACE", "0")
    monkeypatch.setenv("CLAIMS_GATE_LOCAL_TRACE_PATH", str(trace_file))
    client = _client(clear_local_trace=False)
    adj = _login(client, "adjuster")
    assert client.post(f"/claims/{CASE_SC02}/evaluate", headers=adj).status_code == 200
    assert not trace_file.exists()


def test_pytest_default_path_does_not_require_langsmith() -> None:
    """默认路径：无 LangSmith Key 时 evaluate 仍可用。"""
    client = _client()
    assert os.environ.get("LANGCHAIN_API_KEY") in (None, "")
    resp = client.post(f"/claims/{CASE_SC02}/evaluate")
    assert resp.status_code == 200, resp.text

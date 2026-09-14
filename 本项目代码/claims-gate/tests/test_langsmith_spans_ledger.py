"""接缝 S0：真 LangSmith span + ledger 对齐（无 Key / 可注入 mock）。

验收：
- 无 Key 时 evaluate / assist / latch 不阻断；ledger 仍含 retrieval_profile
- 注入 mock Client 且开启 tracing 时，关键动作 ledger 含 trace_id
- 本地 JSONL exporter 仍可用
- 默认 pytest 不要求 LangSmith；真上报在 S2 langsmith_integration

Mock 策略（票 26）：默认/S0 用可注入 FakeLangSmithClient，不打外网；
不得用 mock 冒充 Pilot Complete。真 Key 验证见 tests/langsmith_integration/。

Rewrote from: REF-CASE-EVAL-ADVISOR, REF-MISSIONS
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi.testclient import TestClient

from claims_api import langsmith_trace
from claims_api.api import app, reset_service

CASE_SC02 = "CLM-SC02-001"


class FakeLangSmithClient:
    """官方外形 mock：记录 create_run，不访问网络。"""

    def __init__(self) -> None:
        self.runs: list[dict[str, Any]] = []

    def create_run(self, **kwargs: Any) -> None:
        self.runs.append(dict(kwargs))

    def update_run(self, run_id: Any, **kwargs: Any) -> None:
        self.runs.append({"_update": True, "id": run_id, **kwargs})


def _client(*, clear_env: bool = True) -> TestClient:
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("CLAIMS_GATE_LLM_API_KEY", None)
    if clear_env:
        os.environ.pop("LANGCHAIN_API_KEY", None)
        os.environ.pop("LANGSMITH_API_KEY", None)
        os.environ.pop("LANGCHAIN_TRACING_V2", None)
        os.environ.pop("LANGSMITH_TRACING", None)
        os.environ.pop("CLAIMS_GATE_LOCAL_TRACE", None)
        os.environ.pop("CLAIMS_GATE_LOCAL_TRACE_PATH", None)
        langsmith_trace.reset_client_override()
    reset_service()
    return TestClient(app)


def _login(client: TestClient, username: str) -> dict[str, str]:
    resp = client.post(
        "/auth/login",
        json={"username": username, "password": username},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['session_token']}"}


def test_pytest_ini_excludes_langsmith_integration() -> None:
    root = Path(__file__).resolve().parents[1]
    ini = (root / "pytest.ini").read_text(encoding="utf-8")
    assert "langsmith_integration" in ini
    assert "not langsmith_integration" in ini


def test_no_key_does_not_block_and_ledger_has_profile_without_trace() -> None:
    client = _client()
    assert os.environ.get("LANGCHAIN_API_KEY") in (None, "")
    adj = _login(client, "adjuster")
    resp = client.post(f"/claims/{CASE_SC02}/evaluate", headers=adj)
    assert resp.status_code == 200, resp.text
    led = client.get(f"/claims/{CASE_SC02}/ledger", headers=adj)
    assert led.status_code == 200, led.text
    item = led.json()["items"][0]
    assert item["retrieval_profile"]
    assert item.get("trace_id") in (None, "", [])


def test_mock_langsmith_writes_trace_id_on_evaluate_assist_latch(
    monkeypatch,
) -> None:
    fake = FakeLangSmithClient()
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
    monkeypatch.setenv("LANGCHAIN_API_KEY", "lsv2_pt_test_mock_not_real")
    monkeypatch.setenv("LANGCHAIN_PROJECT", "claims-gate-test")
    langsmith_trace.set_client_override(fake)
    try:
        client = _client(clear_env=False)
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

        led = client.get(f"/claims/{CASE_SC02}/ledger", headers=adj)
        items = led.json()["items"]
        by_type = {i["decision_type"]: i for i in items}
        for key in ("reject_draft", "assist_suggestion", "human_latch_approve"):
            assert key in by_type
            tid = by_type[key].get("trace_id")
            assert tid, f"{key} missing trace_id"
            UUID(str(tid))  # 合法 UUID
            assert by_type[key]["retrieval_profile"]

        names = {r.get("name") for r in fake.runs if "name" in r}
        assert {"evaluate", "assist", "latch"} <= names
    finally:
        langsmith_trace.reset_client_override()


def test_local_exporter_still_works_with_langsmith_mock(
    tmp_path: Path, monkeypatch
) -> None:
    fake = FakeLangSmithClient()
    trace_file = tmp_path / "spans.jsonl"
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
    monkeypatch.setenv("LANGCHAIN_API_KEY", "lsv2_pt_test_mock_not_real")
    monkeypatch.setenv("CLAIMS_GATE_LOCAL_TRACE", "1")
    monkeypatch.setenv("CLAIMS_GATE_LOCAL_TRACE_PATH", str(trace_file))
    langsmith_trace.set_client_override(fake)
    try:
        client = _client(clear_env=False)
        adj = _login(client, "adjuster")
        assert client.post(f"/claims/{CASE_SC02}/evaluate", headers=adj).status_code == 200
        assert trace_file.is_file()
        spans = [
            json.loads(ln)
            for ln in trace_file.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        assert any(s.get("name") == "evaluate" for s in spans)
        assert fake.runs
    finally:
        langsmith_trace.reset_client_override()


def test_env_example_documents_w1_langsmith() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / ".env.example").read_text(encoding="utf-8")
    assert "LANGCHAIN_TRACING_V2" in text
    assert "LANGCHAIN_API_KEY" in text
    assert "CLAIMS_GATE_LOCAL_TRACE" in text

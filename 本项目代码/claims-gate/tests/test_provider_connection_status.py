"""Issue 51：只读连接状态聚合 — S0 接缝（无 Key 回显）。

Rewrote from: REF-MISSIONS（质询 P-CFG β）
"""

from __future__ import annotations

import json

import pytest


def test_missing_keys_reports_degraded_without_secret_literals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """无 LLM/Embedding/LangSmith Key：已配置=false、降级可读，正文无 Key 字面量。"""
    from missions.provider_connection_status import (
        build_provider_connection_status,
    )

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CLAIMS_GATE_LLM_API_KEY", raising=False)
    monkeypatch.delenv("CLAIMS_GATE_EMBEDDING_API_KEY", raising=False)
    monkeypatch.delenv("EMBEDDING_API_KEY", raising=False)
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)
    monkeypatch.setenv("EMBEDDING_PROVIDER", "cloud")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("EMBEDDING_MODEL", "text-embedding-3-small")

    status = build_provider_connection_status()
    blob = json.dumps(status, ensure_ascii=False)

    assert status["llm"]["configured"] is False
    assert status["llm"]["degraded"] is True
    assert status["llm"]["model"] == "gpt-4o-mini"
    assert status["embedding"]["configured"] is False
    assert status["embedding"]["degraded"] is True
    assert status["embedding"]["provider"] == "cloud"
    assert status["embedding"]["model"] == "text-embedding-3-small"
    assert status["langsmith"]["configured"] is False
    assert status["langsmith"]["degraded"] is False
    assert status["langsmith"]["enabled"] is False

    # 永不回显 Key：禁止密钥字段与 sk- 前缀
    for forbidden in ("sk-", "OPENAI_API_KEY=", "CLAIMS_GATE_LLM_API_KEY="):
        assert forbidden not in blob
    for section in ("llm", "embedding", "langsmith"):
        assert "api_key" not in status[section]
        assert "api_key_set" not in status[section]


def test_configured_providers_report_models_and_not_degraded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """满配时：configured=true、degraded=false，仍不回显 Key 值。"""
    from missions.provider_connection_status import (
        build_provider_connection_status,
    )

    secret = "sk-test-secret-never-echo-51"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("CLAIMS_GATE_EMBEDDING_API_KEY", secret)
    monkeypatch.setenv("EMBEDDING_PROVIDER", "cloud")
    monkeypatch.setenv("EMBEDDING_MODEL", "text-embedding-3-small")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
    monkeypatch.setenv("LANGCHAIN_API_KEY", secret)
    monkeypatch.setenv("LANGCHAIN_PROJECT", "claims-gate-pilot")

    status = build_provider_connection_status()
    blob = json.dumps(status, ensure_ascii=False)

    assert status["llm"]["configured"] is True
    assert status["llm"]["degraded"] is False
    assert status["llm"]["model"] == "gpt-4o-mini"
    assert status["embedding"]["configured"] is True
    assert status["embedding"]["degraded"] is False
    assert status["embedding"]["semantic"] is True
    assert status["langsmith"]["configured"] is True
    assert status["langsmith"]["enabled"] is True
    assert status["langsmith"]["degraded"] is False
    assert status["langsmith"]["project"] == "claims-gate-pilot"
    assert secret not in blob


def test_local_embedding_labeled_non_semantic_not_cloud_degraded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CI local 哈希：非语义标明；不算缺 Key 的 cloud 降级。"""
    from missions.chroma_index.embeddings import LOCAL_EMBEDDING_LABEL
    from missions.provider_connection_status import (
        build_provider_connection_status,
    )

    monkeypatch.setenv("EMBEDDING_PROVIDER", "local")
    monkeypatch.delenv("CLAIMS_GATE_EMBEDDING_API_KEY", raising=False)
    monkeypatch.delenv("EMBEDDING_API_KEY", raising=False)

    status = build_provider_connection_status()
    assert status["embedding"]["provider"] == "local"
    assert status["embedding"]["configured"] is True
    assert status["embedding"]["semantic"] is False
    assert status["embedding"]["model"] == LOCAL_EMBEDDING_LABEL
    assert status["embedding"]["degraded"] is False


def test_langsmith_wants_trace_without_key_is_degraded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """开启 tracing 但缺 Key：诚实降级。"""
    from missions.provider_connection_status import (
        build_provider_connection_status,
    )

    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)

    status = build_provider_connection_status()
    assert status["langsmith"]["configured"] is False
    assert status["langsmith"]["enabled"] is False
    assert status["langsmith"]["degraded"] is True
    assert status["langsmith"]["degrade_reason"] == "missing_langsmith_api_key"


# --- S1：HTTP 只读接缝 ---


def _http_client():
    from fastapi.testclient import TestClient

    from claims_api.api import app, reset_service

    reset_service()
    return TestClient(app)


def _login(client, username: str) -> dict[str, str]:
    resp = client.post(
        "/auth/login",
        json={"username": username, "password": username},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["session_token"]
    return {"Authorization": f"Bearer {token}"}


def test_http_connection_status_readable_for_viewer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /provider/connection-status：viewer 可读；含 llm/embedding/langsmith。"""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CLAIMS_GATE_LLM_API_KEY", raising=False)
    secret = "sk-http-leak-probe-51"
    monkeypatch.setenv("OPENAI_API_KEY", secret)

    client = _http_client()
    headers = _login(client, "viewer")
    resp = client.get("/provider/connection-status", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "llm" in body and "embedding" in body and "langsmith" in body
    assert body["llm"]["configured"] is True
    assert body["llm"]["model"]
    text = resp.text
    assert secret not in text
    assert "api_key" not in body["llm"]
    assert "api_key" not in body["embedding"]
    assert "api_key" not in body["langsmith"]
    assert "api_key_set" not in body["langsmith"]


def test_http_connection_status_never_echoes_any_provider_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """满配响应正文不得出现任一 Provider Key 字面量。"""
    secret_llm = "sk-llm-never-echo-51"
    secret_emb = "sk-emb-never-echo-51"
    secret_ls = "lsv2_never_echo_51"
    monkeypatch.setenv("OPENAI_API_KEY", secret_llm)
    monkeypatch.setenv("CLAIMS_GATE_EMBEDDING_API_KEY", secret_emb)
    monkeypatch.setenv("EMBEDDING_PROVIDER", "cloud")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
    monkeypatch.setenv("LANGCHAIN_API_KEY", secret_ls)

    client = _http_client()
    headers = _login(client, "adjuster")
    resp = client.get("/provider/connection-status", headers=headers)
    assert resp.status_code == 200, resp.text
    text = resp.text
    for secret in (secret_llm, secret_emb, secret_ls):
        assert secret not in text
    body = resp.json()
    assert body["llm"]["configured"] is True
    assert body["embedding"]["configured"] is True
    assert body["langsmith"]["configured"] is True


def test_http_connection_status_requires_session() -> None:
    """无 Bearer：401；契约明确须登录（运维肖像不匿名开放）。"""
    client = _http_client()
    resp = client.get("/provider/connection-status")
    assert resp.status_code == 401, resp.text

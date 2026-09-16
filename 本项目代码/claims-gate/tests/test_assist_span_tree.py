"""接缝：assist span 树 retrieve→fuse→gate→llm→(adopt|abstain)→evaluate（Issue 41 / P-E1）。

S0 可测（无 LangSmith Key）：
- 主路径与 abstain 分支节点齐全
- 本地 JSONL 写出 / 回放同构
- 不进 machine_check / S0 必过；默认 pytest 不要求 Key

Rewrote from: REF-CASE-EVAL-ADVISOR
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from missions.assist_span_tree import (
    ASSIST_SPAN_BRANCH_ABSTAIN,
    ASSIST_SPAN_BRANCH_ADOPT,
    ASSIST_SPAN_EVALUATE,
    ASSIST_SPAN_STEPS_CORE,
    build_assist_span_tree,
    emit_assist_span_tree,
    replay_assist_span_tree,
    write_assist_span_tree_jsonl,
)

ROOT = Path(__file__).resolve().parents[1]


def test_span_tree_covers_main_path_adopt() -> None:
    """主路径：retrieve→fuse→gate→llm→adopt→evaluate。"""
    records = build_assist_span_tree(
        case_id="CLM-SC02-001",
        assist_invocation_id="assist-adopt-fixture",
        disposition="draft",
    )
    names = [r.name for r in records if r.name != "assist"]
    assert names == list(ASSIST_SPAN_STEPS_CORE) + [
        ASSIST_SPAN_BRANCH_ADOPT,
        ASSIST_SPAN_EVALUATE,
    ]
    root = next(r for r in records if r.parent_run_id is None)
    assert root.name == "assist"
    # 父子链连续
    by_id = {r.run_id: r for r in records}
    for child in records:
        if child.parent_run_id is None:
            continue
        assert child.parent_run_id in by_id


def test_span_tree_covers_abstain_branch() -> None:
    """abstain 分支：末级决策节点为 abstain，非 adopt。"""
    records = build_assist_span_tree(
        case_id="CLM-SC02-001",
        assist_invocation_id="assist-abstain-fixture",
        disposition="abstain",
        abstain_reason="conflict",
    )
    names = [r.name for r in records if r.name != "assist"]
    assert ASSIST_SPAN_BRANCH_ABSTAIN in names
    assert ASSIST_SPAN_BRANCH_ADOPT not in names
    assert names == list(ASSIST_SPAN_STEPS_CORE) + [
        ASSIST_SPAN_BRANCH_ABSTAIN,
        ASSIST_SPAN_EVALUATE,
    ]
    branch = next(r for r in records if r.name == ASSIST_SPAN_BRANCH_ABSTAIN)
    assert branch.outputs.get("assist_disposition") == "abstain"
    assert branch.outputs.get("abstain_reason") == "conflict"


def test_local_jsonl_replay_without_langsmith_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """无 LangSmith Key 时可写本地 JSONL 并回放同构树。"""
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)
    assert not (os.environ.get("LANGCHAIN_API_KEY") or "").strip()
    assert not (os.environ.get("LANGSMITH_API_KEY") or "").strip()

    path = tmp_path / "assist_spans.jsonl"
    original = build_assist_span_tree(
        case_id="CLM-SC02-001",
        assist_invocation_id="assist-replay-fixture",
        disposition="abstain",
        abstain_reason="low_confidence",
        attributes={"retrieval_profile": "clause_v_current"},
    )
    write_assist_span_tree_jsonl(path, original)
    assert path.is_file()

    replayed = replay_assist_span_tree(path)
    assert [r.name for r in replayed] == [r.name for r in original]
    assert [r.parent_run_id for r in replayed] == [r.parent_run_id for r in original]
    # LangSmith 同构字段仍在本地行上
    line = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    for key in ("name", "id", "parent_run_id", "run_type", "inputs", "outputs", "extra"):
        assert key in line
    assert line.get("exporter") == "local_jsonl"


def test_emit_writes_when_local_trace_enabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CLAIMS_GATE_LOCAL_TRACE 开启时 emit 落盘；无 Key 不抛。"""
    path = tmp_path / "spans.jsonl"
    monkeypatch.setenv("CLAIMS_GATE_LOCAL_TRACE", "1")
    monkeypatch.setenv("CLAIMS_GATE_LOCAL_TRACE_PATH", str(path))
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)

    records = emit_assist_span_tree(
        case_id="CLM-SC02-001",
        assist_invocation_id="assist-emit-fixture",
        disposition="draft",
    )
    assert records
    assert path.is_file()
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == len(records)


def test_assist_span_not_in_machine_check_s0() -> None:
    """硬约束：assist span 树不进 machine_check / S0 必过。"""
    checks_src = (ROOT / "src" / "missions" / "checks.py").read_text(encoding="utf-8")
    assert "assist_span_tree" not in checks_src
    assert "build_assist_span_tree" not in checks_src
    assert "emit_assist_span_tree" not in checks_src

    module = (ROOT / "src" / "missions" / "assist_span_tree.py").read_text(encoding="utf-8")
    assert "machine_check" in module
    assert "非合门禁" in module or "不进" in module
    assert "REF-CASE-EVAL-ADVISOR" in module


def test_default_pytest_still_excludes_langsmith_integration() -> None:
    """默认 addopts 仍排除真 LangSmith；本票不把 Key 绑进 S0。"""
    ini = (ROOT / "pytest.ini").read_text(encoding="utf-8")
    assert "not langsmith_integration" in ini


def test_assist_http_emits_span_tree_to_local_jsonl(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """assist HTTP 路径在本地 trace 开启时写入 span 树（无 LangSmith Key）。"""
    from fastapi.testclient import TestClient

    from claims_api.api import app, reset_service

    path = tmp_path / "assist_tree.jsonl"
    monkeypatch.setenv("CLAIMS_GATE_LOCAL_TRACE", "1")
    monkeypatch.setenv("CLAIMS_GATE_LOCAL_TRACE_PATH", str(path))
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CLAIMS_GATE_LLM_API_KEY", raising=False)
    reset_service()
    client = TestClient(app)
    login = client.post(
        "/auth/login",
        json={"username": "adjuster", "password": "adjuster"},
    )
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['session_token']}"}
    resp = client.post(
        "/claims/CLM-SC02-001/assist",
        json={"query": "除外责任"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert path.is_file()
    replayed = replay_assist_span_tree(path)
    names = [r.name for r in replayed]
    assert "retrieve" in names and "fuse" in names and "gate" in names
    assert "llm" in names and ASSIST_SPAN_EVALUATE in names
    assert ASSIST_SPAN_BRANCH_ADOPT in names or ASSIST_SPAN_BRANCH_ABSTAIN in names

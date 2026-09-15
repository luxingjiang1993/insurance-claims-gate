"""接缝：评测跑次持久化 + actor 归因（票 29 / W2）。

S0：隔离契约（默认 CI）——不替代 machine_check；失败跑次不进合门禁。
S2：eval_bypass ——两演示用户分别触发；结果按 actor 过滤互不覆盖。

前置：W1 票 28（Pilot Complete / Package L）已关闭。
Rewrote from: REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR, REF-MISSIONS
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from claims_api.api import app, reset_service

ROOT = Path(__file__).resolve().parents[2]


def _client(db_path: Path | None = None) -> TestClient:
    reset_service(db_path=db_path)
    return TestClient(app)


def _login(client: TestClient, username: str) -> dict[str, str]:
    resp = client.post(
        "/auth/login",
        json={"username": username, "password": username},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['session_token']}"}


def test_eval_run_persist_module_declares_bypass_and_refs() -> None:
    """旁路模块存在；声明不替代 machine_check；含 Rewrote from 与 W1 前置。"""
    path = ROOT / "src" / "missions" / "eval_run_persist.py"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "旁路" in text and "非合门禁" in text
    assert "machine_check" in text
    assert "actor_user_id" in text
    assert "REF-CASE-OPENEVALS" in text
    assert "REF-CASE-EVAL-ADVISOR" in text
    assert "REF-MISSIONS" in text
    assert "W1" in text or "票 28" in text or "28" in text


def test_checks_does_not_route_through_eval_run_persist() -> None:
    """硬约束：合门禁主缝仍是 machine_check，不得吞并评测跑次入口。"""
    checks_src = (ROOT / "src" / "missions" / "checks.py").read_text(encoding="utf-8")
    assert "eval_run_persist" not in checks_src
    assert "create_eval_run" not in checks_src
    assert "/eval/runs" not in checks_src


def test_pytest_ini_still_excludes_eval_bypass() -> None:
    """默认 pytest 须排除 eval_bypass（故意失败的评测不得让 CI 红）。"""
    ini = (ROOT / "pytest.ini").read_text(encoding="utf-8")
    assert "not eval_bypass" in ini


def test_sqlite_store_persists_eval_run_with_actor(tmp_path: Path) -> None:
    """本地表真源：写入含 actor_user_id 的跑次，可按用户过滤。"""
    from claims_api.sqlite_store import SqliteCaseStore

    db = tmp_path / "eval_runs.sqlite"
    store = SqliteCaseStore(db)
    try:
        run_a = store.save_eval_run(
            run_id="run-adjuster-1",
            actor_user_id="adjuster",
            experiment_name="exp-a",
            experiment_id=None,
            dataset_name="claims-gate-openeval-negatives",
            summary={"passed": 2, "failed": 0, "total": 2},
            cases=[{"id": "c1", "passed": True}],
            created_at="2026-09-15T00:00:00+00:00",
            langsmith_degraded=True,
        )
        store.save_eval_run(
            run_id="run-supervisor-1",
            actor_user_id="supervisor",
            experiment_name="exp-b",
            experiment_id="ls-1",
            dataset_name="claims-gate-openeval-negatives",
            summary={"passed": 1, "failed": 1, "total": 2},
            cases=[{"id": "c2", "passed": False}],
            created_at="2026-09-15T00:01:00+00:00",
            langsmith_degraded=False,
        )
        assert run_a["actor_user_id"] == "adjuster"
        all_runs = store.list_eval_runs()
        assert len(all_runs) == 2
        only_adj = store.list_eval_runs(actor_user_id="adjuster")
        assert len(only_adj) == 1
        assert only_adj[0]["run_id"] == "run-adjuster-1"
        assert only_adj[0]["actor_user_id"] == "adjuster"
        only_sup = store.list_eval_runs(actor_user_id="supervisor")
        assert len(only_sup) == 1
        assert only_sup[0]["run_id"] == "run-supervisor-1"
        # 过滤互不覆盖：adjuster 视图不含 supervisor 跑次
        assert {r["run_id"] for r in only_adj}.isdisjoint(
            {r["run_id"] for r in only_sup}
        )
    finally:
        store.close()


@pytest.mark.eval_bypass
def test_two_demo_users_trigger_isolated_eval_runs(tmp_path: Path) -> None:
    """≥2 演示用户分别触发；结果可按 actor 过滤；仍走 OpenEval 旁路。"""
    from missions.openeval_langsmith import (
        FakeLangSmithExperimentClient,
        reset_experiment_client_override,
        set_experiment_client_override,
    )

    fake = FakeLangSmithExperimentClient()
    set_experiment_client_override(fake)
    try:
        client = _client(db_path=tmp_path / "claims_gate.sqlite")
        h_adj = _login(client, "adjuster")
        h_sup = _login(client, "supervisor")

        r1 = client.post("/eval/runs", headers=h_adj, json={})
        assert r1.status_code == 200, r1.text
        body1 = r1.json()
        assert body1["actor_user_id"] == "adjuster"
        assert body1["run_id"]
        assert body1["blocks_track_a_gate"] is False
        assert body1["gate_role"] == "bypass_not_machine_check"
        assert body1["summary"]["total"] >= 2

        r2 = client.post("/eval/runs", headers=h_sup, json={})
        assert r2.status_code == 200, r2.text
        body2 = r2.json()
        assert body2["actor_user_id"] == "supervisor"
        assert body2["run_id"] != body1["run_id"]

        listed_all = client.get("/eval/runs", headers=h_adj)
        assert listed_all.status_code == 200, listed_all.text
        runs = listed_all.json()["runs"]
        assert len(runs) >= 2
        actors = {row["actor_user_id"] for row in runs}
        assert "adjuster" in actors and "supervisor" in actors

        only_adj = client.get(
            "/eval/runs",
            headers=h_adj,
            params={"actor_user_id": "adjuster"},
        )
        assert only_adj.status_code == 200, only_adj.text
        adj_runs = only_adj.json()["runs"]
        assert adj_runs
        assert all(row["actor_user_id"] == "adjuster" for row in adj_runs)
        assert body1["run_id"] in {row["run_id"] for row in adj_runs}
        assert body2["run_id"] not in {row["run_id"] for row in adj_runs}
    finally:
        reset_experiment_client_override()


@pytest.mark.eval_bypass
def test_viewer_cannot_create_eval_run_but_can_list(tmp_path: Path) -> None:
    """viewer 只读：不可触发跑次；可按用户过滤查看。"""
    client = _client(db_path=tmp_path / "claims_gate.sqlite")
    h_adj = _login(client, "adjuster")
    h_view = _login(client, "viewer")

    created = client.post("/eval/runs", headers=h_adj, json={})
    assert created.status_code == 200, created.text

    denied = client.post("/eval/runs", headers=h_view, json={})
    assert denied.status_code == 403, denied.text

    listed = client.get(
        "/eval/runs",
        headers=h_view,
        params={"actor_user_id": "adjuster"},
    )
    assert listed.status_code == 200, listed.text
    assert listed.json()["runs"]

"""接缝：评测排行榜字段 + 主指标稳定排序（票 30 / W2）。

S0：隔离契约（默认 CI）——榜分不进 machine_check；用本地表种子测字段与排序。
S2：eval_bypass ——两演示用户跑次经 HTTP 可见于榜（可选；不挡合门禁）。

单一数据真源：本地 SQLite `eval_runs`（与票 29 一致；不读 LangSmith 实验 API）。
Rewrote from: REF-CASE-EVAL-ADVISOR, REF-CASE-OPENEVALS, REF-MISSIONS
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


def test_leaderboard_module_declares_single_source_and_refs() -> None:
    """旁路模块存在；声明单一真源为本地 SQLite；含 Rewrote from。"""
    path = ROOT / "src" / "missions" / "eval_leaderboard.py"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "eval_runs" in text
    assert "SQLite" in text or "sqlite" in text.lower()
    assert "旁路" in text or "非合门禁" in text
    assert "machine_check" in text
    assert "REF-CASE-EVAL-ADVISOR" in text
    assert "REF-CASE-OPENEVALS" in text
    assert "REF-MISSIONS" in text
    # 不得双源：模块声明不读 LangSmith 实验 API 作为榜真源
    assert "不读 LangSmith" in text or "非 LangSmith" in text or "单一真源" in text


def test_checks_does_not_route_through_leaderboard() -> None:
    """硬约束：合门禁主缝仍是 machine_check，不得吞并排行榜。"""
    checks_src = (ROOT / "src" / "missions" / "checks.py").read_text(encoding="utf-8")
    assert "eval_leaderboard" not in checks_src
    assert "leaderboard" not in checks_src
    assert "/eval/leaderboard" not in checks_src


def test_pytest_ini_still_excludes_eval_bypass() -> None:
    """默认 pytest 须排除 eval_bypass。"""
    ini = (ROOT / "pytest.ini").read_text(encoding="utf-8")
    assert "not eval_bypass" in ini


def test_leaderboard_rows_have_required_fields_and_stable_sort(tmp_path: Path) -> None:
    """本地表真源：榜行含实验名/主指标/时间/提交者；按主指标降序且稳定。"""
    from claims_api.sqlite_store import SqliteCaseStore
    from missions.eval_leaderboard import build_leaderboard

    db = tmp_path / "leaderboard.sqlite"
    store = SqliteCaseStore(db)
    try:
        # 故意同主指标两条，检验稳定次序（先写入的 created_at 更早 → 同指标时靠前）
        store.save_eval_run(
            run_id="run-tie-earlier",
            actor_user_id="adjuster",
            experiment_name="exp-tie-a",
            experiment_id=None,
            dataset_name="claims-gate-openeval-negatives",
            summary={"passed": 1, "failed": 1, "total": 2},
            cases=[],
            created_at="2026-09-15T00:00:00+00:00",
            langsmith_degraded=True,
        )
        store.save_eval_run(
            run_id="run-tie-later",
            actor_user_id="supervisor",
            experiment_name="exp-tie-b",
            experiment_id=None,
            dataset_name="claims-gate-openeval-negatives",
            summary={"passed": 1, "failed": 1, "total": 2},
            cases=[],
            created_at="2026-09-15T00:02:00+00:00",
            langsmith_degraded=True,
        )
        store.save_eval_run(
            run_id="run-high",
            actor_user_id="adjuster",
            experiment_name="exp-high",
            experiment_id=None,
            dataset_name="claims-gate-openeval-negatives",
            summary={"passed": 2, "failed": 0, "total": 2},
            cases=[],
            created_at="2026-09-15T00:01:00+00:00",
            langsmith_degraded=True,
        )

        rows = build_leaderboard(store, sort_by="primary_metric", order="desc")
        assert len(rows) == 3
        for row in rows:
            d = row.to_dict()
            assert "experiment_name" in d
            assert "primary_metric" in d
            assert "created_at" in d
            assert "submitter" in d

        names = [r.experiment_name for r in rows]
        # 主指标降序：exp-high (1.0) 第一；并列 0.5 时按 created_at 升序稳定
        assert names[0] == "exp-high"
        assert names[1] == "exp-tie-a"
        assert names[2] == "exp-tie-b"

        submitters = {r.experiment_name: r.submitter for r in rows}
        assert submitters["exp-high"] == "adjuster"
        assert submitters["exp-tie-a"] == "adjuster"
        assert submitters["exp-tie-b"] == "supervisor"
    finally:
        store.close()


def test_http_leaderboard_shows_two_actors_seeded(tmp_path: Path) -> None:
    """契约：两用户两条跑次在榜上均可观察（本地种子，不跑 OpenEval）。"""
    from claims_api.api import get_store

    db = tmp_path / "claims_gate.sqlite"
    client = _client(db_path=db)
    store = get_store()
    store.save_eval_run(
        run_id="run-adj",
        actor_user_id="adjuster",
        experiment_name="exp-adjuster",
        experiment_id=None,
        dataset_name="claims-gate-openeval-negatives",
        summary={"passed": 2, "failed": 0, "total": 2},
        cases=[],
        created_at="2026-09-15T01:00:00+00:00",
        langsmith_degraded=True,
    )
    store.save_eval_run(
        run_id="run-sup",
        actor_user_id="supervisor",
        experiment_name="exp-supervisor",
        experiment_id=None,
        dataset_name="claims-gate-openeval-negatives",
        summary={"passed": 0, "failed": 2, "total": 2},
        cases=[],
        created_at="2026-09-15T01:01:00+00:00",
        langsmith_degraded=True,
    )

    headers = _login(client, "viewer")
    resp = client.get("/eval/leaderboard", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("blocks_track_a_gate") is False
    assert body.get("gate_role") == "bypass_not_machine_check"
    assert body.get("data_source") == "local_sqlite_eval_runs"
    rows = body["rows"]
    assert len(rows) == 2
    by_name = {r["experiment_name"]: r for r in rows}
    assert "exp-adjuster" in by_name and "exp-supervisor" in by_name
    assert by_name["exp-adjuster"]["submitter"] == "adjuster"
    assert by_name["exp-supervisor"]["submitter"] == "supervisor"
    # 按主指标降序：adjuster 在前
    assert rows[0]["experiment_name"] == "exp-adjuster"
    assert rows[1]["experiment_name"] == "exp-supervisor"


@pytest.mark.eval_bypass
def test_two_demo_users_runs_appear_on_leaderboard(tmp_path: Path) -> None:
    """S2：两演示用户经 POST /eval/runs 后均可在榜上观察。"""
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

        r1 = client.post(
            "/eval/runs",
            headers=h_adj,
            json={"experiment_name": "lb-adj"},
        )
        assert r1.status_code == 200, r1.text
        r2 = client.post(
            "/eval/runs",
            headers=h_sup,
            json={"experiment_name": "lb-sup"},
        )
        assert r2.status_code == 200, r2.text

        board = client.get("/eval/leaderboard", headers=h_adj)
        assert board.status_code == 200, board.text
        names = {row["experiment_name"] for row in board.json()["rows"]}
        assert "lb-adj" in names and "lb-sup" in names
        submitters = {row["submitter"] for row in board.json()["rows"]}
        assert "adjuster" in submitters and "supervisor" in submitters
    finally:
        reset_experiment_client_override()

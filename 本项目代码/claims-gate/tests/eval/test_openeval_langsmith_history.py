"""接缝：OpenEval 旁路 → LangSmith 实验历史对比（票 27）。

S0：隔离契约（默认 CI）——不替代 machine_check；无排行榜/多人协作。
S2：eval_bypass ——最小集 run + Fake Client 实验外形；历史对比可列表。

Mock 策略：默认/S2 mock 用可注入 FakeLangSmithExperimentClient，不打外网；
不得用 mock 冒充 Pilot Complete。真 Key 见 tests/langsmith_integration/。

Rewrote from: REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR, REF-MISSIONS
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from claims_api.api import app, reset_service

ROOT = Path(__file__).resolve().parents[2]


def test_openeval_langsmith_module_exists_and_declares_bypass() -> None:
    """旁路模块存在；声明不替代 machine_check；含 Rewrote from。"""
    path = ROOT / "src" / "missions" / "openeval_langsmith.py"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "旁路" in text and "非合门禁" in text
    assert "machine_check" in text
    assert "REF-CASE-OPENEVALS" in text
    assert "REF-CASE-EVAL-ADVISOR" in text
    assert "排行榜" in text or "leaderboard" in text.lower()


def test_checks_does_not_route_through_openeval_langsmith() -> None:
    """硬约束：合门禁主缝仍是 machine_check，不得吞并到 OpenEval 实验入口。"""
    checks_src = (ROOT / "src" / "missions" / "checks.py").read_text(encoding="utf-8")
    assert "openeval_langsmith" not in checks_src
    assert "run_openeval_experiment" not in checks_src


def test_no_leaderboard_or_collab_api_in_openeval_module() -> None:
    """W1 不含排行榜 / 多人协作评测台（属 W2）；文档可声明不含。"""
    path = ROOT / "src" / "missions" / "openeval_langsmith.py"
    text = path.read_text(encoding="utf-8")
    # 禁止实现排行榜/协作入口（函数/类名）；文档声明「不含」允许
    for banned in (
        "def leaderboard",
        "def rank_experiments",
        "def assign_eval_task",
        "def collab_eval",
        "class Leaderboard",
    ):
        assert banned not in text, f"不得出现 W2 API: {banned}"


def test_pytest_ini_still_excludes_eval_and_langsmith() -> None:
    """默认 pytest 须排除 eval_bypass 与 langsmith_integration。"""
    ini = (ROOT / "pytest.ini").read_text(encoding="utf-8")
    assert "not eval_bypass" in ini
    assert "not langsmith_integration" in ini


@pytest.mark.eval_bypass
def test_run_openeval_experiment_minimal_suite_with_fake_client() -> None:
    """最小集旁路跑通；结果写入 Fake 实验（同 dataset + experiment_name）。"""
    from missions.openeval_langsmith import (
        DEFAULT_DATASET_NAME,
        EVAL_GATE_ROLE,
        FakeLangSmithExperimentClient,
        run_openeval_experiment,
        set_experiment_client_override,
        reset_experiment_client_override,
    )

    fake = FakeLangSmithExperimentClient()
    set_experiment_client_override(fake)
    try:
        reset_service()
        http = TestClient(app)
        result = run_openeval_experiment(
            http,
            experiment_name="claims-gate-eval-exp-a",
            dataset_name=DEFAULT_DATASET_NAME,
        )
        assert result.gate_role == EVAL_GATE_ROLE
        assert result.blocks_track_a_gate is False
        assert result.dataset_name == DEFAULT_DATASET_NAME
        assert result.experiment_name == "claims-gate-eval-exp-a"
        assert result.experiment_id
        assert result.summary["total"] >= 2
        assert "hallucination_citation" in {
            c["category"] for c in result.cases
        }
        # Fake 侧可见 dataset + 至少一条 experiment
        assert DEFAULT_DATASET_NAME in fake.datasets
        assert len(fake.examples) >= 2
        assert any(
            e["experiment_name"] == "claims-gate-eval-exp-a"
            for e in fake.experiments
        )
    finally:
        reset_experiment_client_override()


@pytest.mark.eval_bypass
def test_experiment_history_compare_shape_two_runs() -> None:
    """同一 dataset 两次不同 experiment_name → 可列表历史对比外形（非排行榜）。"""
    from missions.openeval_langsmith import (
        DEFAULT_DATASET_NAME,
        FakeLangSmithExperimentClient,
        list_experiment_history,
        run_openeval_experiment,
        set_experiment_client_override,
        reset_experiment_client_override,
    )

    fake = FakeLangSmithExperimentClient()
    set_experiment_client_override(fake)
    try:
        reset_service()
        http = TestClient(app)
        r1 = run_openeval_experiment(
            http, experiment_name="claims-gate-eval-exp-v1"
        )
        r2 = run_openeval_experiment(
            http, experiment_name="claims-gate-eval-exp-v2"
        )
        assert r1.experiment_id != r2.experiment_id
        history = list_experiment_history(DEFAULT_DATASET_NAME)
        names = {h.experiment_name for h in history}
        assert "claims-gate-eval-exp-v1" in names
        assert "claims-gate-eval-exp-v2" in names
        for item in history:
            assert item.dataset_name == DEFAULT_DATASET_NAME
            assert item.experiment_name
            assert "passed" in item.summary and "total" in item.summary
            assert item.created_at
            # 历史对比外形：无名次 / 排行字段
            assert not hasattr(item, "rank")
            assert "rank" not in item.summary
            assert "leaderboard_score" not in item.summary
    finally:
        reset_experiment_client_override()

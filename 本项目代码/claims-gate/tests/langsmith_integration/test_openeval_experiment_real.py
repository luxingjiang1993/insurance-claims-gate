"""S2：OpenEval 旁路 → 真 LangSmith 实验（有 Key）或显式跳过。

Mock 不得冒充 Pilot Complete。本文件在真实 Key 下创建数据集实验；
无真实 Key 时 skip。不含排行榜。

运行：pytest tests/langsmith_integration/ -m langsmith_integration -o addopts=

Rewrote from: REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR, REF-MISSIONS
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from claims_api.api import app, reset_service
from missions.openeval_langsmith import (
    DEFAULT_DATASET_NAME,
    RealLangSmithExperimentClient,
    list_experiment_history,
    reset_experiment_client_override,
    run_openeval_experiment,
    set_experiment_client_override,
)

pytestmark = pytest.mark.langsmith_integration


def _has_real_key() -> bool:
    key = (
        os.environ.get("LANGCHAIN_API_KEY")
        or os.environ.get("LANGSMITH_API_KEY")
        or ""
    ).strip()
    if not key:
        return False
    lower = key.lower()
    return "mock" not in lower and "not_real" not in lower


@pytest.mark.skipif(not _has_real_key(), reason="需要真实 LANGCHAIN_API_KEY")
def test_real_openeval_experiment_visible_on_langsmith() -> None:
    """真 Key：旁路最小集写入 dataset+experiment，可 list 历史对比外形。"""
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_PROJECT", "claims-gate-s2")
    reset_experiment_client_override()
    real = RealLangSmithExperimentClient()
    set_experiment_client_override(real)
    try:
        reset_service()
        http = TestClient(app)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        name_a = f"claims-gate-openeval-s2-a-{stamp}"
        name_b = f"claims-gate-openeval-s2-b-{stamp}"
        r1 = run_openeval_experiment(http, experiment_name=name_a)
        r2 = run_openeval_experiment(http, experiment_name=name_b)
        assert r1.experiment_id, "须写入 LangSmith experiment"
        assert r2.experiment_id
        assert r1.summary["total"] >= 2
        assert r1.blocks_track_a_gate is False

        history = list_experiment_history(DEFAULT_DATASET_NAME)
        by_name = {h.experiment_name: h for h in history}
        assert name_a in by_name, f"须在 LangSmith 历史中可见: {name_a}"
        assert name_b in by_name, f"须在 LangSmith 历史中可见: {name_b}"
        for item in (by_name[name_a], by_name[name_b]):
            assert item.dataset_name == DEFAULT_DATASET_NAME
            assert item.summary.get("total", 0) >= 2
            assert not hasattr(item, "rank")
            assert "rank" not in item.summary
    finally:
        reset_experiment_client_override()

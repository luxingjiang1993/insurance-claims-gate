"""评测跑次持久化 + actor 归因（W2 Eval Ops）。

硬约束（旁路，非合门禁主缝）：
- 默认 CI 合门禁仍以 missions.checks.machine_check 为准；
- 本入口失败可告警，不得改写人闸语义；
- 不得要求 LLM / LangSmith 才能让轨 A 变绿；
- 跑次仍经 OpenEval 旁路（及 W1 LangSmith 路径）；无 Client 时 langsmith_degraded=true。

前置：W1 票 28（Pilot Complete）已关闭；本模块不宣称排行榜已交付（属票 30）。

本地 SQLite `eval_runs` 为跑次持久化真源（含 actor_user_id）；复用 W0 演示用户。

Rewrote from: REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR, REF-MISSIONS
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient

from claims_api.sqlite_store import SqliteCaseStore
from missions.eval_entry import EVAL_GATE_ROLE
from missions.openeval_langsmith import (
    DEFAULT_DATASET_NAME,
    ExperimentResult,
    run_openeval_experiment,
)


@dataclass
class EvalRunRecord:
    """持久化后的评测跑次（可按 actor 过滤）。"""

    run_id: str
    actor_user_id: str
    experiment_name: str
    experiment_id: str | None
    dataset_name: str
    summary: dict[str, Any]
    cases: list[dict[str, Any]]
    created_at: str
    langsmith_degraded: bool
    gate_role: str = EVAL_GATE_ROLE
    blocks_track_a_gate: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "actor_user_id": self.actor_user_id,
            "experiment_name": self.experiment_name,
            "experiment_id": self.experiment_id,
            "dataset_name": self.dataset_name,
            "summary": dict(self.summary),
            "cases": list(self.cases),
            "created_at": self.created_at,
            "langsmith_degraded": self.langsmith_degraded,
            "gate_role": self.gate_role,
            "blocks_track_a_gate": self.blocks_track_a_gate,
        }


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def persist_experiment_result(
    store: SqliteCaseStore,
    result: ExperimentResult,
    *,
    actor_user_id: str,
    run_id: str | None = None,
    created_at: str | None = None,
) -> EvalRunRecord:
    """将 OpenEval 旁路实验结果写入本地表，并记录 actor_user_id。"""
    rid = run_id or f"eval-{uuid4().hex[:16]}"
    ts = created_at or _utc_now_iso()
    degraded = result.experiment_id is None
    row = store.save_eval_run(
        run_id=rid,
        actor_user_id=actor_user_id,
        experiment_name=result.experiment_name,
        experiment_id=result.experiment_id,
        dataset_name=result.dataset_name,
        summary=dict(result.summary),
        cases=list(result.cases),
        created_at=ts,
        langsmith_degraded=degraded,
    )
    return EvalRunRecord(
        run_id=str(row["run_id"]),
        actor_user_id=str(row["actor_user_id"]),
        experiment_name=str(row["experiment_name"]),
        experiment_id=row["experiment_id"],
        dataset_name=str(row["dataset_name"]),
        summary=dict(row["summary"]),
        cases=list(row["cases"]),
        created_at=str(row["created_at"]),
        langsmith_degraded=bool(row["langsmith_degraded"]),
        gate_role=EVAL_GATE_ROLE,
        blocks_track_a_gate=False,
    )


def trigger_and_persist_eval_run(
    http_client: TestClient,
    store: SqliteCaseStore,
    *,
    actor_user_id: str,
    experiment_name: str | None = None,
    dataset_name: str = DEFAULT_DATASET_NAME,
) -> EvalRunRecord:
    """以演示用户身份触发 OpenEval 旁路跑次并持久化。

    LangSmith 不可用时仍落本地表（langsmith_degraded=true）；永不写入 machine_check。
    """
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    name = experiment_name or f"claims-gate-eval-{actor_user_id}-{stamp}"
    result = run_openeval_experiment(
        http_client,
        experiment_name=name,
        dataset_name=dataset_name,
    )
    return persist_experiment_result(store, result, actor_user_id=actor_user_id)


def list_persisted_eval_runs(
    store: SqliteCaseStore,
    *,
    actor_user_id: str | None = None,
) -> list[EvalRunRecord]:
    """列出已持久化跑次；可选按 actor_user_id 过滤。"""
    rows = store.list_eval_runs(actor_user_id=actor_user_id)
    return [
        EvalRunRecord(
            run_id=str(r["run_id"]),
            actor_user_id=str(r["actor_user_id"]),
            experiment_name=str(r["experiment_name"]),
            experiment_id=r["experiment_id"],
            dataset_name=str(r["dataset_name"]),
            summary=dict(r["summary"]),
            cases=list(r["cases"]),
            created_at=str(r["created_at"]),
            langsmith_degraded=bool(r["langsmith_degraded"]),
            gate_role=EVAL_GATE_ROLE,
            blocks_track_a_gate=False,
        )
        for r in rows
    ]

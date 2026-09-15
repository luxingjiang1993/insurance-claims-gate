"""评测实验结果排行榜（W2 Eval Ops · 票 30）。

硬约束（旁路，非合门禁主缝）：
- 默认 CI 合门禁仍以 missions.checks.machine_check 为准；
- 榜上分数不得成为 machine_check 条件；
- 本入口失败可告警，不得改写人闸语义。

单一真源：本地 SQLite `eval_runs`（与票 29 一致）。
不读 LangSmith 实验 API 作为排行榜数据源（避免双源打架）；
LangSmith 仅作跑次旁路上报/降级字段，不驱动榜排序。

主指标：pass_rate = summary.passed / summary.total（total<=0 时为 0.0）。
可按主指标升降序；同分时按 created_at、run_id 升序，保证稳定排序。

Rewrote from: REF-CASE-EVAL-ADVISOR, REF-CASE-OPENEVALS, REF-MISSIONS
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from claims_api.sqlite_store import SqliteCaseStore
from missions.eval_entry import EVAL_GATE_ROLE
from missions.eval_run_persist import list_persisted_eval_runs

DATA_SOURCE = "local_sqlite_eval_runs"
PRIMARY_METRIC_NAME = "pass_rate"

SortBy = Literal["primary_metric"]
SortOrder = Literal["asc", "desc"]


@dataclass
class LeaderboardRow:
    """排行榜一行：实验名 / 主指标 / 时间 / 提交者。"""

    experiment_name: str
    primary_metric: float
    created_at: str
    submitter: str
    run_id: str
    primary_metric_name: str = PRIMARY_METRIC_NAME
    gate_role: str = EVAL_GATE_ROLE
    blocks_track_a_gate: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_name": self.experiment_name,
            "primary_metric": self.primary_metric,
            "primary_metric_name": self.primary_metric_name,
            "created_at": self.created_at,
            "submitter": self.submitter,
            "run_id": self.run_id,
            "gate_role": self.gate_role,
            "blocks_track_a_gate": self.blocks_track_a_gate,
        }


def compute_primary_metric(summary: dict[str, Any]) -> float:
    """从跑次 summary 计算主指标 pass_rate。"""
    total = int(summary.get("total") or 0)
    if total <= 0:
        return 0.0
    passed = int(summary.get("passed") or 0)
    return float(passed) / float(total)


def build_leaderboard(
    store: SqliteCaseStore,
    *,
    sort_by: SortBy = "primary_metric",
    order: SortOrder = "desc",
) -> list[LeaderboardRow]:
    """自本地 eval_runs 构建排行榜；按主指标排序且稳定。"""
    if sort_by != "primary_metric":
        raise ValueError(f"不支持的 sort_by: {sort_by}")
    if order not in ("asc", "desc"):
        raise ValueError(f"不支持的 order: {order}")

    runs = list_persisted_eval_runs(store)
    rows = [
        LeaderboardRow(
            experiment_name=run.experiment_name,
            primary_metric=compute_primary_metric(run.summary),
            created_at=run.created_at,
            submitter=run.actor_user_id,
            run_id=run.run_id,
        )
        for run in runs
    ]

    # 两趟稳定排序：先次键升序，再按主指标（Python sort 稳定）
    rows.sort(key=lambda r: (r.created_at, r.run_id))
    rows.sort(key=lambda r: r.primary_metric, reverse=(order == "desc"))
    return rows

"""OpenEval 旁路 → LangSmith 实验 / 历史对比外形。

硬约束（旁路，非合门禁主缝）：
- 默认 CI 合门禁仍以 missions.checks.machine_check 为准；
- 本入口失败可告警，不得改写人闸语义；
- 不得要求 LLM 才能让轨 A 变绿；
- W1 仅数据集 run + 实验历史对比外形；不含排行榜、不含多人协作（属 W2）。

改写自 CASE-openevals 旁路跑法 + 投顾评估 LangSmith 实验外形。
Rewrote from: REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR, REF-MISSIONS
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4

from fastapi.testclient import TestClient

from missions.eval_entry import (
    EVAL_GATE_ROLE,
    DEFAULT_EVAL_SUITE,
    EvalReport,
    run_eval_negatives,
    to_machine_readable_report,
)

DEFAULT_DATASET_NAME = "claims-gate-openeval-negatives"

# 测试注入；生产路径保持 None
_experiment_client_override: Any | None = None


@dataclass(frozen=True)
class ExperimentHistoryItem:
    """单次实验历史条目（对比外形；无名次/排行榜字段）。"""

    experiment_name: str
    experiment_id: str
    dataset_name: str
    summary: dict[str, Any]
    created_at: str


@dataclass
class ExperimentResult:
    """一次 OpenEval 旁路实验跑次结果。"""

    dataset_name: str
    experiment_name: str
    experiment_id: str | None
    cases: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)
    gate_role: str = EVAL_GATE_ROLE
    blocks_track_a_gate: bool = False
    requires_llm: bool = False


class LangSmithExperimentClient(Protocol):
    """LangSmith 实验最小外形：数据集 + 实验记录 + 历史列表。"""

    def ensure_dataset(self, name: str, description: str) -> str: ...

    def upsert_example(
        self,
        dataset_name: str,
        *,
        example_id: str,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
    ) -> None: ...

    def record_experiment(
        self,
        *,
        experiment_name: str,
        dataset_name: str,
        summary: dict[str, Any],
        cases: list[dict[str, Any]],
    ) -> str: ...

    def list_experiments(self, dataset_name: str) -> list[dict[str, Any]]: ...


class FakeLangSmithExperimentClient:
    """官方外形 mock：记录 dataset / example / experiment，不访问网络。"""

    def __init__(self) -> None:
        self.datasets: dict[str, str] = {}
        self.examples: list[dict[str, Any]] = []
        self.experiments: list[dict[str, Any]] = []

    def ensure_dataset(self, name: str, description: str) -> str:
        if name not in self.datasets:
            self.datasets[name] = description
        return name

    def upsert_example(
        self,
        dataset_name: str,
        *,
        example_id: str,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
    ) -> None:
        self.examples = [
            e for e in self.examples if not (
                e["dataset_name"] == dataset_name and e["example_id"] == example_id
            )
        ]
        self.examples.append(
            {
                "dataset_name": dataset_name,
                "example_id": example_id,
                "inputs": inputs,
                "outputs": outputs,
            }
        )

    def record_experiment(
        self,
        *,
        experiment_name: str,
        dataset_name: str,
        summary: dict[str, Any],
        cases: list[dict[str, Any]],
    ) -> str:
        exp_id = str(uuid4())
        self.experiments.append(
            {
                "experiment_id": exp_id,
                "experiment_name": experiment_name,
                "dataset_name": dataset_name,
                "summary": dict(summary),
                "cases": list(cases),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        return exp_id

    def list_experiments(self, dataset_name: str) -> list[dict[str, Any]]:
        return [
            dict(e) for e in self.experiments if e["dataset_name"] == dataset_name
        ]


class RealLangSmithExperimentClient:
    """真 LangSmith Client 适配：数据集 + project(reference_dataset) 实验外形。"""

    _SUMMARY_MARK = "claims_gate_summary_json:"

    def __init__(self, client: Any | None = None) -> None:
        if client is not None:
            self._client = client
        else:
            import os

            from langsmith import Client  # type: ignore[import-untyped]

            api_key = (
                os.environ.get("LANGCHAIN_API_KEY")
                or os.environ.get("LANGSMITH_API_KEY")
                or ""
            ).strip()
            self._client = Client(api_key=api_key)
        self._dataset_ids: dict[str, str] = {}

    def ensure_dataset(self, name: str, description: str) -> str:
        try:
            ds = self._client.read_dataset(dataset_name=name)
        except Exception:
            ds = self._client.create_dataset(
                dataset_name=name, description=description
            )
        self._dataset_ids[name] = str(getattr(ds, "id", name))
        return name

    def upsert_example(
        self,
        dataset_name: str,
        *,
        example_id: str,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
    ) -> None:
        existing = list(
            self._client.list_examples(
                dataset_name=dataset_name, example_ids=[example_id]
            )
        )
        if existing:
            return
        self._client.create_example(
            inputs=inputs,
            outputs=outputs,
            dataset_name=dataset_name,
            example_id=example_id,
        )

    def record_experiment(
        self,
        *,
        experiment_name: str,
        dataset_name: str,
        summary: dict[str, Any],
        cases: list[dict[str, Any]],
    ) -> str:
        import json

        ds_id = self._dataset_ids.get(dataset_name)
        if ds_id is None:
            self.ensure_dataset(dataset_name, "claims-gate OpenEval bypass")
            ds_id = self._dataset_ids.get(dataset_name)
        summary_blob = self._SUMMARY_MARK + json.dumps(
            summary, ensure_ascii=False, sort_keys=True
        )
        kwargs: dict[str, Any] = {
            "project_name": experiment_name,
            "description": (
                f"claims-gate OpenEval bypass; dataset={dataset_name}; "
                f"{summary_blob}"
            ),
        }
        if ds_id is not None:
            kwargs["reference_dataset_id"] = ds_id
        project = self._client.create_project(**kwargs)
        exp_id = str(getattr(project, "id", ""))
        if not exp_id:
            raise RuntimeError("LangSmith create_project 未返回 experiment id")
        run_id = uuid4()
        self._client.create_run(
            name="openeval_bypass_summary",
            inputs={"dataset_name": dataset_name, "cases": cases},
            run_type="chain",
            id=run_id,
            project_name=experiment_name,
            start_time=datetime.now(timezone.utc),
            tags=["claims-gate", "openeval-bypass", "history-compare"],
            extra={
                "metadata": {
                    "dataset_name": dataset_name,
                    "experiment_name": experiment_name,
                    "gate_role": EVAL_GATE_ROLE,
                    "summary": summary,
                }
            },
        )
        # 与票 26 一致：create 已成功即可；update 失败不抹掉 experiment_id
        try:
            self._client.update_run(
                run_id,
                outputs={"summary": summary, "ok": True},
                end_time=datetime.now(timezone.utc),
            )
        except Exception:
            pass
        return exp_id

    def list_experiments(self, dataset_name: str) -> list[dict[str, Any]]:
        import json

        ds_id = self._dataset_ids.get(dataset_name)
        if ds_id is None:
            ds = self._client.read_dataset(dataset_name=dataset_name)
            ds_id = str(getattr(ds, "id", ""))
            self._dataset_ids[dataset_name] = ds_id
        items: list[dict[str, Any]] = []
        projects = self._client.list_projects(reference_dataset_id=ds_id)
        for p in projects:
            name = getattr(p, "name", None) or ""
            pid = str(getattr(p, "id", name))
            created = getattr(p, "start_time", None) or getattr(
                p, "created_at", None
            )
            if created is not None and hasattr(created, "isoformat"):
                created_at = created.isoformat()
            else:
                created_at = str(created or "")
            desc = getattr(p, "description", "") or ""
            summary: dict[str, Any] = {}
            mark = self._SUMMARY_MARK
            if mark in desc:
                raw = desc.split(mark, 1)[1].strip()
                summary = json.loads(raw)
            items.append(
                {
                    "experiment_id": pid,
                    "experiment_name": name,
                    "dataset_name": dataset_name,
                    "summary": summary,
                    "created_at": created_at,
                }
            )
        return items


def set_experiment_client_override(client: LangSmithExperimentClient | None) -> None:
    """测试注入实验 Client；传 None 清除。"""
    global _experiment_client_override
    _experiment_client_override = client


def reset_experiment_client_override() -> None:
    """清除测试注入。"""
    set_experiment_client_override(None)


def _resolve_experiment_client() -> LangSmithExperimentClient | None:
    if _experiment_client_override is not None:
        return _experiment_client_override
    from claims_api.langsmith_trace import langsmith_tracing_enabled

    if not langsmith_tracing_enabled():
        return None
    try:
        return RealLangSmithExperimentClient()
    except ImportError:
        return None


def run_openeval_experiment(
    http_client: TestClient,
    *,
    experiment_name: str,
    dataset_name: str = DEFAULT_DATASET_NAME,
    suite: tuple[str, ...] | list[str] | None = None,
) -> ExperimentResult:
    """跑 OpenEval 最小旁路集，并将结果关联为 LangSmith 实验（若有 Client）。

    无 Client 时仍返回本地旁路报告；experiment_id 为 None。
    LangSmith 写入失败时 experiment_id 保持 None（不假装成功）；永不写入 machine_check。
    """
    names = tuple(suite) if suite is not None else DEFAULT_EVAL_SUITE
    report: EvalReport = run_eval_negatives(http_client, suite=names)
    payload = to_machine_readable_report(report)
    cases = list(payload["cases"])
    summary = dict(payload["summary"])

    result = ExperimentResult(
        dataset_name=dataset_name,
        experiment_name=experiment_name,
        experiment_id=None,
        cases=cases,
        summary=summary,
        gate_role=EVAL_GATE_ROLE,
        blocks_track_a_gate=False,
        requires_llm=False,
    )

    client = _resolve_experiment_client()
    if client is None:
        return result

    try:
        client.ensure_dataset(
            dataset_name,
            "claims-gate OpenEval bypass negatives (not machine_check)",
        )
        for case in cases:
            client.upsert_example(
                dataset_name,
                example_id=str(case.get("id") or case.get("category")),
                inputs={
                    "evaluator": case.get("evaluator"),
                    "category": case.get("category"),
                    "case_id": case.get("id"),
                },
                outputs={
                    "passed": case.get("passed"),
                    "detail": case.get("detail"),
                },
            )
        exp_id = client.record_experiment(
            experiment_name=experiment_name,
            dataset_name=dataset_name,
            summary=summary,
            cases=cases,
        )
        result.experiment_id = exp_id
    except Exception:
        # 旁路隔离：LangSmith 失败不抛；也不伪造 experiment_id
        result.experiment_id = None
    return result


def list_experiment_history(
    dataset_name: str = DEFAULT_DATASET_NAME,
) -> list[ExperimentHistoryItem]:
    """列出同数据集下的实验历史（对比外形；非排行榜）。"""
    client = _resolve_experiment_client()
    if client is None:
        return []
    raw = client.list_experiments(dataset_name)
    items: list[ExperimentHistoryItem] = []
    for row in raw:
        items.append(
            ExperimentHistoryItem(
                experiment_name=str(row.get("experiment_name") or ""),
                experiment_id=str(row.get("experiment_id") or ""),
                dataset_name=str(row.get("dataset_name") or dataset_name),
                summary=dict(row.get("summary") or {}),
                created_at=str(row.get("created_at") or ""),
            )
        )
    return items


def main() -> None:
    """脚本入口：python -m missions.openeval_langsmith（旁路，非合门禁）。"""
    import json
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    from claims_api.api import app, reset_service

    reset_service()
    http = TestClient(app)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    result = run_openeval_experiment(
        http,
        experiment_name=f"claims-gate-openeval-{stamp}",
    )
    history = list_experiment_history(result.dataset_name)
    out = {
        "gate_role": result.gate_role,
        "blocks_track_a_gate": result.blocks_track_a_gate,
        "dataset_name": result.dataset_name,
        "experiment_name": result.experiment_name,
        "experiment_id": result.experiment_id,
        "summary": result.summary,
        "cases": result.cases,
        "history_count": len(history),
        "docs_note": "旁路，非合门禁主缝；合门禁以 machine_check 为准；不含排行榜",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result.summary.get("failed", 0) == 0 else 2)


if __name__ == "__main__":
    main()

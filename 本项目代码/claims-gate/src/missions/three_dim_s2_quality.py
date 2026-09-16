"""三维 S2 质量旁路：检索 / 引用忠实 / 建议可用性（票 47 / P-E2）。

硬约束：
- 三维拉通可跑；LLM 打分不得当唯一主指标；
- 失败只影响旁路退出码，永不红轨 A / 不进 machine_check；
- 检索复用票 46；忠实复用票 42；可用性见 suggestion_usability。

Rewrote from: REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from missions.citation_faithfulness import run_faithfulness_fixtures
from missions.recall_eval_runner import (
    EVAL_RETRIEVAL_PROFILE,
    RetrieveFn,
    run_frozen_seed_recall,
)
from missions.suggestion_usability import (
    default_usability_fixtures_path,
    run_usability_fixtures,
)

PRIMARY_METRICS_ALLOWED = frozenset(
    {
        "rules_fixtures",
        "rules_or_human",
        "recall_metrics",
        "human",
    }
)


@dataclass
class ThreeDimS2Report:
    """三维质量旁路报告（机读）。"""

    dimensions: dict[str, dict[str, Any]] = field(default_factory=dict)
    all_passed: bool = False
    llm_judge_as_primary: bool = False
    blocks_track_a_gate: bool = False
    gate_role: str = "assist_quality_s2_bypass"
    rewrote_from: str = "REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR"
    docs_note: str = (
        "S2/nightly 三维质量旁路：检索（H1/H2）/ 引用忠实（规则夹具）/ "
        "建议可用性（规则或人工·H5）；LLM 不得作唯一主指标；不红轨 A"
    )

    @property
    def exit_code(self) -> int:
        return 0 if self.all_passed else 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimensions": dict(self.dimensions),
            "all_passed": self.all_passed,
            "exit_code": self.exit_code,
            "llm_judge_as_primary": False,
            "blocks_track_a_gate": self.blocks_track_a_gate,
            "gate_role": self.gate_role,
            "rewrote_from": self.rewrote_from,
            "docs_note": self.docs_note,
        }


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _dim_retrieval(
    *,
    seeds_path: Path | None,
    kb_root: Path | None,
    retrieval_profile: str,
    top_k: int,
    vector_enabled: bool,
    retrieve_fn: RetrieveFn | None,
) -> dict[str, Any]:
    report = run_frozen_seed_recall(
        seeds_path=seeds_path,
        kb_root=kb_root,
        retrieval_profile=retrieval_profile,
        top_k=top_k,
        vector_enabled=vector_enabled,
        retrieve_fn=retrieve_fn,
    )
    passed = bool(report.gates and report.gates.all_passed)
    return {
        "name": "retrieval",
        "primary_metric": "recall_metrics",
        "llm_judge_as_primary": False,
        "passed": passed,
        "exit_code": report.exit_code,
        "summary": {
            "h1_recall_at_1": report.h1_recall_at_1,
            "h1_n": report.h1_n,
            "h2_recall_at_5": report.h2_recall_at_5,
            "h2_mrr": report.h2_mrr,
            "h2_n": report.h2_n,
            "h1_passed": report.gates.h1_passed if report.gates else False,
            "h2_passed": report.gates.h2_passed if report.gates else False,
        },
        "report": report.to_dict(),
    }


def _dim_faithfulness(path: Path) -> dict[str, Any]:
    report = run_faithfulness_fixtures(path)
    passed = report.failed == 0 and report.total > 0
    return {
        "name": "citation_faithfulness",
        "primary_metric": report.primary_metric,
        "llm_judge_as_primary": False,
        "passed": passed,
        "summary": {
            "total": report.total,
            "passed": report.passed,
            "failed": report.failed,
            "gold_subset_n": report.gold_subset_n,
            "gold_subset_h4_status": report.gold_subset_h4_status,
            "grounded_claim_allowed": False,
        },
        "report": report.to_dict(),
    }


def _dim_usability(path: Path) -> dict[str, Any]:
    report = run_usability_fixtures(path)
    return {
        "name": "suggestion_usability",
        "primary_metric": report.primary_metric,
        "llm_judge_as_primary": False,
        "passed": report.passed,
        "summary": {
            "total": report.total,
            "passed_count": report.passed_count,
            "failed_count": report.failed_count,
            "abstain_coverage": report.abstain_coverage,
            "abstain_n": report.abstain_n,
            "misdraft_rate": report.misdraft_rate,
            "h5_passed": report.h5_passed,
        },
        "report": report.to_dict(),
    }


def run_three_dim_s2(
    *,
    seeds_path: Path | str | None = None,
    kb_root: Path | str | None = None,
    faithfulness_fixtures_path: Path | str | None = None,
    usability_fixtures_path: Path | str | None = None,
    retrieval_profile: str = EVAL_RETRIEVAL_PROFILE,
    top_k: int = 5,
    vector_enabled: bool = False,
    retrieve_fn: RetrieveFn | None = None,
    run_retrieval: bool = True,
    run_faithfulness: bool = True,
    run_usability: bool = True,
) -> ThreeDimS2Report:
    """跑三维质量旁路并汇总门槛。"""
    root = _project_root()
    seeds = Path(seeds_path) if seeds_path else (
        root / "artifacts" / "demo_retrieval_seeds" / "demo_retrieval_seeds.v1.json"
    )
    faith = Path(faithfulness_fixtures_path) if faithfulness_fixtures_path else (
        root / "artifacts" / "citation_faithfulness" / "fixtures.v1.json"
    )
    usable = (
        Path(usability_fixtures_path)
        if usability_fixtures_path
        else default_usability_fixtures_path(root=root)
    )
    kb = Path(kb_root) if kb_root else (root / "knowledge_base")

    dims: dict[str, dict[str, Any]] = {}
    if run_retrieval:
        dims["retrieval"] = _dim_retrieval(
            seeds_path=seeds,
            kb_root=kb,
            retrieval_profile=retrieval_profile,
            top_k=top_k,
            vector_enabled=vector_enabled,
            retrieve_fn=retrieve_fn,
        )
    if run_faithfulness:
        dims["citation_faithfulness"] = _dim_faithfulness(faith)
    if run_usability:
        dims["suggestion_usability"] = _dim_usability(usable)

    # 硬拒：任一维若声称 LLM 唯一主指标 → 整门失败
    llm_primary = False
    for dim in dims.values():
        if dim.get("llm_judge_as_primary") is True:
            llm_primary = True
        primary = str(dim.get("primary_metric") or "")
        if primary == "llm_judge" or (
            "llm" in primary.lower()
            and "rules" not in primary.lower()
            and "human" not in primary.lower()
            and primary not in PRIMARY_METRICS_ALLOWED
        ):
            llm_primary = True

    all_passed = (
        bool(dims)
        and all(bool(d.get("passed")) for d in dims.values())
        and not llm_primary
    )
    return ThreeDimS2Report(
        dimensions=dims,
        all_passed=all_passed,
        llm_judge_as_primary=False,
        blocks_track_a_gate=False,
    )


def write_report(report: ThreeDimS2Report, path: Path | str) -> Path:
    """写出 UTF-8 JSON 三维报告。"""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return out

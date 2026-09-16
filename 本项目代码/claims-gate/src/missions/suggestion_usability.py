"""建议可用性评测：规则或人工为主（票 47 / P-E2 · 可用性维）。

硬约束：
- 主指标 = rules_or_human（规则为主，人工可并存标注）；禁止 LLM 打分作唯一主指标；
- 人工标签不得在规则失败时单独翻绿；human_usable=false 在规则已过时仅作旁注，不否决；
- H5：预登记拒答覆盖率 100%；误起草率 ≤ 5%（分母=预登记拒答条数）；
- 旁路 S2，不进 machine_check / 默认 pytest 绿。

Rewrote from: REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from missions.assist_disposition import (
    mark_citations_unadoptable_for_abstain,
    resolve_assist_disposition,
)

# SPEC-02B-P 决策 9 · H5
H5_ABSTAIN_COVERAGE_THRESHOLD = 1.0
H5_MISDRAFT_RATE_THRESHOLD = 0.05
H5_MIN_ABSTAIN_N = 1

PRIMARY_METRIC = "rules_or_human"
SCHEMA_ID = "claims-gate-suggestion-usability-fixtures-v1"


class UsabilityEvalError(ValueError):
    """可用性评测宣称或夹具外形不合法。"""


@dataclass(frozen=True)
class UsabilityCaseResult:
    """单条建议可用性判定。"""

    case_id: str
    passed: bool
    actual_disposition: str
    actual_abstain_reason: str | None
    expected_disposition: str
    usable_for_adopt: bool
    is_misdraft: bool
    detail: str = ""
    primary_metric: str = PRIMARY_METRIC
    llm_judge_as_primary: bool = False
    human_usable: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class H5GateResult:
    """H5 门槛对照（机读）。"""

    abstain_coverage: float
    abstain_n: int
    abstain_coverage_threshold: float
    misdraft_rate: float
    scored_n: int
    misdraft_rate_threshold: float
    h5_passed: bool
    primary_metric: str = PRIMARY_METRIC
    llm_judge_as_primary: bool = False
    blocks_track_a_gate: bool = False
    gate_role: str = "assist_quality_s2_bypass"
    docs_note: str = (
        "S2 旁路：建议可用性（规则/人工）；H5 覆盖率与误起草率；"
        "LLM 不得作唯一主指标；失败不红轨 A"
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class UsabilityFixtureReport:
    """可用性夹具跑批报告。"""

    cases: list[dict[str, Any]] = field(default_factory=list)
    primary_metric: str = PRIMARY_METRIC
    llm_judge_as_primary: bool = False
    abstain_coverage: float = 0.0
    abstain_n: int = 0
    misdraft_rate: float = 0.0
    scored_n: int = 0
    gates: H5GateResult | None = None
    docs_note: str = ""

    @property
    def total(self) -> int:
        return len(self.cases)

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.cases if c.get("passed"))

    @property
    def failed_count(self) -> int:
        return self.total - self.passed_count

    @property
    def all_cases_passed(self) -> bool:
        return self.total > 0 and self.failed_count == 0

    @property
    def h5_passed(self) -> bool:
        return bool(self.gates and self.gates.h5_passed)

    @property
    def passed(self) -> bool:
        return self.all_cases_passed and self.h5_passed

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_metric": self.primary_metric,
            "llm_judge_as_primary": False,
            "passed": self.passed,
            "all_cases_passed": self.all_cases_passed,
            "h5_passed": self.h5_passed,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "total": self.total,
            "abstain_coverage": self.abstain_coverage,
            "abstain_n": self.abstain_n,
            "misdraft_rate": self.misdraft_rate,
            "scored_n": self.scored_n,
            "gates": self.gates.to_dict() if self.gates else None,
            "docs_note": self.docs_note,
            "cases": list(self.cases),
        }


def evaluate_h5_gates(
    *,
    abstain_coverage: float,
    abstain_n: int,
    misdraft_rate: float,
    scored_n: int,
) -> H5GateResult:
    """对照 H5：覆盖率 100% 且误起草率 ≤ 5%；样本量至少 1 条拒答预登记。"""
    cover_ok = (
        abstain_n >= H5_MIN_ABSTAIN_N
        and abstain_coverage >= H5_ABSTAIN_COVERAGE_THRESHOLD
    )
    draft_ok = scored_n > 0 and misdraft_rate <= H5_MISDRAFT_RATE_THRESHOLD
    return H5GateResult(
        abstain_coverage=float(abstain_coverage),
        abstain_n=int(abstain_n),
        abstain_coverage_threshold=H5_ABSTAIN_COVERAGE_THRESHOLD,
        misdraft_rate=float(misdraft_rate),
        scored_n=int(scored_n),
        misdraft_rate_threshold=H5_MISDRAFT_RATE_THRESHOLD,
        h5_passed=bool(cover_ok and draft_ok),
    )


def _has_latch_token(suggestion: Mapping[str, Any] | None) -> bool:
    if not suggestion:
        return False
    token = suggestion.get("human_latch_token")
    return bool(token)


def evaluate_usability_case(case: Mapping[str, Any]) -> UsabilityCaseResult:
    """规则判定单条建议可用性（可叠加人工标签，但 LLM 不作唯一主指标）。"""
    case_id = str(case.get("id") or "")
    scenario = dict(case.get("scenario") or {})
    expected = dict(case.get("expected") or {})
    suggestion = dict(case.get("suggestion") or {})
    human_usable = case.get("human_usable")
    if human_usable is not None:
        human_usable = bool(human_usable)

    expected_disp = str(expected.get("assist_disposition") or "")
    expected_reason = expected.get("abstain_reason")
    expected_usable = bool(expected.get("usable_for_adopt"))
    must_no_token = bool(expected.get("must_not_issue_latch_token", True))

    citations = [dict(c) for c in (scenario.get("citations") or [])]
    disposition, reason, _latch = resolve_assist_disposition(
        query=str(scenario.get("query") or ""),
        conflict_route_id=scenario.get("conflict_route_id"),
        can_external_deny=bool(scenario.get("can_external_deny", True)),
        retrieval_profile=str(scenario.get("retrieval_profile") or "clause_primary"),
        stance=str(scenario.get("stance") or "approve"),
        intended_external_action=scenario.get("intended_external_action"),
        citations=citations,
    )

    if disposition == "abstain" and reason is not None:
        mark_citations_unadoptable_for_abstain(citations, reason)

    adoptable_left = any(c.get("adoptable") is True for c in citations)
    usable_for_adopt = disposition == "draft" and adoptable_left

    is_misdraft = expected_disp == "abstain" and disposition == "draft"
    detail_parts: list[str] = []

    disp_ok = disposition == expected_disp
    if not disp_ok:
        detail_parts.append(
            f"disposition 期望 {expected_disp} 实际 {disposition}"
        )

    reason_ok = True
    if expected_reason is not None:
        reason_ok = reason == expected_reason
        if not reason_ok:
            detail_parts.append(
                f"abstain_reason 期望 {expected_reason} 实际 {reason}"
            )

    usable_ok = usable_for_adopt is expected_usable
    if not usable_ok:
        detail_parts.append(
            f"usable_for_adopt 期望 {expected_usable} 实际 {usable_for_adopt}"
        )

    token_ok = True
    if must_no_token and _has_latch_token(suggestion):
        token_ok = False
        detail_parts.append("禁止出现 human_latch_token")

    rules_ok = disp_ok and reason_ok and usable_ok and token_ok and not is_misdraft

    # 人工标签可并存；不得单独用 LLM；规则失败时不得仅靠人工翻绿
    if human_usable is not None and not rules_ok:
        detail_parts.append("规则未过，人工标签不得单独翻绿")

    passed = rules_ok
    if not detail_parts:
        detail_parts.append("规则判定通过")

    return UsabilityCaseResult(
        case_id=case_id,
        passed=passed,
        actual_disposition=disposition,
        actual_abstain_reason=reason,
        expected_disposition=expected_disp,
        usable_for_adopt=usable_for_adopt,
        is_misdraft=is_misdraft,
        detail="; ".join(detail_parts),
        primary_metric=PRIMARY_METRIC,
        llm_judge_as_primary=False,
        human_usable=human_usable,
    )


def _load_fixtures_payload(path_or_data: Path | str | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(path_or_data, Mapping):
        return dict(path_or_data)
    path = Path(path_or_data)
    return json.loads(path.read_text(encoding="utf-8"))


def run_usability_fixtures(
    path_or_data: Path | str | Mapping[str, Any],
) -> UsabilityFixtureReport:
    """加载夹具并跑规则可用性；主指标恒为 rules_or_human。"""
    raw = _load_fixtures_payload(path_or_data)
    if raw.get("llm_judge_as_primary") is True:
        raise UsabilityEvalError("禁止将 LLM 打分设为可用性唯一主指标")
    primary = raw.get("primary_metric")
    if primary not in (None, PRIMARY_METRIC, "rules_or_human", "rules_fixtures", "human"):
        raise UsabilityEvalError(
            f"可用性主指标须为 {PRIMARY_METRIC}（或 human/rules），收到: {primary!r}"
        )
    if primary == "llm_judge":
        raise UsabilityEvalError("禁止将 LLM 打分设为可用性唯一主指标")

    report = UsabilityFixtureReport(
        docs_note=str(raw.get("docs_note") or ""),
        primary_metric=PRIMARY_METRIC,
        llm_judge_as_primary=False,
    )

    abstain_expected = 0
    abstain_hit = 0
    misdraft_n = 0
    scored = 0

    for case in raw.get("cases") or []:
        result = evaluate_usability_case(case)
        report.cases.append(result.to_dict())
        scored += 1
        expected_disp = str((case.get("expected") or {}).get("assist_disposition") or "")
        if expected_disp == "abstain":
            abstain_expected += 1
            if result.actual_disposition == "abstain":
                abstain_hit += 1
            if result.is_misdraft:
                misdraft_n += 1

    coverage = (abstain_hit / abstain_expected) if abstain_expected else 0.0
    # 误起草率分母 = 预登记拒答条数（SPEC H5）；非全量 scored
    misdraft_rate = (
        (misdraft_n / abstain_expected) if abstain_expected else (1.0 if scored else 1.0)
    )
    report.abstain_coverage = coverage
    report.abstain_n = abstain_expected
    report.misdraft_rate = misdraft_rate
    report.scored_n = scored
    report.gates = evaluate_h5_gates(
        abstain_coverage=coverage,
        abstain_n=abstain_expected,
        misdraft_rate=misdraft_rate,
        scored_n=abstain_expected if abstain_expected else scored,
    )
    return report


def default_usability_fixtures_path(*, root: Path | None = None) -> Path:
    """默认可用性夹具路径。"""
    base = root or Path(__file__).resolve().parents[2]
    return base / "artifacts" / "suggestion_usability" / "fixtures.v1.json"

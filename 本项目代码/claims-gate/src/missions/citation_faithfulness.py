"""引用→断言忠实检查：α 规则/夹具为主（票 42 / P-H4）；β 接 κ（票 50）。

硬约束（旁路，非合门禁主缝）：
- 主指标 = rules_fixtures；禁止把 LLM-as-judge 当唯一主指标；
- 绑金标薄切片（P-E3）子集；n<10 则 H4=deferred，禁止宣称 grounded；
- grounded 须另过 κ≥0.60（见 missions.judge_human_kappa）且非合成；
- 默认 CI 合门禁仍以 missions.checks.machine_check 为准。

规则（SPEC 决策 13）：
1. stance_conflict — 通赔断言 vs 免赔/除外摘录；
2. support_registry — 预登记支撑关系（claim_key → 允许的 doc_id+clause_item）；
3. entity_overlap — 摘录须含断言关键实体（或显式 required_entities）。

Rewrote from: REF-CASE-OPENEVALS
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from missions.gold_label_io import (  # noqa: E402
    GoldLabelDataset,
    assess_h4_status,
    load_dataset_file,
)

PRIMARY_METRIC = "rules_fixtures"
SCHEMA_ID = "claims-gate-citation-faithfulness-fixtures-v1"

_PAY_HINTS = ("通赔", "全额通赔", "给付", "可赔", "同意赔付", "保障范围")
_DENY_HINTS = ("免赔", "除外", "责任免除", "不承担", "拒赔", "剔除")

# 断言中可抽取的最小实体提示（中文名词片语粗切）
_ENTITY_STOP = frozenset(
    {
        "属于",
        "主险",
        "保障",
        "范围",
        "可以",
        "可通赔",
        "通赔",
        "全额",
        "依据",
        "条款",
        "请",
        "引用",
        "支撑",
        "这一",
        "断言",
        "生成",
        "可采纳",
        "建议",
        "条文",
        "来",
        "并",
        "的",
        "是",
        "已",
        "按",
        "约定",
        "保险人",
        "费用",
    }
)


class FaithfulnessEvalError(ValueError):
    """忠实评测宣称或夹具外形不合法。"""


@dataclass(frozen=True)
class FaithfulnessResult:
    """单条引用→断言忠实判定。"""

    faithful: bool
    rule: str
    detail: str = ""
    primary_metric: str = PRIMARY_METRIC
    llm_judge_as_primary: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "faithful": self.faithful,
            "rule": self.rule,
            "detail": self.detail,
            "primary_metric": self.primary_metric,
            "llm_judge_as_primary": False,
        }


@dataclass
class FaithfulnessFixtureReport:
    """夹具跑批报告（S2）。"""

    cases: list[dict[str, Any]] = field(default_factory=list)
    primary_metric: str = PRIMARY_METRIC
    llm_judge_as_primary: bool = False
    gold_subset_n: int = 0
    gold_subset_h4_status: str = "deferred"
    docs_note: str = ""

    @property
    def total(self) -> int:
        return len(self.cases)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.cases if c.get("passed"))

    @property
    def failed(self) -> int:
        return self.total - self.passed

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_metric": self.primary_metric,
            "llm_judge_as_primary": False,
            "passed": self.passed,
            "failed": self.failed,
            "total": self.total,
            "gold_subset_n": self.gold_subset_n,
            "gold_subset_h4_status": self.gold_subset_h4_status,
            "docs_note": self.docs_note,
            "cases": list(self.cases),
        }


@dataclass
class GoldThinSliceFaithfulnessReport:
    """金标薄切片子集上的忠实评测（P-E3 边界诚实）。"""

    n: int
    h4_status: str
    faithfulness_rate: float | None
    primary_metric: str = PRIMARY_METRIC
    llm_judge_as_primary: bool = False
    grounded_claim_allowed: bool = False
    matched: int = 0
    detail: str = ""

    kappa: float | None = None
    is_synthetic: bool = False

    def assert_grounded_claim_allowed(self) -> None:
        """H4 全部门：n≥10 + 忠实率≥0.85 + κ≥0.60 + 非合成。"""
        if self.grounded_claim_allowed:
            return
        raise FaithfulnessEvalError(
            f"H4={self.h4_status}，禁止宣称 grounded"
            f"（primary_metric={self.primary_metric}；"
            f"n={self.n}；faithfulness_rate={self.faithfulness_rate}；"
            f"κ={self.kappa}；is_synthetic={self.is_synthetic}；"
            "须金标 n≥10、忠实率≥0.85 且 κ≥0.60 且非合成）"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "n": self.n,
            "h4_status": self.h4_status,
            "faithfulness_rate": self.faithfulness_rate,
            "kappa": self.kappa,
            "is_synthetic": self.is_synthetic,
            "primary_metric": self.primary_metric,
            "llm_judge_as_primary": False,
            "grounded_claim_allowed": self.grounded_claim_allowed,
            "matched": self.matched,
            "detail": self.detail,
        }


def _citation_blob(citation: dict[str, Any]) -> str:
    return (
        str(citation.get("quote") or "")
        + " "
        + str(citation.get("clause_item") or "")
    )


def _assertion_asks_pay(assertion: str) -> bool:
    return any(h in assertion for h in _PAY_HINTS)


def _blob_is_denyish(blob: str) -> bool:
    return any(h in blob for h in _DENY_HINTS)


def _extract_entities(assertion: str) -> list[str]:
    """粗抽断言实体：连续汉字片语，去掉停用片语。"""
    import re

    parts = re.findall(r"[\u4e00-\u9fff]{2,}", assertion)
    out: list[str] = []
    for p in parts:
        if p in _ENTITY_STOP:
            continue
        if any(h in p for h in _PAY_HINTS) and len(p) <= 4:
            continue
        if p not in out:
            out.append(p)
    return out


def _registry_allows(
    claim_key: str,
    citation: dict[str, Any],
    support_registry: dict[str, list[dict[str, str]]] | None,
) -> bool | None:
    """None = 无登记；True/False = 在册是否允许。"""
    if not support_registry or not claim_key:
        return None
    allowed = support_registry.get(claim_key)
    if allowed is None:
        return None
    doc_id = str(citation.get("doc_id") or "")
    clause_item = str(citation.get("clause_item") or "")
    for item in allowed:
        if (
            str(item.get("doc_id") or "") == doc_id
            and str(item.get("clause_item") or "") == clause_item
        ):
            return True
    return False


def check_citation_faithfulness(
    *,
    assertion: str,
    citation: dict[str, Any],
    claim_key: str | None = None,
    required_entities: list[str] | None = None,
    support_registry: dict[str, list[dict[str, str]]] | None = None,
) -> FaithfulnessResult:
    """规则忠实判定：摘录是否支撑断言。

    优先级：support_registry（若有 claim_key 登记）>
    stance_conflict > entity_overlap。
    """
    key = (claim_key or "").strip()
    reg = _registry_allows(key, citation, support_registry)
    if reg is True:
        return FaithfulnessResult(
            faithful=True,
            rule="support_registry",
            detail=f"预登记允许 {key}",
        )
    if reg is False:
        return FaithfulnessResult(
            faithful=False,
            rule="support_registry",
            detail=f"预登记不支持 {key}→"
            f"{citation.get('doc_id')}/{citation.get('clause_item')}",
        )

    blob = _citation_blob(citation)
    # 通赔断言 + 免赔/除外摘录 → 不忠实（「不承担给付」中的「给付」不算支撑）
    if _assertion_asks_pay(assertion) and _blob_is_denyish(blob):
        return FaithfulnessResult(
            faithful=False,
            rule="stance_conflict",
            detail="通赔断言与免赔/除外摘录冲突",
        )

    entities = list(required_entities or []) or _extract_entities(assertion)
    if entities:
        missing = [e for e in entities if e not in blob]
        if missing:
            return FaithfulnessResult(
                faithful=False,
                rule="entity_overlap",
                detail="摘录缺少关键实体: " + ",".join(missing),
            )
        return FaithfulnessResult(
            faithful=True,
            rule="entity_overlap",
            detail="摘录覆盖关键实体",
        )

    # 无实体可抽且无 stance 冲突 → 保守视为不忠实（避免空断言过门）
    if not assertion.strip() or not blob.strip():
        return FaithfulnessResult(
            faithful=False,
            rule="entity_overlap",
            detail="断言或摘录为空",
        )
    return FaithfulnessResult(
        faithful=True,
        rule="entity_overlap",
        detail="无显式实体要求且无 stance 冲突",
    )


def is_citation_unfaithful_for_assist(
    query: str,
    citations: list[dict[str, Any]],
) -> bool:
    """供 assist_disposition 调用的薄封装（与夹具同规则栈）。"""
    if not citations:
        return False
    # 查询同时含通赔与免赔提示 → 自相矛盾，不忠实
    if _assertion_asks_pay(query) and any(h in query for h in _DENY_HINTS):
        return True
    if not _assertion_asks_pay(query):
        return False
    for c in citations:
        result = check_citation_faithfulness(assertion=query, citation=c)
        if not result.faithful:
            return True
    return False


def _parse_support_registry(
    raw: list[dict[str, Any]] | dict[str, Any] | None,
) -> dict[str, list[dict[str, str]]]:
    if not raw:
        return {}
    if isinstance(raw, dict):
        out: dict[str, list[dict[str, str]]] = {}
        for k, v in raw.items():
            out[str(k)] = [
                {
                    "doc_id": str(item.get("doc_id") or ""),
                    "clause_item": str(item.get("clause_item") or ""),
                }
                for item in (v or [])
            ]
        return out
    out = {}
    for row in raw:
        key = str(row.get("claim_key") or "")
        if not key:
            continue
        allowed = []
        for item in row.get("allowed_citations") or []:
            allowed.append(
                {
                    "doc_id": str(item.get("doc_id") or ""),
                    "clause_item": str(item.get("clause_item") or ""),
                }
            )
        out[key] = allowed
    return out


def run_faithfulness_fixtures(
    path: str | Path,
) -> FaithfulnessFixtureReport:
    """加载夹具并跑规则检查；主指标恒为 rules_fixtures。"""
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    if raw.get("llm_judge_as_primary") is True:
        raise FaithfulnessEvalError("禁止将 LLM-as-judge 设为忠实主指标")
    if raw.get("primary_metric") not in (None, PRIMARY_METRIC, "rules_fixtures"):
        raise FaithfulnessEvalError(
            f"α 主指标须为 {PRIMARY_METRIC}，收到: {raw.get('primary_metric')}"
        )

    registry = _parse_support_registry(raw.get("support_registry"))
    report = FaithfulnessFixtureReport(
        docs_note=str(raw.get("docs_note") or ""),
        primary_metric=PRIMARY_METRIC,
        llm_judge_as_primary=False,
    )

    for case in raw.get("cases") or []:
        assertion = str(case.get("assertion") or "")
        citation = dict(case.get("citation") or {})
        claim_key = case.get("claim_key")
        required = case.get("required_entities")
        expected = bool(case.get("expected_faithful"))
        result = check_citation_faithfulness(
            assertion=assertion,
            citation=citation,
            claim_key=str(claim_key) if claim_key else None,
            required_entities=list(required) if required else None,
            support_registry=registry,
        )
        matched = result.faithful is expected
        report.cases.append(
            {
                "id": case.get("id"),
                "expected_faithful": expected,
                "actual_faithful": result.faithful,
                "rule": result.rule,
                "detail": result.detail,
                "passed": matched,
            }
        )

    subset = raw.get("gold_thin_slice_subset") or {}
    bound_ids = [str(x) for x in (subset.get("bound_case_ids") or [])]
    report.gold_subset_n = len(bound_ids)
    report.gold_subset_h4_status = assess_h4_status(report.gold_subset_n)

    source = subset.get("source")
    if source:
        # 相对 claims-gate 根解析；n 以 bound 子集为准（P-E3 边界诚实）
        root = Path(__file__).resolve().parents[2]
        src_path = root / str(source)
        if src_path.is_file():
            gold = load_dataset_file(src_path)
            if bound_ids:
                bound_set = set(bound_ids)
                filtered = [r for r in gold.records if r.case_id in bound_set]
                report.gold_subset_n = len(filtered)
            else:
                report.gold_subset_n = len(gold.records)
            report.gold_subset_h4_status = assess_h4_status(report.gold_subset_n)

    return report


def evaluate_gold_thin_slice_faithfulness(
    dataset: GoldLabelDataset,
) -> GoldThinSliceFaithfulnessReport:
    """在金标薄切片上汇总忠实率外形；n 不足诚实 deferred。

    α：仅当 inputs 含可机读 assertion+citation 时才跑规则计分；
    缺少机读字段时 faithfulness_rate=None，禁止用 expected 自洽冒充。
    禁止 grounded 宣称。
    """
    n = len(dataset.records)
    h4 = assess_h4_status(n)
    matched = 0
    scored = 0
    skipped_no_machine_inputs = 0
    for rec in dataset.records:
        expected = rec.expected or {}
        if "citation_faithful" not in expected:
            continue
        want = bool(expected.get("citation_faithful"))
        inputs = rec.inputs or {}
        assertion = str(inputs.get("assertion") or "").strip()
        citation = inputs.get("citation")
        if not (isinstance(citation, dict) and assertion):
            skipped_no_machine_inputs += 1
            continue
        result = check_citation_faithfulness(
            assertion=assertion,
            citation=citation,
        )
        scored += 1
        if result.faithful is want:
            matched += 1

    rate: float | None
    if scored == 0:
        rate = None
        detail = (
            "无可用机读 assertion+citation 跑规则；"
            f"跳过 {skipped_no_machine_inputs} 条外形样例；"
            "非 LLM judge；禁止用 expected 自洽冒充忠实率"
        )
    else:
        rate = matched / scored
        detail = (
            f"规则/夹具计分 {matched}/{scored}；"
            f"跳过无机构造 {skipped_no_machine_inputs}；"
            "非 LLM judge；非真外聘双标运营跑分"
        )

    from missions.judge_human_kappa import (
        assess_grounded_claim_allowed,
        evaluate_thin_slice_kappa,
    )

    kappa_report = evaluate_thin_slice_kappa(
        dataset,
        faithfulness_rate=rate,
    )
    allowed = kappa_report.grounded_claim_allowed
    if kappa_report.is_synthetic:
        detail = f"{detail}；合成/外形样例不得冒充 grounded（κ 模块）"

    return GoldThinSliceFaithfulnessReport(
        n=n,
        h4_status=h4,
        faithfulness_rate=rate,
        matched=matched,
        detail=detail,
        grounded_claim_allowed=allowed,
        kappa=kappa_report.kappa,
        is_synthetic=kappa_report.is_synthetic,
    )


def main(argv: list[str] | None = None) -> int:
    """约定脚本入口：python -m missions.citation_faithfulness run --file ..."""
    parser = argparse.ArgumentParser(description="引用忠实规则/夹具旁路（非合门禁）")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run_p = sub.add_parser("run", help="跑夹具")
    run_p.add_argument(
        "--file",
        type=Path,
        default=Path("artifacts/citation_faithfulness/fixtures.v1.json"),
    )
    args = parser.parse_args(argv)
    if args.cmd == "run":
        report = run_faithfulness_fixtures(args.file)
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return 0 if report.failed == 0 else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

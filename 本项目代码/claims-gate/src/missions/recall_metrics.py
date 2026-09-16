"""冻结集 Recall@K / MRR 与 H1/H2 门槛对照（票 46 / P-R3）。

硬约束：
- 指标可在 Demo 检索种子上复现；对照 SPEC H1/H2；
- 不得写入 machine_check / 默认 pytest 绿；
- 造问增广仅隔离参考，不并入主集计量。

Rewrote from: REF-CASE-RECALL
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence

# SPEC-02B-P 决策 9
H1_THRESHOLD = 0.95
H2_RECALL5_THRESHOLD = 0.70
H2_MRR_THRESHOLD = 0.55
H1_MIN_N = 15
H2_MIN_N = 20


def recall_at_k(
    ranked_ids: Sequence[str],
    relevant_ids: Iterable[str],
    k: int,
) -> float:
    """单查询 Recall@K = |相关 ∩ top-K| / |相关|；无相关或 k<=0 时为 0。"""
    if k <= 0:
        return 0.0
    relevant = {str(x) for x in relevant_ids if str(x).strip()}
    if not relevant:
        return 0.0
    top = [str(x) for x in ranked_ids[:k]]
    hit = sum(1 for x in relevant if x in top)
    return float(hit) / float(len(relevant))


def mean_reciprocal_rank(
    ranked_ids: Sequence[str],
    relevant_ids: Iterable[str],
) -> float:
    """单查询 MRR：首个相关项排名的倒数；未命中为 0。"""
    relevant = {str(x) for x in relevant_ids if str(x).strip()}
    if not relevant:
        return 0.0
    for idx, item in enumerate(ranked_ids, start=1):
        if str(item) in relevant:
            return 1.0 / float(idx)
    return 0.0


@dataclass(frozen=True)
class MetricSummary:
    """一组查询上的均值指标。"""

    n: int
    mean_recall: float
    mean_mrr: float


def summarize_query_metrics(
    rows: Sequence[Mapping[str, Any]],
    *,
    recall_key: str | None = None,
    mrr_key: str | None = None,
) -> MetricSummary:
    """对查询行求均值；缺键按 0 计。"""
    n = len(rows)
    if n == 0:
        return MetricSummary(n=0, mean_recall=0.0, mean_mrr=0.0)
    recall_sum = 0.0
    mrr_sum = 0.0
    for row in rows:
        if recall_key is not None:
            recall_sum += float(row.get(recall_key) or 0.0)
        if mrr_key is not None:
            mrr_sum += float(row.get(mrr_key) or 0.0)
    return MetricSummary(
        n=n,
        mean_recall=(recall_sum / n) if recall_key else 0.0,
        mean_mrr=(mrr_sum / n) if mrr_key else 0.0,
    )


@dataclass(frozen=True)
class HypothesisGateResult:
    """H1/H2 门槛对照结果（机读）。"""

    h1_recall_at_1: float
    h1_n: int
    h1_threshold: float
    h1_min_n: int
    h1_passed: bool
    h2_recall_at_5: float
    h2_mrr: float
    h2_n: int
    h2_recall5_threshold: float
    h2_mrr_threshold: float
    h2_min_n: int
    h2_passed: bool
    all_passed: bool
    blocks_track_a_gate: bool = False
    gate_role: str = "assist_quality_s2_bypass"
    docs_note: str = (
        "S2/nightly 旁路：冻结 Demo 检索种子上的 Recall@K/MRR；"
        "对照 H1/H2；失败不红轨 A / 不进 machine_check"
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_h1_h2_gates(
    *,
    h1_recall_at_1: float,
    h1_n: int,
    h2_recall_at_5: float,
    h2_mrr: float,
    h2_n: int,
    h1_threshold: float = H1_THRESHOLD,
    h2_recall5_threshold: float = H2_RECALL5_THRESHOLD,
    h2_mrr_threshold: float = H2_MRR_THRESHOLD,
    h1_min_n: int = H1_MIN_N,
    h2_min_n: int = H2_MIN_N,
) -> HypothesisGateResult:
    """对照 SPEC：H1=Recall@1；H2=Recall@5 或 MRR（且样本量达标）。"""
    h1_passed = h1_n >= h1_min_n and h1_recall_at_1 >= h1_threshold
    h2_metric_ok = (
        h2_recall_at_5 >= h2_recall5_threshold or h2_mrr >= h2_mrr_threshold
    )
    h2_passed = h2_n >= h2_min_n and h2_metric_ok
    return HypothesisGateResult(
        h1_recall_at_1=float(h1_recall_at_1),
        h1_n=int(h1_n),
        h1_threshold=float(h1_threshold),
        h1_min_n=int(h1_min_n),
        h1_passed=bool(h1_passed),
        h2_recall_at_5=float(h2_recall_at_5),
        h2_mrr=float(h2_mrr),
        h2_n=int(h2_n),
        h2_recall5_threshold=float(h2_recall5_threshold),
        h2_mrr_threshold=float(h2_mrr_threshold),
        h2_min_n=int(h2_min_n),
        h2_passed=bool(h2_passed),
        all_passed=bool(h1_passed and h2_passed),
    )

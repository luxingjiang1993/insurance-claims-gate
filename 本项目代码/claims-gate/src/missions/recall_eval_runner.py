"""在冻结 Demo 检索种子上跑 Recall@K / MRR（票 46 / P-R3 · S2）。

硬约束：
- 主集仅 artifacts/demo_retrieval_seeds 冻结 JSON；造问增广不得并入计量；
- 默认使用 retrieval_profile=demo_seed_eval + 关键词腿（可复现）；
- 产出对照 H1/H2 门槛的机读报告；失败退出码非 0，但不红轨 A。

Rewrote from: REF-CASE-RECALL
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

from missions.demo_retrieval_seeds import (
    BUCKET_CLAUSE,
    BUCKET_SEMANTIC,
    DemoRetrievalQuery,
    DemoRetrievalSeeds,
    default_main_path,
    load_demo_retrieval_seeds,
)
from missions.recall_metrics import (
    HypothesisGateResult,
    evaluate_h1_h2_gates,
    mean_reciprocal_rank,
    recall_at_k,
    summarize_query_metrics,
)
from missions.track_llm_optional.hybrid_retrieval import (
    HybridRetrievalConfig,
    hybrid_retrieve,
)

# 评测默认：覆盖种子涉及的全部文档类型；非作业默认 profile
EVAL_RETRIEVAL_PROFILE = "demo_seed_eval"
DEFAULT_TOP_K = 5

RetrieveFn = Callable[[str], Sequence[str]]


@dataclass
class QueryRecallRow:
    """单条查询的召回明细。"""

    query_id: str
    bucket: str
    query: str
    relevant_clause_items: list[str]
    ranked_clause_items: list[str]
    recall_at_1: float
    recall_at_5: float
    mrr: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RecallEvalReport:
    """冻结集 Recall 评测报告（机读）。"""

    dataset_id: str
    dataset_version: str
    retrieval_profile: str
    vector_enabled: bool
    top_k: int
    queries: list[QueryRecallRow] = field(default_factory=list)
    h1_recall_at_1: float = 0.0
    h1_n: int = 0
    h2_recall_at_5: float = 0.0
    h2_mrr: float = 0.0
    h2_n: int = 0
    gates: HypothesisGateResult | None = None
    blocks_track_a_gate: bool = False
    gate_role: str = "assist_quality_s2_bypass"
    rewrote_from: str = "REF-CASE-RECALL"
    docs_note: str = (
        "S2/nightly：冻结 Demo 检索种子 Recall@K/MRR；对照 H1/H2；"
        "不进默认 pytest 绿 / machine_check"
    )

    @property
    def exit_code(self) -> int:
        if self.gates is None:
            return 1
        return 0 if self.gates.all_passed else 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "dataset_version": self.dataset_version,
            "retrieval_profile": self.retrieval_profile,
            "vector_enabled": self.vector_enabled,
            "top_k": self.top_k,
            "queries": [q.to_dict() for q in self.queries],
            "h1": {
                "bucket": BUCKET_CLAUSE,
                "n": self.h1_n,
                "recall_at_1": self.h1_recall_at_1,
            },
            "h2": {
                "bucket": BUCKET_SEMANTIC,
                "n": self.h2_n,
                "recall_at_5": self.h2_recall_at_5,
                "mrr": self.h2_mrr,
            },
            "gates": self.gates.to_dict() if self.gates else None,
            "exit_code": self.exit_code,
            "blocks_track_a_gate": self.blocks_track_a_gate,
            "gate_role": self.gate_role,
            "rewrote_from": self.rewrote_from,
            "docs_note": self.docs_note,
        }


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_retrieve_fn(
    *,
    kb_root: Path,
    retrieval_profile: str,
    top_k: int,
    vector_enabled: bool,
) -> RetrieveFn:
    """默认检索：hybrid_retrieve；评测默认可关向量以复现。"""
    cfg = HybridRetrievalConfig(
        keyword_weight=0.7,
        vector_weight=0.3,
        vector_enabled=vector_enabled,
    )

    def _retrieve(query: str) -> list[str]:
        citations, _portrait = hybrid_retrieve(
            query,
            kb_root=kb_root,
            retrieval_profile=retrieval_profile,
            top_k=top_k,
            cfg=cfg,
            vector_searcher=None,
        )
        return [str(c.get("clause_item") or "") for c in citations]

    return _retrieve


def _row_for_query(
    q: DemoRetrievalQuery,
    *,
    ranked: Sequence[str],
) -> QueryRecallRow:
    relevant = [str(x) for x in (q.expected.get("relevant_clause_items") or [])]
    ranked_list = [str(x) for x in ranked if str(x).strip()]
    return QueryRecallRow(
        query_id=q.query_id,
        bucket=q.bucket,
        query=q.query,
        relevant_clause_items=relevant,
        ranked_clause_items=ranked_list,
        recall_at_1=recall_at_k(ranked_list, relevant, 1),
        recall_at_5=recall_at_k(ranked_list, relevant, 5),
        mrr=mean_reciprocal_rank(ranked_list, relevant),
    )


def run_frozen_seed_recall(
    *,
    seeds_path: Path | str | None = None,
    kb_root: Path | str | None = None,
    retrieval_profile: str = EVAL_RETRIEVAL_PROFILE,
    top_k: int = DEFAULT_TOP_K,
    vector_enabled: bool = False,
    retrieve_fn: RetrieveFn | None = None,
    dataset: DemoRetrievalSeeds | None = None,
) -> RecallEvalReport:
    """在冻结主集上跑 H1（条款号 Recall@1）与 H2（语义难例 Recall@5/MRR）。

    abstain_conflict 桶不计入 H1/H2（属 H5）。
    """
    root = _project_root()
    path = Path(seeds_path) if seeds_path else default_main_path(root=root)
    seeds = dataset if dataset is not None else load_demo_retrieval_seeds(path)
    kb = Path(kb_root) if kb_root else (root / "knowledge_base")

    retrieve = retrieve_fn or _default_retrieve_fn(
        kb_root=kb,
        retrieval_profile=retrieval_profile,
        top_k=top_k,
        vector_enabled=vector_enabled,
    )

    rows: list[QueryRecallRow] = []
    for q in seeds.queries:
        if q.bucket not in (BUCKET_CLAUSE, BUCKET_SEMANTIC):
            continue
        ranked = list(retrieve(q.query))
        rows.append(_row_for_query(q, ranked=ranked))

    h1_rows = [r for r in rows if r.bucket == BUCKET_CLAUSE]
    h2_rows = [r for r in rows if r.bucket == BUCKET_SEMANTIC]
    h1 = summarize_query_metrics(
        [r.to_dict() for r in h1_rows], recall_key="recall_at_1"
    )
    h2_r = summarize_query_metrics(
        [r.to_dict() for r in h2_rows], recall_key="recall_at_5"
    )
    h2_m = summarize_query_metrics([r.to_dict() for r in h2_rows], mrr_key="mrr")
    gates = evaluate_h1_h2_gates(
        h1_recall_at_1=h1.mean_recall,
        h1_n=h1.n,
        h2_recall_at_5=h2_r.mean_recall,
        h2_mrr=h2_m.mean_mrr,
        h2_n=h2_r.n,
    )
    return RecallEvalReport(
        dataset_id=seeds.dataset_id,
        dataset_version=seeds.version,
        retrieval_profile=retrieval_profile,
        vector_enabled=vector_enabled,
        top_k=top_k,
        queries=rows,
        h1_recall_at_1=h1.mean_recall,
        h1_n=h1.n,
        h2_recall_at_5=h2_r.mean_recall,
        h2_mrr=h2_m.mean_mrr,
        h2_n=h2_r.n,
        gates=gates,
    )


def write_report(report: RecallEvalReport, path: Path | str) -> Path:
    """写出 UTF-8 JSON 报告。"""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return out

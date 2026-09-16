"""在冻结 Demo 检索种子上跑 Recall@K / MRR（票 46 / P-R3 · S2；票 58 / G2 双剖面）。

硬约束：
- 主集仅 artifacts/demo_retrieval_seeds 冻结 JSON；造问增广不得并入计量；
- 并列剖面 demo_seed_eval（向量关）与 pilot_cloud_embed（向量开）；
- 报告必须带剖面标签；禁止无标签短路 1.00 冒充语义满分；
- 产出对照 H1/H2 门槛的机读报告；失败退出码非 0，但不红轨 A。

Rewrote from: REF-CASE-RECALL；REF-CASE-KB（种子边界）
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

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

# 评测剖面名（S2）；非作业默认 clause_v_current
PROFILE_DEMO_SEED_EVAL = "demo_seed_eval"
PROFILE_PILOT_CLOUD_EMBED = "pilot_cloud_embed"
EVAL_RETRIEVAL_PROFILE = PROFILE_DEMO_SEED_EVAL
DEFAULT_TOP_K = 5

RetrieveFn = Callable[[str], Sequence[str]]


class HonestyLabelError(ValueError):
    """验收产物缺少剖面标签或试图用无标签满分冒充语义证明。"""


class MissingVectorSearcherError(RuntimeError):
    """pilot_cloud_embed 需要向量搜索器；禁止关键词静默冒充语义剖面。"""


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
    """冻结集 Recall 评测报告（机读；单剖面）。"""

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
    # 向量腿是否真正绑定搜索器（配置开了但未绑定 → 不得冒充语义满分）
    vector_leg_active: bool = False
    skip_reason: str | None = None
    docs_note: str = (
        "S2/nightly：冻结 Demo 检索种子 Recall@K/MRR；对照 H1/H2；"
        "先剖面后数字；不进默认 pytest 绿 / machine_check"
    )

    @property
    def exit_code(self) -> int:
        if self.skip_reason:
            return 1
        if self.gates is None:
            return 1
        return 0 if self.gates.all_passed else 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "dataset_version": self.dataset_version,
            "retrieval_profile": self.retrieval_profile,
            "vector_enabled": self.vector_enabled,
            "vector_leg_active": self.vector_leg_active,
            "skip_reason": self.skip_reason,
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


@dataclass
class DualRetrievalProfileReport:
    """G2：并列 demo_seed_eval + pilot_cloud_embed 双剖面报告。"""

    demo_seed_eval: RecallEvalReport
    pilot_cloud_embed: RecallEvalReport
    report_kind: str = "dual_retrieval_profile"
    honesty_note: str = (
        "先报剖面再报数字；禁止只用无剖面标签的短路/关键词 1.00 冒充语义满分；"
        "γ 仅当 pilot_cloud_embed 上 H2 失败才允许另议"
    )
    blocks_track_a_gate: bool = False
    gate_role: str = "assist_quality_s2_bypass"
    rewrote_from: str = "REF-CASE-RECALL"

    @property
    def exit_code(self) -> int:
        # 双剖面均过门才 0；任一失败 → 旁路非 0（不红轨 A）
        return 0 if (
            self.demo_seed_eval.exit_code == 0
            and self.pilot_cloud_embed.exit_code == 0
        ) else 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_kind": self.report_kind,
            "honesty_note": self.honesty_note,
            "profiles": {
                PROFILE_DEMO_SEED_EVAL: self.demo_seed_eval.to_dict(),
                PROFILE_PILOT_CLOUD_EMBED: self.pilot_cloud_embed.to_dict(),
            },
            "exit_code": self.exit_code,
            "blocks_track_a_gate": self.blocks_track_a_gate,
            "gate_role": self.gate_role,
            "rewrote_from": self.rewrote_from,
            "gamma_trigger_profile": PROFILE_PILOT_CLOUD_EMBED,
        }


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _looks_like_perfect_score(payload: dict[str, Any]) -> bool:
    """机读：是否呈现「满分」验收外形（H1/H2 近似 1.0）。"""
    h1 = payload.get("h1") or {}
    h2 = payload.get("h2") or {}
    r1 = h1.get("recall_at_1")
    r5 = h2.get("recall_at_5")
    if r1 is None and r5 is None:
        return False
    try:
        perfect_h1 = r1 is not None and float(r1) >= 0.999
        perfect_h2 = r5 is not None and float(r5) >= 0.999
    except (TypeError, ValueError):
        return False
    return bool(perfect_h1 or perfect_h2)


def _reject_degraded_pilot_perfect(section: Mapping[str, Any]) -> None:
    """pilot 剖面：向量未真正激活时禁止满分外形冒充语义。"""
    profile = str(section.get("retrieval_profile") or "").strip()
    if profile != PROFILE_PILOT_CLOUD_EMBED:
        return
    if section.get("skip_reason"):
        return
    if bool(section.get("vector_leg_active")):
        return
    if _looks_like_perfect_score(dict(section)):
        raise HonestyLabelError(
            "禁止 pilot_cloud_embed 在向量腿未激活时用短路/关键词满分冒充语义验收"
        )


def assert_acceptance_report_honest(payload: Mapping[str, Any]) -> None:
    """拒绝无剖面标签的验收产物（尤其是短路满分冒充语义）。

    允许：单剖面目带 retrieval_profile；或 dual_retrieval_profile 分节。
    """
    data = dict(payload)
    kind = data.get("report_kind")
    if kind == "dual_retrieval_profile":
        profiles = data.get("profiles") or {}
        if not isinstance(profiles, dict):
            raise HonestyLabelError("双剖面报告缺少 profiles 分节")
        for name in (PROFILE_DEMO_SEED_EVAL, PROFILE_PILOT_CLOUD_EMBED):
            section = profiles.get(name)
            if not isinstance(section, dict):
                raise HonestyLabelError(f"双剖面报告缺少剖面分节: {name}")
            label = str(section.get("retrieval_profile") or "").strip()
            if label != name:
                raise HonestyLabelError(
                    f"剖面 {name} 的 retrieval_profile 标签缺失或不匹配"
                )
            _reject_degraded_pilot_perfect(section)
        return

    profile = str(data.get("retrieval_profile") or "").strip()
    if not profile:
        if _looks_like_perfect_score(data):
            raise HonestyLabelError(
                "禁止无剖面标签的短路/关键词满分（如 1.00）冒充语义验收；"
                "须标注 retrieval_profile（demo_seed_eval 或 pilot_cloud_embed）"
            )
        raise HonestyLabelError(
            "验收报告缺少 retrieval_profile 剖面标签；先剖面后数字"
        )
    _reject_degraded_pilot_perfect(data)


def _resolve_vector_searcher(vector_searcher: Any | None) -> Any | None:
    """解析向量搜索器；不吞异常伪装成功。"""
    if vector_searcher is not None:
        return vector_searcher
    from missions.track_llm_optional.retrieval import _try_build_vector_searcher

    searcher, _cfg = _try_build_vector_searcher()
    return searcher


def _default_retrieve_fn(
    *,
    kb_root: Path,
    retrieval_profile: str,
    top_k: int,
    vector_enabled: bool,
    vector_searcher: Any | None = None,
) -> RetrieveFn:
    """默认检索：hybrid_retrieve；向量开时须已绑定搜索器。"""
    if vector_enabled and vector_searcher is None:
        raise MissingVectorSearcherError(
            "vector_enabled=true 须绑定向量搜索器；禁止关键词静默冒充语义剖面"
        )
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
            vector_searcher=vector_searcher,
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


def _skipped_pilot_report(
    *,
    seeds: DemoRetrievalSeeds,
    top_k: int,
    reason: str,
) -> RecallEvalReport:
    """无向量搜索器时诚实跳过 pilot，不写关键词满分。"""
    gates = evaluate_h1_h2_gates(
        h1_recall_at_1=0.0,
        h1_n=0,
        h2_recall_at_5=0.0,
        h2_mrr=0.0,
        h2_n=0,
    )
    return RecallEvalReport(
        dataset_id=seeds.dataset_id,
        dataset_version=seeds.version,
        retrieval_profile=PROFILE_PILOT_CLOUD_EMBED,
        vector_enabled=True,
        vector_leg_active=False,
        skip_reason=reason,
        top_k=top_k,
        queries=[],
        h1_recall_at_1=0.0,
        h1_n=0,
        h2_recall_at_5=0.0,
        h2_mrr=0.0,
        h2_n=0,
        gates=gates,
        docs_note=(
            "pilot_cloud_embed 已跳过：缺向量搜索器/索引/embedding Key；"
            "不得用 demo 短路满分冒充本剖面"
        ),
    )


def run_frozen_seed_recall(
    *,
    seeds_path: Path | str | None = None,
    kb_root: Path | str | None = None,
    retrieval_profile: str = EVAL_RETRIEVAL_PROFILE,
    top_k: int = DEFAULT_TOP_K,
    vector_enabled: bool | None = None,
    retrieve_fn: RetrieveFn | None = None,
    vector_searcher: Any | None = None,
    dataset: DemoRetrievalSeeds | None = None,
    allow_missing_vector_skip: bool = False,
) -> RecallEvalReport:
    """在冻结主集上跑 H1（条款号 Recall@1）与 H2（语义难例 Recall@5/MRR）。

    abstain_conflict 桶不计入 H1/H2（属 H5）。
    vector_enabled 默认取 profile 的 eval_vector_enabled。
    """
    from missions.retrieval_profiles import RETRIEVAL_PROFILES

    root = _project_root()
    path = Path(seeds_path) if seeds_path else default_main_path(root=root)
    seeds = dataset if dataset is not None else load_demo_retrieval_seeds(path)
    kb = Path(kb_root) if kb_root else (root / "knowledge_base")

    profile_meta = RETRIEVAL_PROFILES.get(retrieval_profile) or {}
    if vector_enabled is None:
        vector_enabled = bool(profile_meta.get("eval_vector_enabled", False))

    vector_leg_active = False
    searcher = vector_searcher
    if retrieve_fn is None and vector_enabled:
        try:
            searcher = _resolve_vector_searcher(searcher)
        except Exception as exc:
            if allow_missing_vector_skip:
                return _skipped_pilot_report(
                    seeds=seeds,
                    top_k=top_k,
                    reason=f"vector_searcher_error:{type(exc).__name__}",
                )
            raise MissingVectorSearcherError(
                f"无法构建向量搜索器（{type(exc).__name__}）；"
                "禁止关键词静默冒充语义剖面"
            ) from exc
        if searcher is None:
            reason = "missing_vector_searcher_or_index"
            if allow_missing_vector_skip:
                return _skipped_pilot_report(
                    seeds=seeds, top_k=top_k, reason=reason
                )
            raise MissingVectorSearcherError(
                "pilot_cloud_embed / vector_enabled=true 需要已重建索引的向量搜索器；"
                "有 embedding Key 时先 rebuild，再跑本剖面"
            )
        vector_leg_active = True
        retrieve = _default_retrieve_fn(
            kb_root=kb,
            retrieval_profile=retrieval_profile,
            top_k=top_k,
            vector_enabled=True,
            vector_searcher=searcher,
        )
    elif retrieve_fn is not None:
        # 注入检索：调用方自证路径；vector_enabled 时视为腿已激活（单测）
        retrieve = retrieve_fn
        vector_leg_active = bool(vector_enabled)
    else:
        retrieve = _default_retrieve_fn(
            kb_root=kb,
            retrieval_profile=retrieval_profile,
            top_k=top_k,
            vector_enabled=False,
            vector_searcher=None,
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
        vector_enabled=bool(vector_enabled),
        vector_leg_active=vector_leg_active,
        top_k=top_k,
        queries=rows,
        h1_recall_at_1=h1.mean_recall,
        h1_n=h1.n,
        h2_recall_at_5=h2_r.mean_recall,
        h2_mrr=h2_m.mean_mrr,
        h2_n=h2_r.n,
        gates=gates,
    )


def run_dual_retrieval_profiles(
    *,
    seeds_path: Path | str | None = None,
    kb_root: Path | str | None = None,
    top_k: int = DEFAULT_TOP_K,
    dataset: DemoRetrievalSeeds | None = None,
    demo_retrieve_fn: RetrieveFn | None = None,
    pilot_retrieve_fn: RetrieveFn | None = None,
    pilot_vector_searcher: Any | None = None,
) -> DualRetrievalProfileReport:
    """并列跑 demo_seed_eval（向量关）与 pilot_cloud_embed（向量开）。

    缺向量搜索器时 pilot 诚实跳过（不写关键词满分），旁路 exit_code 非 0。
    """
    demo = run_frozen_seed_recall(
        seeds_path=seeds_path,
        kb_root=kb_root,
        retrieval_profile=PROFILE_DEMO_SEED_EVAL,
        top_k=top_k,
        vector_enabled=False,
        retrieve_fn=demo_retrieve_fn,
        dataset=dataset,
    )
    pilot = run_frozen_seed_recall(
        seeds_path=seeds_path,
        kb_root=kb_root,
        retrieval_profile=PROFILE_PILOT_CLOUD_EMBED,
        top_k=top_k,
        vector_enabled=True,
        retrieve_fn=pilot_retrieve_fn,
        vector_searcher=pilot_vector_searcher,
        dataset=dataset,
        allow_missing_vector_skip=pilot_retrieve_fn is None,
    )
    return DualRetrievalProfileReport(
        demo_seed_eval=demo,
        pilot_cloud_embed=pilot,
    )


def write_report(
    report: RecallEvalReport | DualRetrievalProfileReport,
    path: Path | str,
) -> Path:
    """写出 UTF-8 JSON 报告；写出前做剖面诚实校验。"""
    payload = report.to_dict()
    assert_acceptance_report_honest(payload)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return out

"""接缝：冻结集 Recall 评测 runner（票 46 / P-R3）。

S0：runner 外形、可注入检索、报告字段、Rewrote from。
S2（-m assist_quality）：真实冻结集跑通并对齐 H1/H2 门槛。

Rewrote from: REF-CASE-RECALL
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SEEDS = (
    ROOT
    / "artifacts"
    / "demo_retrieval_seeds"
    / "demo_retrieval_seeds.v1.json"
)
KB = ROOT / "knowledge_base"


def test_runner_module_declares_rewrote_from() -> None:
    """handoff：runner 声明 Rewrote from: REF-CASE-RECALL。"""
    text = (SRC / "missions" / "recall_eval_runner.py").read_text(encoding="utf-8")
    assert "Rewrote from" in text
    assert "REF-CASE-RECALL" in text
    assert "S2" in text or "nightly" in text


def test_runner_with_injected_retrieve_builds_gate_report() -> None:
    """接缝：可注入检索函数；报告含 H1/H2 对照与 exit_code。"""
    from missions.demo_retrieval_seeds import load_demo_retrieval_seeds
    from missions.recall_eval_runner import run_frozen_seed_recall

    seeds = load_demo_retrieval_seeds(SEEDS)

    def fake_retrieve(query: str) -> list[str]:
        for q in seeds.queries:
            if q.query == query:
                return list(q.expected.get("relevant_clause_items") or [])
        return []

    report = run_frozen_seed_recall(
        seeds_path=SEEDS,
        dataset=seeds,
        retrieve_fn=fake_retrieve,
    )
    payload = report.to_dict()
    assert payload["blocks_track_a_gate"] is False
    assert payload["h1"]["n"] == 15
    assert payload["h2"]["n"] == 20
    assert payload["h1"]["recall_at_1"] == pytest.approx(1.0)
    assert payload["h2"]["recall_at_5"] == pytest.approx(1.0)
    assert payload["gates"]["h1_passed"] is True
    assert payload["gates"]["h2_passed"] is True
    assert payload["exit_code"] == 0
    # abstain 桶不进 H1/H2 计量
    assert all(q["bucket"] != "abstain_conflict" for q in payload["queries"])


def test_runner_failing_retrieve_sets_nonzero_exit() -> None:
    """接缝：检索全空时门槛失败，exit_code=1，仍不声称阻断轨 A。"""
    from missions.recall_eval_runner import run_frozen_seed_recall

    report = run_frozen_seed_recall(
        seeds_path=SEEDS,
        retrieve_fn=lambda _q: [],
    )
    assert report.gates is not None
    assert report.gates.all_passed is False
    assert report.exit_code == 1
    assert report.blocks_track_a_gate is False


def test_demo_seed_eval_profile_registered() -> None:
    """接缝：S2 评测 profile 覆盖种子文档类型，且非作业默认。"""
    from missions.retrieval_profiles import RETRIEVAL_PROFILES

    profile = RETRIEVAL_PROFILES["demo_seed_eval"]
    types = set(profile["prefer_doc_types"])
    assert {"main_policy", "rider", "endorsement", "handbook"} <= types
    # 默认作业 profile 仍收窄，避免本票改写作业面
    assert "handbook" not in (
        RETRIEVAL_PROFILES["clause_v_current"].get("prefer_doc_types") or []
    )


def test_write_report_utf8_json(tmp_path: Path) -> None:
    """接缝：报告可落盘为 UTF-8 JSON。"""
    from missions.recall_eval_runner import run_frozen_seed_recall, write_report

    report = run_frozen_seed_recall(
        seeds_path=SEEDS,
        retrieve_fn=lambda _q: ["ART-5-EXCL"],
    )
    out = write_report(report, tmp_path / "recall_s2.json")
    raw = out.read_text(encoding="utf-8")
    payload = json.loads(raw)
    assert payload["gate_role"] == "assist_quality_s2_bypass"
    assert "gates" in payload


@pytest.mark.assist_quality
def test_frozen_seed_recall_meets_h1_h2_thresholds() -> None:
    """S2：在冻结 Demo 检索种子上复现 Recall，并对齐 H1/H2 门槛。"""
    from missions.recall_eval_runner import EVAL_RETRIEVAL_PROFILE, run_frozen_seed_recall

    report = run_frozen_seed_recall(
        seeds_path=SEEDS,
        kb_root=KB,
        retrieval_profile=EVAL_RETRIEVAL_PROFILE,
        vector_enabled=False,
        top_k=5,
    )
    assert report.h1_n >= 15
    assert report.h2_n >= 20
    assert report.h1_recall_at_1 >= 0.95
    assert (
        report.h2_recall_at_5 >= 0.70 or report.h2_mrr >= 0.55
    )
    assert report.gates is not None
    assert report.gates.h1_passed is True
    assert report.gates.h2_passed is True
    assert report.exit_code == 0
    assert report.blocks_track_a_gate is False


@pytest.mark.assist_quality
def test_clause_short_circuit_ranks_handbook_and_endorsement_first() -> None:
    """S2：条款号短路时手册/批单精确项须 Rank1（否则 H1 被 profile 类型序淹没）。"""
    from missions.track_llm_optional.hybrid_retrieval import (
        HybridRetrievalConfig,
        hybrid_retrieve,
    )

    cfg = HybridRetrievalConfig(vector_enabled=False)
    for query, want in (
        ("材料受理状态依据 POL-CLAIM-001", "POL-CLAIM-001"),
        ("运动医疗剔除请查条款项: END-1-NARROW", "END-1-NARROW"),
    ):
        citations, portrait = hybrid_retrieve(
            query,
            kb_root=KB,
            retrieval_profile="demo_seed_eval",
            top_k=3,
            cfg=cfg,
            vector_searcher=None,
        )
        assert portrait["clause_short_circuit"] is True
        assert citations[0].get("clause_item") == want

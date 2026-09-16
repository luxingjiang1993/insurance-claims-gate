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


def test_pilot_cloud_embed_profile_registered() -> None:
    """接缝 S2：pilot_cloud_embed 注册为评测剖面（非作业默认）。"""
    from missions.retrieval_profiles import RETRIEVAL_PROFILES

    profile = RETRIEVAL_PROFILES["pilot_cloud_embed"]
    types = set(profile["prefer_doc_types"])
    assert {"main_policy", "rider", "endorsement", "handbook"} <= types
    assert profile.get("eval_vector_enabled") is True
    assert "pilot_cloud_embed" != "clause_v_current"


def test_dual_profile_report_labels_both_sections() -> None:
    """接缝 S2：双剖面报告含 demo_seed_eval 与 pilot_cloud_embed 分节标签。"""
    from missions.demo_retrieval_seeds import load_demo_retrieval_seeds
    from missions.recall_eval_runner import (
        PROFILE_DEMO_SEED_EVAL,
        PROFILE_PILOT_CLOUD_EMBED,
        run_dual_retrieval_profiles,
    )

    seeds = load_demo_retrieval_seeds(SEEDS)

    def fake_retrieve(query: str) -> list[str]:
        for q in seeds.queries:
            if q.query == query:
                return list(q.expected.get("relevant_clause_items") or [])
        return []

    dual = run_dual_retrieval_profiles(
        seeds_path=SEEDS,
        dataset=seeds,
        demo_retrieve_fn=fake_retrieve,
        pilot_retrieve_fn=fake_retrieve,
    )
    payload = dual.to_dict()
    assert payload["report_kind"] == "dual_retrieval_profile"
    profiles = payload["profiles"]
    assert PROFILE_DEMO_SEED_EVAL in profiles
    assert PROFILE_PILOT_CLOUD_EMBED in profiles
    demo = profiles[PROFILE_DEMO_SEED_EVAL]
    pilot = profiles[PROFILE_PILOT_CLOUD_EMBED]
    assert demo["retrieval_profile"] == PROFILE_DEMO_SEED_EVAL
    assert demo["vector_enabled"] is False
    assert pilot["retrieval_profile"] == PROFILE_PILOT_CLOUD_EMBED
    assert pilot["vector_enabled"] is True
    assert pilot["vector_leg_active"] is True
    # 门槛语义继承；数字可低于 1.0（本注入路径碰巧满分，但须带剖面名）
    assert "gates" in demo and "gates" in pilot
    assert dual.exit_code == 0


def test_reject_unlabeled_short_circuit_perfect_score_as_acceptance() -> None:
    """接缝 S2：禁止无剖面标签的短路 1.00 冒充语义满分验收。"""
    from missions.recall_eval_runner import (
        HonestyLabelError,
        assert_acceptance_report_honest,
    )

    unlabeled = {
        "h1": {"n": 15, "recall_at_1": 1.0},
        "h2": {"n": 20, "recall_at_5": 1.0, "mrr": 0.9},
        "gates": {"h1_passed": True, "h2_passed": True, "all_passed": True},
    }
    with pytest.raises(HonestyLabelError, match="剖面|profile"):
        assert_acceptance_report_honest(unlabeled)

    labeled_demo = {
        "retrieval_profile": "demo_seed_eval",
        "vector_enabled": False,
        "h1": {"n": 15, "recall_at_1": 1.0},
        "h2": {"n": 20, "recall_at_5": 1.0, "mrr": 0.9},
        "gates": {"h1_passed": True, "h2_passed": True, "all_passed": True},
    }
    # 单剖面 demo 可过机读校验，但不得被当作唯一语义满分
    assert_acceptance_report_honest(labeled_demo)

    degraded_pilot_perfect = {
        "retrieval_profile": "pilot_cloud_embed",
        "vector_enabled": True,
        "vector_leg_active": False,
        "h1": {"n": 15, "recall_at_1": 1.0},
        "h2": {"n": 20, "recall_at_5": 1.0},
    }
    with pytest.raises(HonestyLabelError, match="向量腿未激活|冒充语义"):
        assert_acceptance_report_honest(degraded_pilot_perfect)

    dual_ok = {
        "report_kind": "dual_retrieval_profile",
        "profiles": {
            "demo_seed_eval": {
                "retrieval_profile": "demo_seed_eval",
                "vector_enabled": False,
                "h1": {"recall_at_1": 1.0},
            },
            "pilot_cloud_embed": {
                "retrieval_profile": "pilot_cloud_embed",
                "vector_enabled": True,
                "vector_leg_active": True,
                "h1": {"recall_at_1": 0.8},
            },
        },
    }
    assert_acceptance_report_honest(dual_ok)


def test_pilot_cloud_embed_path_runs_with_vector_searcher() -> None:
    """接缝 S2：pilot_cloud_embed 在注入向量搜索器时 vector_enabled=true 可跑。"""
    from missions.demo_retrieval_seeds import load_demo_retrieval_seeds
    from missions.recall_eval_runner import (
        PROFILE_PILOT_CLOUD_EMBED,
        run_frozen_seed_recall,
    )

    seeds = load_demo_retrieval_seeds(SEEDS)
    calls: list[str] = []

    class FakeVectorSearcher:
        def search(self, query: str, *, top_k: int, where=None):  # noqa: ANN001
            calls.append(query)
            # 返回空命中；hybrid 仍可走关键词腿，本测只证向量路径被打开
            return []

    report = run_frozen_seed_recall(
        seeds_path=SEEDS,
        dataset=seeds,
        kb_root=KB,
        retrieval_profile=PROFILE_PILOT_CLOUD_EMBED,
        vector_enabled=True,
        vector_searcher=FakeVectorSearcher(),
        top_k=5,
    )
    assert report.retrieval_profile == PROFILE_PILOT_CLOUD_EMBED
    assert report.vector_enabled is True
    assert report.vector_leg_active is True
    assert report.skip_reason is None
    assert len(calls) >= 1
    assert report.blocks_track_a_gate is False


def test_pilot_without_vector_searcher_skips_honestly_in_dual(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """接缝 S2：缺向量搜索器时 dual 中 pilot 诚实跳过，不写满分。"""
    from missions.demo_retrieval_seeds import load_demo_retrieval_seeds
    from missions import recall_eval_runner as runner

    seeds = load_demo_retrieval_seeds(SEEDS)

    def fake_demo(query: str) -> list[str]:
        for q in seeds.queries:
            if q.query == query:
                return list(q.expected.get("relevant_clause_items") or [])
        return []

    monkeypatch.setattr(
        runner, "_resolve_vector_searcher", lambda _s: None
    )

    dual = runner.run_dual_retrieval_profiles(
        seeds_path=SEEDS,
        dataset=seeds,
        demo_retrieve_fn=fake_demo,
        pilot_retrieve_fn=None,
        pilot_vector_searcher=None,
    )
    pilot = dual.pilot_cloud_embed
    assert pilot.retrieval_profile == runner.PROFILE_PILOT_CLOUD_EMBED
    assert pilot.vector_enabled is True
    assert pilot.vector_leg_active is False
    assert pilot.skip_reason
    assert pilot.h1_recall_at_1 == 0.0
    assert dual.exit_code == 1
    runner.write_report(dual, tmp_path / "dual_skip.json")

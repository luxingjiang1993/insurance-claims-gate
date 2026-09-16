"""接缝：三维 S2 质量旁路（票 47 / P-E2）。

S0：编排外形、LLM 非唯一主指标、不阻断轨 A、Rewrote from。
S2（-m assist_quality）：三维拉通并对齐门槛。

Rewrote from: REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR
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
FAITH = ROOT / "artifacts" / "citation_faithfulness" / "fixtures.v1.json"
USABLE = ROOT / "artifacts" / "suggestion_usability" / "fixtures.v1.json"
KB = ROOT / "knowledge_base"


def test_three_dim_module_declares_rewrote_from() -> None:
    """handoff：三维门声明 Rewrote from。"""
    text = (SRC / "missions" / "three_dim_s2_quality.py").read_text(encoding="utf-8")
    assert "Rewrote from" in text
    assert "REF-CASE-OPENEVALS" in text
    assert "REF-CASE-EVAL-ADVISOR" in text
    assert "llm" in text.lower()


def test_orchestrator_with_injected_dims_never_llm_primary() -> None:
    """接缝：三维拉通报告；主指标非 LLM；不阻断轨 A。"""
    from missions.three_dim_s2_quality import run_three_dim_s2

    report = run_three_dim_s2(
        seeds_path=SEEDS,
        faithfulness_fixtures_path=FAITH,
        usability_fixtures_path=USABLE,
        retrieve_fn=lambda _q: ["ART-5-EXCL"],
        run_retrieval=True,
        run_faithfulness=True,
        run_usability=True,
    )
    payload = report.to_dict()
    assert payload["blocks_track_a_gate"] is False
    assert payload["llm_judge_as_primary"] is False
    assert payload["gate_role"] == "assist_quality_s2_bypass"
    assert set(payload["dimensions"].keys()) == {
        "retrieval",
        "citation_faithfulness",
        "suggestion_usability",
    }
    # 各维主指标不得以 LLM 为唯一
    for dim in payload["dimensions"].values():
        assert dim.get("llm_judge_as_primary") is False
        primary = dim.get("primary_metric") or ""
        assert "llm" not in primary.lower() or "rules" in primary.lower() or "human" in primary.lower()


def test_overall_fail_when_any_dim_fails() -> None:
    """接缝：任一维失败 → exit_code 非 0，仍不红轨 A。"""
    from missions.three_dim_s2_quality import run_three_dim_s2

    report = run_three_dim_s2(
        seeds_path=SEEDS,
        faithfulness_fixtures_path=FAITH,
        usability_fixtures_path=USABLE,
        retrieve_fn=lambda _q: [],  # 检索全空 → H1/H2 失败
    )
    assert report.exit_code != 0
    assert report.blocks_track_a_gate is False
    assert report.all_passed is False


def test_write_three_dim_report_utf8(tmp_path: Path) -> None:
    """接缝：三维报告可落盘 UTF-8 JSON。"""
    from missions.three_dim_s2_quality import run_three_dim_s2, write_report

    report = run_three_dim_s2(
        seeds_path=SEEDS,
        faithfulness_fixtures_path=FAITH,
        usability_fixtures_path=USABLE,
        retrieve_fn=lambda _q: ["ART-2-COVER"],
    )
    out = write_report(report, tmp_path / "three_dim_s2.json")
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "dimensions" in payload
    assert payload["rewrote_from"]


@pytest.mark.assist_quality
def test_three_dim_s2_real_run_passes_gates() -> None:
    """S2：冻结集检索 + 忠实夹具 + 可用性夹具可跑且过门。"""
    from missions.three_dim_s2_quality import run_three_dim_s2

    report = run_three_dim_s2(
        seeds_path=SEEDS,
        kb_root=KB,
        faithfulness_fixtures_path=FAITH,
        usability_fixtures_path=USABLE,
        vector_enabled=False,
    )
    assert report.dimensions["retrieval"]["passed"] is True
    assert report.dimensions["citation_faithfulness"]["passed"] is True
    assert report.dimensions["suggestion_usability"]["passed"] is True
    assert report.llm_judge_as_primary is False
    assert report.all_passed is True
    assert report.exit_code == 0
    assert report.blocks_track_a_gate is False

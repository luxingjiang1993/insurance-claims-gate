"""轨 B 最小检索→辅助起草：仅 -m track_llm_optional 运行。

完整方差预算 / 金标门槛数值化仍属 P2-4；本票只验最小可跑。
Rewrote from: REF-RAG-CY, REF-MISSIONS, REF-CASE-HYBRID
"""

from __future__ import annotations

from pathlib import Path

import pytest

from missions.track_llm_optional.pipeline import draft_assist

pytestmark = pytest.mark.track_llm_optional

ROOT = Path(__file__).resolve().parents[2]
KB_ROOT = ROOT / "knowledge_base"


def test_draft_assist_returns_llm_optional_track_with_citations() -> None:
    """正向：无 LLM 时确定性假检索可跑通，产物标注 inference_track=llm_optional。"""
    result = draft_assist(
        query="疾病导致的摔伤是否属于责任免除",
        kb_root=KB_ROOT,
        retrieval_profile="clause_v_current",
        enable_llm=False,
    )
    assert result.inference_track == "llm_optional"
    assert result.used_llm is False
    assert result.retrieval_profile == "clause_v_current"
    assert len(result.citations) >= 1
    assert result.draft_text.strip()
    # 引用须可回溯到 KB 字段外形
    top = result.citations[0]
    assert top.get("doc_id")
    assert top.get("clause_item")


def test_rules_vs_rag_conflict_fail_closed_to_latch() -> None:
    """规则结论与 RAG 辅助结论冲突时 fail-closed 进人闸，不静默采信。"""
    result = draft_assist(
        query="疾病摔伤除外责任",
        kb_root=KB_ROOT,
        retrieval_profile="clause_v_current",
        rules_conclusion="pay",
        enable_llm=False,
    )
    assert result.inference_track == "llm_optional"
    assert result.human_latch_required is True
    assert result.conflict_route_id == "R-CONFLICT-RULES-RAG"


def test_handbook_ops_cannot_alone_support_external_deny() -> None:
    """handbook_ops 不得单独支撑对外拒赔（无论是否显式传入 intended_external_action）。"""
    # 显式拒赔意图
    with_intent = draft_assist(
        query="作业手册拒赔指引",
        kb_root=KB_ROOT,
        retrieval_profile="handbook_ops",
        intended_external_action="deny",
        enable_llm=False,
    )
    assert with_intent.inference_track == "llm_optional"
    assert with_intent.can_external_deny is False
    assert with_intent.human_latch_required is True

    # 未传 intended_external_action 时，handbook_ops 仍不可独撑对外拒赔
    bare = draft_assist(
        query="作业手册拒赔指引",
        kb_root=KB_ROOT,
        retrieval_profile="handbook_ops",
        enable_llm=False,
    )
    assert bare.can_external_deny is False


def test_endorsement_priority_profile_preserved() -> None:
    """轨 B 不得破坏 endorsement_priority 语义：批单类优先出现。"""
    result = draft_assist(
        query="免赔额批单覆盖主险",
        kb_root=KB_ROOT,
        retrieval_profile="endorsement_priority",
        enable_llm=False,
    )
    assert result.inference_track == "llm_optional"
    assert result.retrieval_profile == "endorsement_priority"
    assert len(result.citations) >= 1
    # 首条应为批单或特约（与轨 A RETRIEVAL_PROFILES endorsement_first 一致）
    first_doc = str(result.citations[0].get("doc_id") or "")
    assert "END" in first_doc.upper() or result.citations[0].get("doc_type") in {
        "endorsement",
        "special_agreement",
    }

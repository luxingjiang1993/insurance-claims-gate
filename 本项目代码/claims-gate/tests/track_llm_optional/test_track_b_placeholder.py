"""轨 B 隔离占位：仅在显式 -m track_llm_optional 时运行。

本期不交付完整 RAG/LLM 质量门；本文件失败不得进入默认 CI。
Rewrote from: REF-CASE-HYBRID, REF-MISSIONS
"""

from __future__ import annotations

import pytest

from missions.track_llm_optional.config import TrackBConfig

pytestmark = pytest.mark.track_llm_optional


def test_track_b_placeholder_config_isolated() -> None:
    """占位：轨 B 配置与轨 A 人闸策略槽位独立，不并入默认绿门。"""
    cfg = TrackBConfig()
    assert cfg.inference_track == "llm_optional"
    assert cfg.blocks_track_a_gate is False
    # 独立人闸/方差槽位存在即可；完整质量门属 P2
    assert cfg.latch_policy_profile == "llm_optional_independent"
    assert cfg.variance_budget_profile == "llm_optional_variance"

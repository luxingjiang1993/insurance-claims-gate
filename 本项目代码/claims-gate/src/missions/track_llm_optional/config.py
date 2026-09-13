"""轨 B（llm_optional）隔离配置占位。

方差、重试与人闸策略独立于轨 A；失败不得阻断轨 A 合门禁。
本期不交付完整 RAG/LLM 质量门。

Rewrote from: REF-CASE-HYBRID, REF-MISSIONS
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrackBConfig:
    """轨 B 独立槽位；默认 CI / Demo 禁止依赖本配置才能绿。"""

    inference_track: str = "llm_optional"
    # 轨 B 失败是否阻断轨 A 合门禁（必须为 False）
    blocks_track_a_gate: bool = False
    # 默认 CI 是否允许以调用 LLM 作为 SC 通过条件（必须为 False）
    default_ci_requires_llm: bool = False
    # 独立人闸策略画像（与轨 A latch_matrix 表隔离）
    latch_policy_profile: str = "llm_optional_independent"
    # 独立方差/重试预算画像
    variance_budget_profile: str = "llm_optional_variance"

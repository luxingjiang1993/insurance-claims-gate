"""Missions 角色检索画像与可配置模型名（轻量 A4 / Q-A6）。

Validator 与 Worker 必须可区分；真多模型调用不进默认 S0。
Rewrote from: REF-MISSIONS
"""

from __future__ import annotations

# 检索 profile：与 RAG / handoff 事件字段对齐
WORKER_RETRIEVE_PROFILE = "worker_narrow_top3"
VALIDATOR_RETRIEVE_PROFILE = "validator_skeptical_top5"

# 可配置独立模型名（S0 仅配置位可区分；不触发真 LLM）
WORKER_MODEL_NAME = "worker-impl-s0"
VALIDATOR_MODEL_NAME = "validator-judge-s0"

"""Assist 编排步数预算≤4：retrieve→gate→draft→self-check。

架构声明：编排由 app 拥有（app-owned）。实现上可用图库（含 LangGraph）
作本地状态机，但口头与架构不得售卖 LangGraph / 第二套 Agent 平台；
合门禁与权威仍归轨 A + 人闸。

观测 span 树（retrieve→fuse→gate→llm→…）可更细；本模块约束的是编排预算外形。

Rewrote from: REF-CASE-DELIBERATIVE
"""

from __future__ import annotations

from typing import Any

ASSIST_STEP_BUDGET = 4
ASSIST_ORCHESTRATION_STEPS: tuple[str, ...] = (
    "retrieve",
    "gate",
    "draft",
    "self-check",
)
ASSIST_ORCHESTRATION_OWNER = "app-owned"
REWROTE_FROM = "REF-CASE-DELIBERATIVE"


class AssistStepBudgetError(ValueError):
    """assist 编排步数 / 步序违规（P-A4）。"""


class AssistStepBudget:
    """可强制、可测的 assist 四步预算记账器。"""

    def __init__(self) -> None:
        self._steps: list[str] = []

    @property
    def steps(self) -> tuple[str, ...]:
        return tuple(self._steps)

    def record(self, step: str) -> None:
        """按固定顺序记录一步；未知 / 乱序 / 超预算一律拒绝。"""
        if step not in ASSIST_ORCHESTRATION_STEPS:
            raise AssistStepBudgetError(f"未知编排步: {step}")
        if len(self._steps) >= ASSIST_STEP_BUDGET:
            raise AssistStepBudgetError(
                f"超出步数预算 {ASSIST_STEP_BUDGET}（已记录 {list(self._steps)}）"
            )
        expected = ASSIST_ORCHESTRATION_STEPS[len(self._steps)]
        if step != expected:
            raise AssistStepBudgetError(
                f"步序错误: 期望 {expected}，得到 {step}"
            )
        self._steps.append(step)

    def assert_complete(self) -> None:
        """未跑满四步不得宣称编排完成。"""
        if tuple(self._steps) != ASSIST_ORCHESTRATION_STEPS:
            raise AssistStepBudgetError(
                f"编排未完成: 已记录 {list(self._steps)}，"
                f"期望 {list(ASSIST_ORCHESTRATION_STEPS)}"
            )

    def to_dict(self) -> dict[str, Any]:
        """可机读步迹（供 assist 响应 / 验收）。"""
        return {
            "orchestration_steps": list(self._steps),
            "orchestration_step_budget": ASSIST_STEP_BUDGET,
            "orchestration_owner": ASSIST_ORCHESTRATION_OWNER,
            "rewrote_from": REWROTE_FROM,
        }

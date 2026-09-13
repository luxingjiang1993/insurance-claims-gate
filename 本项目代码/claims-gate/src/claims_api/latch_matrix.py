"""人闸权限矩阵：金额档 × 决定类型 × 敏感上浮（PRD §7 试点默认）。

Rewrote from: REF-MISSIONS（transfer_api/limits.py 表驱动 + error_code 模式换域；
阈值取自 PRD §7，不照搬转账限额数字）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

# 金额档边界（人民币元，单次案件建议赔付额）— PRD §7.2
TIER_A_MAX = 10_000
TIER_B_MAX = 50_000
TIER_C_MAX = 200_000

TIER_ORDER: tuple[str, ...] = ("A", "B", "C", "D")

# 敏感场景：至少上浮一档（PRD §7.3）
SENSITIVITY_FLAGS: frozenset[str] = frozenset(
    {
        "litigation",  # 诉讼
        "petition",  # 信访
        "media",  # 媒体
        "health_sensitive",  # 健康敏感病历争议
        "first_large_loss",  # 首次大额出险
        "exgratia",  # 通融（决定类型本身也上浮）
        "reject",  # 拒赔
    }
)

# 默认必闸的决定类型（PRD §7.1）
ALWAYS_LATCH_DECISIONS: frozenset[str] = frozenset(
    {
        "reject_draft",
        "exgratia",
        "prepay",
        "investigating",  # 解除冻决须闸；进入自动冻决
        "unfreeze",
    }
)


@dataclass(frozen=True)
class LatchRequirement:
    """人闸矩阵计算结果（外部可观察字段）。"""

    amount_tier: str
    latch_tier: str
    human_latch_required: bool
    dual_token_required: bool
    latch_level_label: str
    recommended_payout_amount: int


_LATCH_LABELS: dict[str, str] = {
    "A": "双人机审抽检/直通草案",
    "B": "作业中心主管闸",
    "C": "省级核赔负责人闸",
    "D": "总公司授权闸",
}


def latch_level_label(decision_type: str, latch_tier: str) -> str:
    """按决定类型校正档位文案（减赔 A 起即为主管闸）。"""
    if decision_type == "reduce" and latch_tier == "A":
        return "主管闸"
    if decision_type in ("exgratia", "prepay", "reject_draft", "investigating", "unfreeze"):
        if latch_tier == "A":
            return "主管闸"
    return _LATCH_LABELS[latch_tier]


def amount_tier(amount: int) -> str:
    """按建议赔付额映射 A/B/C/D。"""
    if amount < 0:
        raise ValueError("建议赔付额不得为负")
    if amount <= TIER_A_MAX:
        return "A"
    if amount <= TIER_B_MAX:
        return "B"
    if amount <= TIER_C_MAX:
        return "C"
    return "D"


def uplift_tier(tier: str, steps: int = 1) -> tuple[str, bool]:
    """上浮档位；已在 D 则保持 D 并要求双人令牌。"""
    if tier not in TIER_ORDER:
        raise ValueError(f"未知金额档: {tier}")
    if steps <= 0:
        return tier, False
    idx = TIER_ORDER.index(tier)
    new_idx = idx + steps
    if new_idx >= len(TIER_ORDER):
        return "D", True
    return TIER_ORDER[new_idx], False


def _has_sensitivity(flags: Iterable[str] | None) -> bool:
    if not flags:
        return False
    return any(f in SENSITIVITY_FLAGS for f in flags)


def resolve_latch(
    decision_type: str,
    recommended_payout_amount: int,
    *,
    sensitivity_flags: Iterable[str] | None = None,
) -> LatchRequirement:
    """决定类型 × 金额档 × 敏感上浮 → 是否人闸。

    规则摘要（PRD §7）：
    - 补件：不闸
    - 通赔建议：A 可直通草案；B+ 必闸；敏感上浮后按 latch_tier
    - 减赔：A 起即主管闸（必闸）；争议/敏感上浮一档
    - 拒赔/通融/预赔/解除冻决：必闸
    - 通融/拒赔标志本身计入敏感上浮
    """
    base_tier = amount_tier(recommended_payout_amount)
    flags = list(sensitivity_flags or [])
    # 通融/拒赔决定类型强制带敏感上浮语义
    if decision_type == "exgratia" and "exgratia" not in flags:
        flags.append("exgratia")
    if decision_type == "reject_draft" and "reject" not in flags:
        flags.append("reject")

    dual = False
    latch_tier = base_tier
    if _has_sensitivity(flags):
        latch_tier, dual = uplift_tier(base_tier, 1)

    if decision_type == "supplement":
        required = False
    elif decision_type in ALWAYS_LATCH_DECISIONS:
        required = True
    elif decision_type == "approve_recommend":
        # A 直通草案；上浮后或 B+ 必闸
        required = latch_tier != "A"
    elif decision_type == "reduce":
        # 减赔：A 档即为主管闸
        required = True
    else:
        # 未知类型失败关闭：默认必闸
        required = True

    return LatchRequirement(
        amount_tier=base_tier,
        latch_tier=latch_tier,
        human_latch_required=required,
        dual_token_required=dual,
        latch_level_label=latch_level_label(decision_type, latch_tier),
        recommended_payout_amount=recommended_payout_amount,
    )


def is_fake_exgratia_clause_approve_citation(citation: dict) -> bool:
    """通融不得伪装成「主险条款通赔」citation（PRD §7.4）。"""
    quote = str(citation.get("quote") or "")
    clause_item = str(citation.get("clause_item") or "")
    doc_id = str(citation.get("doc_id") or "")
    semantic = str(citation.get("semantic") or citation.get("role") or "")
    if "主险条款通赔" in quote or "条款通赔" in quote:
        return True
    if semantic in ("clause_approve", "main_policy_approve", "通赔"):
        return True
    # 主险责任条款被标成通赔依据
    if doc_id.startswith("PA-ACC-MAIN") and (
        "COV" in clause_item.upper() or "责任" in quote
    ):
        if citation.get("as_clause_approve") is True:
            return True
        if "通赔" in quote and "通融" not in quote:
            return True
    return False

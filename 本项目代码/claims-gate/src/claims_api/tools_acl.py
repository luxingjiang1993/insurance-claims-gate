"""工具 ACL：支付类工具默认无权限（威胁模型最小落地）。

Rewrote from: REF-MISSIONS（工具 ACL 外形）
"""

from __future__ import annotations

# 支付 / 银企类工具名：默认一律拒绝
PAYMENT_TOOL_NAMES: frozenset[str] = frozenset(
    {
        "bank_payout_transfer",
        "silver_enterprise_direct_pay",
        "auto_payout",
        "l3_payment_adapter",
    }
)

# 脚手架允许的只读/领域工具（无支付）
ALLOWED_TOOL_NAMES: frozenset[str] = frozenset(
    {
        "read_claim_header",
        "list_gate_status",
        "validate_citation",
        "evaluate_claim",
        "read_decision",
        "register_materials",
        "notify_supplement",
        "export_document",
        "approve_human_latch",
        "reject_human_latch",
        "decide_exgratia",
        "decide_prepay",
        "investigate_enter",
        "investigate_unfreeze",
        "peak_degrade",
        "read_ledger",
    }
)


class ToolPermissionError(PermissionError):
    """工具 ACL 拒绝。"""


def assert_tool_allowed(tool_name: str) -> None:
    """支付类默认无权限；仅白名单工具可通过。"""
    if tool_name in PAYMENT_TOOL_NAMES:
        raise ToolPermissionError(f"支付类工具默认无权限: {tool_name}")
    if tool_name not in ALLOWED_TOOL_NAMES:
        raise ToolPermissionError(f"未授权工具: {tool_name}")

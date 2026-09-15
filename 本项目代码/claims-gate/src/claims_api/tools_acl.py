"""工具 ACL：支付类默认无权限；演示 RBAC 角色差。

Rewrote from: REF-MISSIONS（工具 ACL 外形 + 权限拒绝）
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
        "l2_payout_ready",
        "l2_close",
        "auth_login",
        "auth_me",
        "auth_logout",
        "read_latch_events",
        "assist_claim",
        "adopt_assist",
        "create_eval_run",
        "list_eval_runs",
    }
)

# 对外通知 / 出款就绪类人闸：仅 supervisor
SUPERVISOR_ONLY_TOOLS: frozenset[str] = frozenset(
    {
        "approve_human_latch",
        "reject_human_latch",
    }
)

# viewer 只读（含登录会话自检）
VIEWER_ALLOWED_TOOLS: frozenset[str] = frozenset(
    {
        "read_claim_header",
        "list_gate_status",
        "validate_citation",
        "read_decision",
        "read_ledger",
        "read_latch_events",
        "auth_login",
        "auth_me",
        "auth_logout",
        "list_eval_runs",
    }
)


class ToolPermissionError(PermissionError):
    """工具 ACL 拒绝。"""


class RolePermissionError(PermissionError):
    """角色 RBAC 拒绝。"""

    def __init__(self, message: str, *, missing_auth: bool = False) -> None:
        super().__init__(message)
        self.missing_auth = missing_auth


def assert_tool_allowed(tool_name: str) -> None:
    """支付类默认无权限；仅白名单工具可通过。"""
    if tool_name in PAYMENT_TOOL_NAMES:
        raise ToolPermissionError(f"支付类工具默认无权限: {tool_name}")
    if tool_name not in ALLOWED_TOOL_NAMES:
        raise ToolPermissionError(f"未授权工具: {tool_name}")


def assert_role_allowed(tool_name: str, role: str | None) -> None:
    """按会话角色硬门：人闸仅 supervisor；viewer 只读。

    role=None 表示无会话：除人闸外保持轨 A 匿名机检可用。
    """
    if tool_name in SUPERVISOR_ONLY_TOOLS:
        if role is None:
            raise RolePermissionError(
                "人闸须主管登录会话",
                missing_auth=True,
            )
        if role != "supervisor":
            raise RolePermissionError(f"仅 supervisor 可执行人闸: {tool_name}")
        return
    if role == "viewer" and tool_name not in VIEWER_ALLOWED_TOOLS:
        raise RolePermissionError(f"viewer 只读，拒绝写操作: {tool_name}")

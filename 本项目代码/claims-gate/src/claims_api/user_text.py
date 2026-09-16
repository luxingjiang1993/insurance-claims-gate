"""用户可控文本（OCR / 客户备注）吸收：可观察收纳，永不改写人闸规则。

Rewrote from: REF-MISSIONS（transfer 用户字段不得改限额）；REF-CASE-HYBRID
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models_domain import ClaimCase


def absorb_user_controlled_text(
    case: "ClaimCase",
    *,
    ocr_text: str | None = None,
    customer_remark: str | None = None,
) -> None:
    """将 OCR/备注写入案件可观察字段（首尾空白 strip；全空白→空串）。

    硬约束：不得从这些文本解析或改写 human_latch_required、payout_ready、
    sensitivity_flags、金额档或任何人闸矩阵输入。
    """
    # F-Q-DEMO-01：写入前 strip；全空白 → 空串；不改人闸/payout 字段
    if ocr_text is not None:
        case.ocr_text = str(ocr_text).strip()
    if customer_remark is not None:
        case.customer_remark = str(customer_remark).strip()

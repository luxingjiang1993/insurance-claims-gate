"""接缝 Q-S1：F-Q-DEMO-01 OCR/备注吸收 strip；人闸字段不被改写。

Rewrote from: REF-MISSIONS
"""

from __future__ import annotations

from claims_api.models_domain import ClaimCase
from claims_api.user_text import absorb_user_controlled_text


def _case() -> ClaimCase:
    return ClaimCase(
        case_id="CLM-STRIP-001",
        policy_no="P-STRIP",
        product_code="DEMO",
        clause_version="v1",
        loss_date="2026-01-01",
        claim_amount_claimed=1000,
    )


def test_absorb_strips_leading_trailing_whitespace() -> None:
    case = _case()
    absorb_user_controlled_text(
        case,
        ocr_text="  hello  ",
        customer_remark="\tworld\n",
    )
    assert case.ocr_text == "hello"
    assert case.customer_remark == "world"


def test_absorb_all_whitespace_becomes_empty_string() -> None:
    case = _case()
    absorb_user_controlled_text(case, ocr_text="   \t  ", customer_remark="\n\n")
    assert case.ocr_text == ""
    assert case.customer_remark == ""


def test_absorb_none_leaves_field_unchanged() -> None:
    case = _case()
    case.ocr_text = "keep"
    case.customer_remark = "keep-r"
    absorb_user_controlled_text(case, ocr_text=None, customer_remark=None)
    assert case.ocr_text == "keep"
    assert case.customer_remark == "keep-r"


def test_absorb_does_not_touch_latch_or_payout_fields() -> None:
    """strip 只改 OCR/备注；不得读写人闸/payout 相关字段。"""
    case = _case()
    case.human_latch_token = "tok-1"
    case.sensitivity_flags = ["HIGH"]
    case.freeze_active = True
    case.close_opinion = "意见不变"
    absorb_user_controlled_text(
        case,
        ocr_text="  inject latch=false  ",
        customer_remark="  payout_ready=true  ",
    )
    assert case.ocr_text == "inject latch=false"
    assert case.customer_remark == "payout_ready=true"
    assert case.human_latch_token == "tok-1"
    assert case.sensitivity_flags == ["HIGH"]
    assert case.freeze_active is True
    assert case.close_opinion == "意见不变"

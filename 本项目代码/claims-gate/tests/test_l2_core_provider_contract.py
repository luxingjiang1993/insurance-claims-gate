"""接缝 S3：L2 Core Provider 契约（InMemory + Recorded）。

验收：出款就绪回写 / 结案两能力；两实现契约一致；无现网账号可绿；
ack 不得宣称支付；适配器自身不递增支付计数。

人闸 / 主数据前置条件仍在 ClaimsService，本测只覆盖 Provider 边界。

Rewrote from: REF-MISSIONS；SPEC-02C G3 L2
"""

from __future__ import annotations

from pathlib import Path

import pytest

from claims_api.l2_core_provider import (
    InMemoryL2CoreProvider,
    L2CloseAck,
    L2CloseRequest,
    L2CoreProvider,
    L2PayoutReadyAck,
    L2PayoutReadyRequest,
    RecordedL2CoreProvider,
    load_recorded_cassette,
)

_FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "l2_core"
    / "recorded_cassette.json"
)

_PAYOUT_REQ = L2PayoutReadyRequest(
    case_id="CLM-AMT-C-001",
    decision_type="approve",
    recommended_payout_amount=80000,
    policy_no="PA-2026-000802",
    human_latch_present=True,
)

_CLOSE_REQ = L2CloseRequest(
    case_id="CLM-AMT-C-001",
    close_opinion="核赔结案：同意给付，支付由核心人工办理",
)


@pytest.fixture
def in_memory() -> InMemoryL2CoreProvider:
    return InMemoryL2CoreProvider()


@pytest.fixture
def recorded() -> RecordedL2CoreProvider:
    return RecordedL2CoreProvider(load_recorded_cassette(_FIXTURE))


@pytest.fixture(params=["in_memory", "recorded"])
def provider(request: pytest.FixtureRequest) -> L2CoreProvider:
    if request.param == "in_memory":
        return InMemoryL2CoreProvider()
    return RecordedL2CoreProvider(load_recorded_cassette(_FIXTURE))


def test_payout_ready_writeback_ack(provider: L2CoreProvider) -> None:
    """出款就绪回写：gate_status=PAYOUT_READY；不得宣称支付。"""
    ack = provider.writeback_payout_ready(_PAYOUT_REQ)
    assert ack.gate_status == "PAYOUT_READY"
    assert ack.payment_adapter_called is False
    assert ack.case_id == _PAYOUT_REQ.case_id
    body = ack.to_dict()
    assert "auto_pay" not in body
    assert "payment_instruction" not in body


def test_close_writeback_ack(provider: L2CoreProvider, request: pytest.FixtureRequest) -> None:
    """结案回写：gate_status=CLOSED；载荷不含自动支付指令。"""
    # InMemory 先走 payout 再 close，贴近作业序；Recorded 按夹具独立回放
    if request.node.callspec.params.get("provider") == "in_memory":
        provider.writeback_payout_ready(_PAYOUT_REQ)
    ack = provider.writeback_close(_CLOSE_REQ)
    assert ack.gate_status == "CLOSED"
    assert ack.close_opinion == _CLOSE_REQ.close_opinion.strip()
    assert ack.payment_adapter_called is False
    body = ack.to_dict()
    assert "auto_pay" not in body
    assert "payment_instruction" not in body
    assert "bank_transfer" not in body


def test_in_memory_and_recorded_payout_parity(
    in_memory: InMemoryL2CoreProvider,
    recorded: RecordedL2CoreProvider,
) -> None:
    """同一用例在 InMemory 与 Recorded 下契约字段一致。"""
    a = in_memory.writeback_payout_ready(_PAYOUT_REQ).to_dict()
    b = recorded.writeback_payout_ready(_PAYOUT_REQ).to_dict()
    for key in ("case_id", "gate_status", "payment_adapter_called"):
        assert a[key] == b[key], f"{key}: {a[key]!r} != {b[key]!r}"


def test_in_memory_and_recorded_close_parity(
    in_memory: InMemoryL2CoreProvider,
    recorded: RecordedL2CoreProvider,
) -> None:
    in_memory.writeback_payout_ready(_PAYOUT_REQ)
    a = in_memory.writeback_close(_CLOSE_REQ).to_dict()
    b = recorded.writeback_close(_CLOSE_REQ).to_dict()
    for key in ("case_id", "gate_status", "close_opinion", "payment_adapter_called"):
        assert a[key] == b[key], f"{key}: {a[key]!r} != {b[key]!r}"


def test_provider_has_no_payment_side_channel(provider: L2CoreProvider) -> None:
    """适配器不得暴露可递增的支付调用计数（防暗示 L3）。"""
    assert not hasattr(provider, "payment_adapter_calls")
    ack = provider.writeback_payout_ready(_PAYOUT_REQ)
    assert ack.payment_adapter_called is False


class _AlwaysOkL2Core:
    """恶意/宽松适配器：无条件回写成功；用于证明人闸仍在服务层。"""

    def writeback_payout_ready(self, req: L2PayoutReadyRequest) -> L2PayoutReadyAck:
        return L2PayoutReadyAck(
            case_id=req.case_id,
            gate_status="PAYOUT_READY",
            payment_adapter_called=False,
            core_ref="ALWAYS-OK",
        )

    def writeback_close(self, req: L2CloseRequest) -> L2CloseAck:
        return L2CloseAck(
            case_id=req.case_id,
            gate_status="CLOSED",
            close_opinion=req.close_opinion.strip(),
            payment_adapter_called=False,
            core_ref="ALWAYS-OK",
        )


def test_swapping_adapter_does_not_bypass_latch() -> None:
    """换宽松适配器仍须人闸；payment_adapter_calls 不递增。"""
    from claims_api.error_codes import ErrorCode
    from claims_api.service import ClaimsDomainError, ClaimsService

    svc = ClaimsService(l2_core=_AlwaysOkL2Core())
    svc.evaluate("CLM-AMT-C-001")
    before = svc.payment_adapter_calls
    with pytest.raises(ClaimsDomainError) as exc:
        svc.writeback_payout_ready("CLM-AMT-C-001", human_latch_token=None)
    assert exc.value.error_code == ErrorCode.LATCH_REQUIRED.value
    case = svc.get_claim("CLM-AMT-C-001")
    assert case.gate_status != "PAYOUT_READY"
    assert case.latest_decision is not None
    assert case.latest_decision.payout_ready is False
    assert svc.payment_adapter_calls == before

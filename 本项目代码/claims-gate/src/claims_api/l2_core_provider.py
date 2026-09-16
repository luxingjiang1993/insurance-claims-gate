"""Integration L2 核心回写 Provider：出款就绪 / 结案。

人闸令牌与主数据校验留在 ClaimsService；本模块只做核心侧回写接缝。
默认 InMemory（进程内）；Recorded 用于无现网账号的契约验收。
Ready ≠ Deployed：契约测绿 = Integration-Ready，禁止宣称「已接核心」。

Rewrote from: REF-MISSIONS；SPEC-02C G3 L2
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class L2PayoutReadyRequest:
    """出款就绪回写请求（服务已完成人闸前置校验后下发）。"""

    case_id: str
    decision_type: str
    recommended_payout_amount: int | None
    policy_no: str
    human_latch_present: bool


@dataclass(frozen=True)
class L2PayoutReadyAck:
    """核心侧出款就绪回写确认；不得含自动支付指令。"""

    case_id: str
    gate_status: str
    payment_adapter_called: bool = False
    core_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        body = asdict(self)
        # 明确不写出 auto_pay / payment_instruction
        return body


@dataclass(frozen=True)
class L2CloseRequest:
    """结案回写请求。"""

    case_id: str
    close_opinion: str


@dataclass(frozen=True)
class L2CloseAck:
    """核心侧结案回写确认；与出款解耦。"""

    case_id: str
    gate_status: str
    close_opinion: str
    payment_adapter_called: bool = False
    core_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class L2CoreProvider(Protocol):
    """对外接缝：Integration L2 出款就绪回写与结案。"""

    def writeback_payout_ready(self, req: L2PayoutReadyRequest) -> L2PayoutReadyAck:
        ...

    def writeback_close(self, req: L2CloseRequest) -> L2CloseAck:
        ...


class InMemoryL2CoreProvider:
    """进程内模拟核心回写；默认 Demo / CI 实现。"""

    def __init__(self) -> None:
        self._payout_ready: dict[str, L2PayoutReadyAck] = {}
        self._closed: dict[str, L2CloseAck] = {}

    def writeback_payout_ready(self, req: L2PayoutReadyRequest) -> L2PayoutReadyAck:
        if not req.case_id.strip():
            raise ValueError("case_id 不能为空")
        if not req.human_latch_present:
            raise ValueError("InMemory L2 要求 human_latch_present=True（人闸由服务校验）")
        ack = L2PayoutReadyAck(
            case_id=req.case_id,
            gate_status="PAYOUT_READY",
            payment_adapter_called=False,
            core_ref=f"MEM-L2-PR-{req.case_id}",
        )
        self._payout_ready[req.case_id] = ack
        return ack

    def writeback_close(self, req: L2CloseRequest) -> L2CloseAck:
        opinion = (req.close_opinion or "").strip()
        if not req.case_id.strip():
            raise ValueError("case_id 不能为空")
        if not opinion:
            raise ValueError("close_opinion 不能为空")
        ack = L2CloseAck(
            case_id=req.case_id,
            gate_status="CLOSED",
            close_opinion=opinion,
            payment_adapter_called=False,
            core_ref=f"MEM-L2-CL-{req.case_id}",
        )
        self._closed[req.case_id] = ack
        return ack


def load_recorded_cassette(path: Path | str) -> dict[str, Any]:
    """加载 Recorded 夹具 JSON。"""
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"L2 Recorded 夹具格式错误: {p}")
    return data


class RecordedL2CoreProvider:
    """按录制夹具回放核心回写；无保司账号可跑绿契约测。

    不是现网客户端；不得据此宣称 Deployed / 已接核心。
    """

    def __init__(self, cassette: Mapping[str, Any]) -> None:
        self._cassette = dict(cassette)
        self._payout = dict(cassette.get("payout_ready") or {})
        self._close = dict(cassette.get("close") or {})

    def writeback_payout_ready(self, req: L2PayoutReadyRequest) -> L2PayoutReadyAck:
        entry = self._payout.get(req.case_id)
        if entry is None:
            raise KeyError(f"Recorded 夹具无 payout_ready 用例: {req.case_id}")
        self._assert_request_match(entry.get("request") or {}, asdict(req), op="payout_ready")
        resp = entry.get("response") or {}
        if resp.get("payment_adapter_called") is True:
            raise RuntimeError("Recorded L2 夹具禁止 payment_adapter_called=true")
        return L2PayoutReadyAck(
            case_id=str(resp.get("case_id") or req.case_id),
            gate_status=str(resp["gate_status"]),
            payment_adapter_called=False,
            core_ref=resp.get("core_ref"),
        )

    def writeback_close(self, req: L2CloseRequest) -> L2CloseAck:
        entry = self._close.get(req.case_id)
        if entry is None:
            raise KeyError(f"Recorded 夹具无 close 用例: {req.case_id}")
        expected = entry.get("request") or {}
        actual = {"case_id": req.case_id, "close_opinion": req.close_opinion.strip()}
        self._assert_request_match(expected, actual, op="close")
        resp = entry.get("response") or {}
        if resp.get("payment_adapter_called") is True:
            raise RuntimeError("Recorded L2 夹具禁止 payment_adapter_called=true")
        return L2CloseAck(
            case_id=str(resp.get("case_id") or req.case_id),
            gate_status=str(resp["gate_status"]),
            close_opinion=str(resp.get("close_opinion") or req.close_opinion.strip()),
            payment_adapter_called=False,
            core_ref=resp.get("core_ref"),
        )

    @staticmethod
    def _assert_request_match(
        expected: Mapping[str, Any],
        actual: Mapping[str, Any],
        *,
        op: str,
    ) -> None:
        for key, want in expected.items():
            got = actual.get(key)
            if key == "close_opinion" and isinstance(want, str) and isinstance(got, str):
                if want.strip() != got.strip():
                    raise AssertionError(
                        f"Recorded {op} 请求字段 {key} 不匹配: want={want!r} got={got!r}"
                    )
                continue
            if got != want:
                raise AssertionError(
                    f"Recorded {op} 请求字段 {key} 不匹配: want={want!r} got={got!r}"
                )

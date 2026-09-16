"""OCR Provider：extract → 规范化文本，再进入既有用户可控文本收纳。

默认 Stub（进程内规范化）；Recorded 用于无真 OCR 账号的契约验收。
Ready ≠ Deployed：契约测绿 = Integration-Ready，禁止宣称「生产 OCR 已上线」。

Rewrote from: REF-MISSIONS；SPEC-02C G3 OCR
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class OcrExtractRequest:
    """OCR 抽取请求：图引用与/或原始载荷（客户端预填文本）。"""

    image_id: str | None = None
    raw_payload: str | None = None


@dataclass(frozen=True)
class OcrExtractResult:
    """规范化文本结果；不得含 Deployed / 真供应商上线宣称。"""

    normalized_text: str
    ocr_integration_status: str = "Integration-Ready"
    ocr_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        body = asdict(self)
        # 明确不写 deployed / production_live
        return body


class OcrProvider(Protocol):
    """对外接缝：OCR extract → 规范化文本。"""

    def extract(self, req: OcrExtractRequest) -> OcrExtractResult:
        ...


def normalize_ocr_text(raw: str | None) -> str:
    """规范化：首尾空白 strip；全空白→空串。"""
    if raw is None:
        return ""
    return str(raw).strip()


class StubOcrProvider:
    """默认 CI / Demo：对 raw_payload 做规范化；可选 image_id→文本种子。

    不是真 OCR 供应商；不得据此宣称生产 OCR 已上线。
    """

    def __init__(self, image_text: Mapping[str, str] | None = None) -> None:
        self._image_text = dict(image_text or {})

    def extract(self, req: OcrExtractRequest) -> OcrExtractResult:
        if req.raw_payload is not None:
            text = normalize_ocr_text(req.raw_payload)
            return OcrExtractResult(
                normalized_text=text,
                ocr_integration_status="Integration-Ready",
                ocr_ref="STUB-OCR-RAW",
            )
        if req.image_id:
            seeded = self._image_text.get(req.image_id)
            if seeded is not None:
                return OcrExtractResult(
                    normalized_text=normalize_ocr_text(seeded),
                    ocr_integration_status="Integration-Ready",
                    ocr_ref=f"STUB-OCR-{req.image_id}",
                )
            return OcrExtractResult(
                normalized_text="",
                ocr_integration_status="Integration-Ready",
                ocr_ref=f"STUB-OCR-{req.image_id}",
            )
        return OcrExtractResult(
            normalized_text="",
            ocr_integration_status="Integration-Ready",
            ocr_ref="STUB-OCR-EMPTY",
        )


def load_recorded_cassette(path: Path | str) -> dict[str, Any]:
    """加载 OCR Recorded 夹具 JSON。"""
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"OCR Recorded 夹具格式错误: {p}")
    return data


class RecordedOcrProvider:
    """按录制夹具回放 OCR 抽取；无真 OCR 账号可跑绿契约测。

    不是现网客户端；不得据此宣称 Deployed / 生产 OCR 已上线。
    """

    def __init__(self, cassette: Mapping[str, Any]) -> None:
        self._cassette = dict(cassette)
        self._by_image = dict(cassette.get("by_image_id") or {})
        self._by_raw = dict(cassette.get("by_raw_payload") or {})

    def extract(self, req: OcrExtractRequest) -> OcrExtractResult:
        if req.raw_payload is not None:
            entry = self._by_raw.get(req.raw_payload)
            if entry is None:
                raise KeyError(f"Recorded OCR 夹具无 raw_payload 用例: {req.raw_payload!r}")
            self._assert_request_match(
                entry.get("request") or {},
                {"raw_payload": req.raw_payload},
                op="raw_payload",
            )
            return self._result_from_entry(entry, fallback_text=normalize_ocr_text(req.raw_payload))

        if req.image_id:
            entry = self._by_image.get(req.image_id)
            if entry is None:
                raise KeyError(f"Recorded OCR 夹具无 image_id 用例: {req.image_id}")
            self._assert_request_match(
                entry.get("request") or {},
                {"image_id": req.image_id},
                op="image_id",
            )
            return self._result_from_entry(entry, fallback_text="")

        raise ValueError("Recorded OCR 请求须提供 image_id 或 raw_payload")

    @staticmethod
    def _result_from_entry(
        entry: Mapping[str, Any],
        *,
        fallback_text: str,
    ) -> OcrExtractResult:
        resp = entry.get("response") or {}
        text = resp.get("normalized_text")
        if text is None:
            text = fallback_text
        return OcrExtractResult(
            normalized_text=normalize_ocr_text(str(text)),
            ocr_integration_status="Integration-Ready",
            ocr_ref=resp.get("ocr_ref"),
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
            if got != want:
                raise AssertionError(
                    f"Recorded OCR {op} 请求字段 {key} 不匹配: want={want!r} got={got!r}"
                )

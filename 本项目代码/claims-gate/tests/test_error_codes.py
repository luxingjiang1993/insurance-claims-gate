"""接缝：最小 error_code 表骨架已登记。"""

from __future__ import annotations

from claims_api.error_codes import ERROR_CODE_TABLE, ErrorCode


def test_minimal_error_codes_registered() -> None:
    required = {
        "VALIDATION_FAILED",
        "LATCH_REQUIRED",
        "CITATION_NOT_IN_KB",
        "DOCUMENT_STATUS_FORBIDDEN",
        "MASTER_DATA_MISMATCH",
    }
    assert required.issubset(set(ERROR_CODE_TABLE))
    for code in required:
        assert ErrorCode(code).value == code
        assert ERROR_CODE_TABLE[code].strip()

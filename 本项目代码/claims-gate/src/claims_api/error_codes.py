"""理赔 HTTP 产品面：错误码表骨架（P1-4）。

Rewrote from: REF-MISSIONS（limits.py 错误码模式换域）
"""

from __future__ import annotations

from enum import Enum


class ErrorCode(str, Enum):
    """最小冻结集合；语义占位，后续票细化映射。"""

    VALIDATION_FAILED = "VALIDATION_FAILED"
    LATCH_REQUIRED = "LATCH_REQUIRED"
    CITATION_NOT_IN_KB = "CITATION_NOT_IN_KB"
    DOCUMENT_STATUS_FORBIDDEN = "DOCUMENT_STATUS_FORBIDDEN"
    MASTER_DATA_MISMATCH = "MASTER_DATA_MISMATCH"
    AUTH_FAILED = "AUTH_FAILED"
    PERMISSION_DENIED = "PERMISSION_DENIED"


# 占位语义：供 API / machine_check / 文档对照，禁止静默发明同义码
ERROR_CODE_TABLE: dict[str, str] = {
    ErrorCode.VALIDATION_FAILED.value: "请求或契约校验失败，不得继续门禁推进",
    ErrorCode.LATCH_REQUIRED.value: "当前动作要求人闸令牌，缺令牌则拒绝",
    ErrorCode.CITATION_NOT_IN_KB.value: "条款引用未落库（doc/条款项/版本不匹配）",
    ErrorCode.DOCUMENT_STATUS_FORBIDDEN.value: "文书效力态不允许（如无人闸升 EXTERNAL_NOTIFY）",
    ErrorCode.MASTER_DATA_MISMATCH.value: "保单/批单/案件主数据不一致，禁止出款就绪",
    ErrorCode.AUTH_FAILED.value: "登录失败或会话无效",
    ErrorCode.PERMISSION_DENIED.value: "当前角色无权执行该操作（如非主管批人闸、viewer 写操作）",
}

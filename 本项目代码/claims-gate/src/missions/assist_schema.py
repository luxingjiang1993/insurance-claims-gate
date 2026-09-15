"""assist 建议体 JSON Schema：citation 槽三联键硬停。

非法形状不得进入采纳路径（H3 的 Schema 层）。落库门仍由 KnowledgeBase.validate_citation 执行。

Rewrote from: REF-COURSE-03
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "schemas"

_SCHEMA: dict[str, Any] | None = None


class AssistSchemaError(ValueError):
    """非法 assist 建议体 / citation 槽：不得采纳。"""


def _load_schema() -> dict[str, Any]:
    global _SCHEMA
    if _SCHEMA is None:
        _SCHEMA = json.loads(
            (SCHEMAS_DIR / "assist_suggestion.schema.json").read_text(encoding="utf-8")
        )
    return _SCHEMA


def _format_errors(errors: list[Any]) -> str:
    msgs = [
        f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}"
        for err in errors
    ]
    return "; ".join(msgs[:5])


def validate_assist_suggestion_dict(payload: dict[str, Any]) -> None:
    """校验 assist 结构化输出；不通过则抛 AssistSchemaError。"""
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if errors:
        raise AssistSchemaError(
            "非法 assist 建议体（citation Schema 槽），拒绝: " + _format_errors(errors)
        )


def validate_assist_citations_schema(citations: list[dict[str, Any]]) -> None:
    """校验采纳请求中的 citations 元素是否满足 Schema 槽（直接验 $defs，不包假信封）。"""
    schema = _load_schema()
    citation_schema = schema["$defs"]["assist_citation"]
    # 解析 $defs 引用时需带上完整 schema 作为根
    validator = Draft202012Validator(
        {
            "$schema": schema.get("$schema"),
            "$defs": schema.get("$defs", {}),
            **citation_schema,
        }
    )
    all_errors: list[Any] = []
    for idx, item in enumerate(citations):
        for err in validator.iter_errors(item):
            all_errors.append((idx, err))
    if all_errors:
        msgs = [
            f"citations/{idx}/{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}"
            for idx, err in all_errors[:5]
        ]
        raise AssistSchemaError(
            "非法 assist citation 槽，拒绝采纳: " + "; ".join(msgs)
        )

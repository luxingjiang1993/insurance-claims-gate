"""mission plan request JSON Schema 硬停（Q-A2）。

Rewrote from: REF-COURSE-03（Schema 外形）；REF-MISSIONS（入账前硬停语义）
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "schemas"


class PlanSchemaError(ValueError):
    """非法 plan request：不得开工、不得创建 implement feature。"""


def validate_plan_request(payload: dict[str, Any]) -> None:
    """规划入参硬停：不通过则抛 PlanSchemaError。"""
    # goal 空白视为缺 goal（schema minLength 不 trim）
    goal = payload.get("goal")
    if isinstance(goal, str) and not goal.strip():
        raise PlanSchemaError("非法 plan request，拒绝开工: goal: 不能为空或仅空白")

    schema = json.loads(
        (SCHEMAS_DIR / "mission_plan_request.schema.json").read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(schema)
    # 规范化后再校验：空白 goal 已拦截；其余按 schema
    normalized = dict(payload)
    if isinstance(normalized.get("goal"), str):
        normalized["goal"] = normalized["goal"].strip()
    errors = sorted(validator.iter_errors(normalized), key=lambda e: list(e.path))
    if errors:
        msgs = [
            f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}"
            for err in errors
        ]
        raise PlanSchemaError(
            "非法 plan request，拒绝开工: " + "; ".join(msgs[:5])
        )

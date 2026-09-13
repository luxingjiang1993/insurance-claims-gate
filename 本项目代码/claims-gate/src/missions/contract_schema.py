"""validation contract JSON Schema 硬停（P1-2）。

Rewrote from: REF-MISSIONS（schemas/validation_contract.schema.json）
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "schemas"


class ContractSchemaError(ValueError):
    """非法 validation contract：不得开工。"""


def validate_contract_dict(payload: dict[str, Any]) -> None:
    """入账前硬停：不通过则抛 ContractSchemaError，不得进入 Worker。"""
    schema = json.loads(
        (SCHEMAS_DIR / "validation_contract.schema.json").read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if errors:
        msgs = [
            f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}"
            for err in errors
        ]
        raise ContractSchemaError(
            "非法 validation contract，拒绝开工: " + "; ".join(msgs[:5])
        )

"""接缝：非法 validation contract 在入账前 JSON Schema 硬停。"""

from __future__ import annotations

import pytest

from missions.contract_schema import ContractSchemaError, validate_contract_dict


def test_illegal_contract_missing_assertions_hard_stops() -> None:
    bad = {
        "mission_id": "m-bad",
        "title": "x",
        "goal": "y",
        "version": "1.0.0",
        "created_by": "orchestrator",
        "assertions": [],
        "source_citations": [
            {
                "doc_id": "d",
                "chunk_id": "c",
                "clause_id": "POL-CLAIM-001",
                "quote": "材料受理",
                "score": 0.9,
            }
        ],
    }
    with pytest.raises(ContractSchemaError):
        validate_contract_dict(bad)


def test_illegal_contract_bad_assertion_id_hard_stops() -> None:
    bad = {
        "mission_id": "m-bad",
        "title": "x",
        "goal": "y",
        "version": "1.0.0",
        "created_by": "orchestrator",
        "assertions": [
            {
                "id": "BAD-ID",
                "behavior": "b",
                "policy_clause_id": "POL-CLAIM-001",
                "acceptance": "a",
                "machine_check": {"type": "claim_header_l1", "params": {}},
            }
        ],
        "source_citations": [
            {
                "doc_id": "d",
                "chunk_id": "c",
                "clause_id": "POL-CLAIM-001",
                "quote": "材料受理",
                "score": 0.9,
            }
        ],
    }
    with pytest.raises(ContractSchemaError):
        validate_contract_dict(bad)


def test_valid_minimal_contract_passes() -> None:
    good = {
        "mission_id": "m-ok",
        "title": "脚手架契约",
        "goal": "拉到案件头并进入材料受理",
        "version": "1.0.0",
        "created_by": "orchestrator",
        "inference_track": "deterministic",
        "assertions": [
            {
                "id": "A-001",
                "behavior": "L1 只读返回案件头且门禁态为 MATERIALS_INTAKE",
                "policy_clause_id": "POL-CLAIM-001",
                "acceptance": "GET /claims/{case_id} 含最低字段且 gate_status=MATERIALS_INTAKE",
                "machine_check": {
                    "type": "claim_header_l1",
                    "params": {"case_id": "CLM-SC01-001"},
                },
            }
        ],
        "source_citations": [
            {
                "doc_id": "POL-CLAIM-L1",
                "chunk_id": "POL-CLAIM-L1::chunk-1",
                "clause_id": "POL-CLAIM-001",
                "quote": "立案后进入材料受理态",
                "score": 0.95,
            }
        ],
    }
    validate_contract_dict(good)

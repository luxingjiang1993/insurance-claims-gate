"""接缝：金标薄切片协议 + 导入导出加深（票 38 / P-E3）。

S0：隔离契约——双标+第三人协议外形、case_id、H4 deferred、禁止 ≥300/grounded 宣称。
S2：eval_bypass ——薄切片 HTTP 导入导出保留 annotation（可选）。

硬边界：不得用合成自标冒充真双标运营；n<10 则 H4=deferred。
Rewrote from: REF-CASE-OPENEVALS
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from claims_api.api import app, reset_service

ROOT = Path(__file__).resolve().parents[2]


def _client(db_path: Path | None = None) -> TestClient:
    reset_service(db_path=db_path)
    return TestClient(app)


def _login(client: TestClient, username: str) -> dict[str, str]:
    resp = client.post(
        "/auth/login",
        json={"username": username, "password": username},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['session_token']}"}


def _thin_slice_record(
    case_id: str = "CLM-SC01-001",
    *,
    disagree: bool = False,
) -> dict:
    """角色占位双标行外形（非真人名）。"""
    label_a = {"citation_faithful": True, "supports_claim": True}
    label_b = (
        {"citation_faithful": False, "supports_claim": False}
        if disagree
        else dict(label_a)
    )
    return {
        "case_id": case_id,
        "inputs": {"scene": "sc01", "suggestion_span": "demo"},
        "expected": {"citation_faithful": True, "supports_claim": True},
        "annotation": {
            "annotator_a_role": "external_claims_advisor_a",
            "annotator_b_role": "external_claims_advisor_b",
            "adjudicator_role": "third_party_adjudicator",
            "label_a": label_a,
            "label_b": label_b,
            "adjudication": {
                "final": "agree" if not disagree else "a_wins",
                "reason_code": "consensus" if not disagree else "adjudicated",
            },
            "disagreement": disagree,
        },
        "notes": "外形样例；非真实外聘双标运营",
    }


def test_thin_slice_module_declares_protocol_and_refs() -> None:
    """加深模块声明薄切片协议、H4 deferred 与 Rewrote from。"""
    path = ROOT / "src" / "missions" / "gold_label_io.py"
    text = path.read_text(encoding="utf-8")
    assert "金标薄切片" in text
    assert "第三人" in text or "third_party" in text
    assert "H4" in text
    assert "deferred" in text
    assert "REF-CASE-OPENEVALS" in text
    assert "Rewrote from" in text


def test_assess_h4_deferred_when_n_below_ten() -> None:
    """α：n<10 诚实 H4=deferred；n_met 仍禁止宣称 grounded。"""
    from missions.gold_label_io import (
        GoldLabelIoError,
        assess_h4_status,
        assert_h4_claim_allowed,
    )

    status = assess_h4_status(1)
    assert status == "deferred"
    assert assess_h4_status(10) == "n_met"
    with pytest.raises(GoldLabelIoError):
        assert_h4_claim_allowed(status, claim="grounded")
    with pytest.raises(GoldLabelIoError):
        assert_h4_claim_allowed("n_met", claim="grounded")


def test_parse_thin_slice_rejects_swapped_protocol_roles() -> None:
    """协议角色槽位固定，不得把裁决人占位填进双标槽。"""
    from missions.gold_label_io import GoldLabelIoError, parse_dataset

    bad = _thin_slice_record()
    bad["annotation"]["annotator_a_role"] = "third_party_adjudicator"
    with pytest.raises(GoldLabelIoError):
        parse_dataset(
            {
                "schema": "claims-gate-gold-thin-slice-v1",
                "dataset_id": "thin-swap",
                "is_gold_thin_slice": True,
                "records": [bad],
            }
        )


def test_parse_thin_slice_requires_dual_plus_third_roles() -> None:
    """薄切片记录须双标角色 + 第三人裁决角色占位。"""
    from missions.gold_label_io import GoldLabelIoError, parse_dataset

    with pytest.raises(GoldLabelIoError):
        parse_dataset(
            {
                "schema": "claims-gate-gold-thin-slice-v1",
                "dataset_id": "thin-bad",
                "is_gold_thin_slice": True,
                "records": [
                    {
                        "case_id": "CLM-SC01-001",
                        "inputs": {},
                        "expected": {},
                    }
                ],
            }
        )


def test_parse_thin_slice_rejects_person_names_in_roles() -> None:
    """人名不得进仓；角色须为占位 id。"""
    from missions.gold_label_io import GoldLabelIoError, parse_dataset

    bad = _thin_slice_record()
    bad["annotation"]["annotator_a_role"] = "张三"
    with pytest.raises(GoldLabelIoError):
        parse_dataset(
            {
                "schema": "claims-gate-gold-thin-slice-v1",
                "dataset_id": "thin-name",
                "is_gold_thin_slice": True,
                "records": [bad],
            }
        )


def test_parse_thin_slice_rejects_ops_complete_and_full_workflow() -> None:
    """仍禁止 ≥300 运营完成与双人全量工作流标志。"""
    from missions.gold_label_io import GoldLabelIoError, parse_dataset

    base = {
        "schema": "claims-gate-gold-thin-slice-v1",
        "dataset_id": "thin-ops",
        "is_gold_thin_slice": True,
        "records": [_thin_slice_record()],
    }
    with pytest.raises(GoldLabelIoError):
        parse_dataset({**base, "gold_ops_complete": True})
    with pytest.raises(GoldLabelIoError):
        parse_dataset({**base, "dual_annotation_workflow": True})


def test_parse_thin_slice_happy_path_exports_h4_deferred() -> None:
    """合法薄切片：保留 case_id + annotation；n=1 → h4_status=deferred。"""
    from missions.gold_label_io import parse_dataset

    dataset = parse_dataset(
        {
            "schema": "claims-gate-gold-thin-slice-v1",
            "dataset_id": "thin-ok",
            "is_gold_thin_slice": True,
            "records": [_thin_slice_record()],
        }
    )
    assert dataset.is_gold_thin_slice is True
    assert dataset.h4_status == "deferred"
    assert dataset.gold_ops_complete is False
    assert dataset.dual_annotation_workflow is False
    assert dataset.records[0].case_id == "CLM-SC01-001"
    assert dataset.records[0].annotation is not None
    assert (
        dataset.records[0].annotation["adjudicator_role"]
        == "third_party_adjudicator"
    )
    payload = dataset.to_dict()
    assert payload["h4_status"] == "deferred"
    assert payload["protocol"]["dual_annotation"] is True
    assert payload["protocol"]["third_party_adjudication"] is True
    assert payload["protocol"]["person_names_in_repo"] is False
    assert "≥300" not in payload["docs_note"] or "禁止" in payload["docs_note"] or "不得" in payload["docs_note"]


def test_legacy_preview_schema_still_loads() -> None:
    """票 32 钩子外形仍可用（非薄切片）。"""
    from missions.gold_label_io import load_dataset_file

    path = ROOT / "artifacts" / "gold_label_dataset_preview.json"
    dataset = load_dataset_file(path)
    assert dataset.is_gold_thin_slice is False
    assert dataset.h4_status == "deferred"
    assert all(r.case_id for r in dataset.records)


def test_artifact_thin_slice_example_honest() -> None:
    """冻结外形样例：有协议字段；不得宣称 grounded / ≥300 已完成。"""
    path = ROOT / "artifacts" / "gold_thin_slice" / "gold_thin_slice.v1.example.json"
    assert path.is_file()
    from missions.gold_label_io import load_dataset_file

    dataset = load_dataset_file(path)
    assert dataset.is_gold_thin_slice is True
    assert dataset.h4_status == "deferred"
    raw = path.read_text(encoding="utf-8")
    assert "金标已达标" not in raw
    assert "≥300 已完成" not in raw
    assert "grounded" not in raw.lower() or "禁止" in raw or "不得" in raw


def test_acceptance_and_user_docs_mention_protocol() -> None:
    """双标+第三人协议写入验收与手册。"""
    acceptance = (
        ROOT / "docs" / "acceptance" / "gold-thin-slice.md"
    ).read_text(encoding="utf-8")
    assert "双" in acceptance and ("第三人" in acceptance or "裁决" in acceptance)
    assert "H4" in acceptance and "deferred" in acceptance
    assert "≥300" in acceptance

    # 仓库根：本项目代码/claims-gate → 仓库根
    repo_root = ROOT.parents[1]
    guide = repo_root / "docs" / "user" / "USER_GUIDE.md"
    text = guide.read_text(encoding="utf-8")
    assert "金标薄切片" in text
    assert "H4" in text
    assert "deferred" in text.lower() or "Deferred" in text


def test_store_roundtrip_keeps_annotation(tmp_path: Path) -> None:
    """导入导出加深：annotation 与 case_id 可往返。"""
    from claims_api.sqlite_store import SqliteCaseStore
    from missions.gold_label_io import export_dataset, import_dataset, parse_dataset

    db = tmp_path / "thin.sqlite"
    store = SqliteCaseStore(db)
    try:
        payload = parse_dataset(
            {
                "schema": "claims-gate-gold-thin-slice-v1",
                "dataset_id": "thin-roundtrip",
                "is_gold_thin_slice": True,
                "records": [_thin_slice_record("CLM-SC02-001", disagree=True)],
            }
        )
        imported = import_dataset(store, payload, actor_user_id="adjuster")
        assert imported.imported_count == 1
        assert imported.h4_status == "deferred"
        exported = export_dataset(store, dataset_id="thin-roundtrip")
        assert exported.is_gold_thin_slice is True
        assert exported.h4_status == "deferred"
        assert exported.records[0].case_id == "CLM-SC02-001"
        assert exported.records[0].annotation is not None
        assert exported.records[0].annotation["disagreement"] is True
    finally:
        store.close()


@pytest.mark.eval_bypass
def test_http_thin_slice_import_export(tmp_path: Path) -> None:
    """HTTP：薄切片导入携带 annotation；导出可回读；h4_status=deferred。"""
    db = tmp_path / "thin-http.sqlite"
    client = _client(db)
    adj = _login(client, "adjuster")
    body = {
        "schema": "claims-gate-gold-thin-slice-v1",
        "dataset_id": "thin-http",
        "is_gold_thin_slice": True,
        "records": [_thin_slice_record("CLM-SC03-001")],
    }
    imported = client.post("/eval/gold-labels/import", json=body, headers=adj)
    assert imported.status_code == 200, imported.text
    data = imported.json()
    assert data["imported_count"] == 1
    assert data["h4_status"] == "deferred"
    assert data["gold_ops_complete"] is False

    exported = client.get(
        "/eval/gold-labels/export?dataset_id=thin-http",
        headers=adj,
    )
    assert exported.status_code == 200, exported.text
    out = exported.json()
    assert out["h4_status"] == "deferred"
    assert out["is_gold_thin_slice"] is True
    assert out["records"][0]["case_id"] == "CLM-SC03-001"
    assert out["records"][0]["annotation"]["annotator_a_role"] == (
        "external_claims_advisor_a"
    )

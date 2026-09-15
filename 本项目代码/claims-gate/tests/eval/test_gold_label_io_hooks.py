"""接缝：金标数据集导入/导出钩子 + case_id（票 32 / W2）。

S0：隔离契约（默认 CI）——不替代 machine_check；不进合门禁；不宣称金标已达标。
S2：eval_bypass ——导入后可按 case_id 导出（可选；不挡合门禁）。

前置：票 29 已落地。本票只做接口/字段/最小外形，不实现双人标注全量运营。
Rewrote from: REF-CASE-OPENEVALS, REF-MISSIONS
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


def test_gold_label_io_module_declares_hooks_and_refs() -> None:
    """旁路模块存在；声明不替代 machine_check；含 Rewrote from 与 case_id。"""
    path = ROOT / "src" / "missions" / "gold_label_io.py"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "旁路" in text and "非合门禁" in text
    assert "machine_check" in text
    assert "case_id" in text
    assert "REF-CASE-OPENEVALS" in text
    assert "REF-MISSIONS" in text
    # 允许否定句；禁止把「金标已达标」写成已交付事实
    if "金标已达标" in text:
        assert "不得宣称" in text or "禁止" in text


def test_checks_does_not_route_through_gold_label_io() -> None:
    """硬约束：合门禁主缝仍是 machine_check，不得吞并金标 I/O。"""
    checks_src = (ROOT / "src" / "missions" / "checks.py").read_text(encoding="utf-8")
    assert "gold_label_io" not in checks_src
    assert "/eval/gold-labels" not in checks_src


def test_pytest_ini_still_excludes_eval_bypass() -> None:
    """默认 pytest 须排除 eval_bypass（金标 I/O 失败不得让 CI 红）。"""
    ini = (ROOT / "pytest.ini").read_text(encoding="utf-8")
    assert "not eval_bypass" in ini


def test_preview_dataset_carries_case_id_and_not_complete() -> None:
    """样例外形：每条有 case_id；不得宣称运营完成。"""
    path = ROOT / "artifacts" / "gold_label_dataset_preview.json"
    assert path.is_file()
    from missions.gold_label_io import load_dataset_file

    dataset = load_dataset_file(path)
    assert dataset.records
    assert all(r.case_id for r in dataset.records)
    assert dataset.gold_ops_complete is False
    assert dataset.dual_annotation_workflow is False
    raw = path.read_text(encoding="utf-8")
    assert "金标已达标" not in raw
    assert "≥300 已完成" not in raw


def test_parse_rejects_missing_case_id() -> None:
    from missions.gold_label_io import GoldLabelIoError, parse_dataset

    with pytest.raises(GoldLabelIoError):
        parse_dataset(
            {
                "dataset_id": "bad",
                "records": [{"inputs": {}, "expected": {}}],
            }
        )


def test_parse_rejects_ops_complete_claim() -> None:
    from missions.gold_label_io import GoldLabelIoError, parse_dataset

    with pytest.raises(GoldLabelIoError):
        parse_dataset(
            {
                "dataset_id": "bad",
                "gold_ops_complete": True,
                "records": [{"case_id": "CLM-SC01-001"}],
            }
        )


def test_parse_rejects_dual_annotation_workflow_claim() -> None:
    from missions.gold_label_io import GoldLabelIoError, parse_dataset

    with pytest.raises(GoldLabelIoError):
        parse_dataset(
            {
                "dataset_id": "bad",
                "dual_annotation_workflow": True,
                "records": [{"case_id": "CLM-SC01-001"}],
            }
        )


def test_store_roundtrip_keeps_case_id(tmp_path: Path) -> None:
    """本地表：导入后可按 case_id 导出。"""
    from claims_api.sqlite_store import SqliteCaseStore
    from missions.gold_label_io import export_dataset, import_dataset, parse_dataset

    db = tmp_path / "gold.sqlite"
    store = SqliteCaseStore(db)
    try:
        payload = parse_dataset(
            {
                "dataset_id": "preview-hook",
                "records": [
                    {
                        "case_id": "CLM-SC01-001",
                        "inputs": {"scene": "sc01"},
                        "expected": {"route": "supplement"},
                    }
                ],
            }
        )
        imported = import_dataset(store, payload, actor_user_id="adjuster")
        assert imported.imported_count == 1
        exported = export_dataset(store, dataset_id="preview-hook")
        assert exported.dataset_id == "preview-hook"
        assert exported.gold_ops_complete is False
        assert [r.case_id for r in exported.records] == ["CLM-SC01-001"]
        assert exported.records[0].inputs["scene"] == "sc01"
    finally:
        store.close()


def test_cli_module_exposes_import_export_entry() -> None:
    """约定脚本入口：python -m missions.gold_label_io。"""
    path = ROOT / "src" / "missions" / "gold_label_io.py"
    text = path.read_text(encoding="utf-8")
    assert "def main(" in text
    assert '__name__ == "__main__"' in text
    assert "import" in text and "export" in text


@pytest.mark.eval_bypass
def test_http_import_export_associates_case_id(tmp_path: Path) -> None:
    """HTTP 钩子：导入携带 case_id，导出可回读；viewer 只读。"""
    db = tmp_path / "gold-http.sqlite"
    client = _client(db)
    adj = _login(client, "adjuster")
    body = {
        "dataset_id": "preview-hook",
        "records": [
            {
                "case_id": "CLM-SC02-001",
                "inputs": {"scene": "sc02"},
                "expected": {"route": "deny"},
            }
        ],
    }
    imported = client.post("/eval/gold-labels/import", json=body, headers=adj)
    assert imported.status_code == 200, imported.text
    data = imported.json()
    assert data["imported_count"] == 1
    assert data["gold_ops_complete"] is False
    assert data["blocks_track_a_gate"] is False

    exported = client.get(
        "/eval/gold-labels/export?dataset_id=preview-hook",
        headers=adj,
    )
    assert exported.status_code == 200, exported.text
    out = exported.json()
    assert out["dataset_id"] == "preview-hook"
    assert out["gold_ops_complete"] is False
    assert out["records"][0]["case_id"] == "CLM-SC02-001"

    viewer = _login(client, "viewer")
    denied = client.post("/eval/gold-labels/import", json=body, headers=viewer)
    assert denied.status_code == 403
    listed = client.get("/eval/gold-labels/export", headers=viewer)
    assert listed.status_code == 200

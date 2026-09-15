"""金标数据集导入/导出钩子（W2 Eval Ops · 票 32）。

硬约束（旁路，非合门禁主缝）：
- 默认 CI 合门禁仍以 missions.checks.machine_check 为准；
- 本入口失败不得改写人闸语义，不得进入默认 pytest -q 必过条件；
- 只预留接口/字段/最小外形：记录必须关联 case_id；
- 不实现双人标注全量工作流；不关闭 PRD ≥300 金标运营；
- 任何导出/响应不得宣称金标已达标。

数据集外形参考 OpenEvals 的 inputs/outputs（此处 outputs 落为 expected），
并延续票 11 合成抽检的 case_id 关联。

Rewrote from: REF-CASE-OPENEVALS, REF-MISSIONS
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from claims_api.sqlite_store import SqliteCaseStore
from missions.eval_entry import EVAL_GATE_ROLE

SCHEMA_ID = "claims-gate-gold-label-dataset-v1"
FORBIDDEN_CLAIM_PHRASES = ("金标已达标", "≥300 已完成")


class GoldLabelIoError(ValueError):
    """金标数据集外形或运营宣称不合法。"""


@dataclass
class GoldLabelRecord:
    """单条金标钩子行：必须能回到案件键。"""

    case_id: str
    inputs: dict[str, Any] = field(default_factory=dict)
    expected: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "inputs": dict(self.inputs),
            "expected": dict(self.expected),
            "notes": self.notes,
        }


@dataclass
class GoldLabelDataset:
    """金标数据集最小外形；运营完成标志恒为未完成。"""

    dataset_id: str
    records: list[GoldLabelRecord]
    gold_ops_complete: bool = False
    dual_annotation_workflow: bool = False
    schema: str = SCHEMA_ID
    docs_note: str = (
        "旁路钩子，非合门禁主缝；合门禁以 machine_check 为准；"
        "金标全量运营仍延后，不得宣称已达标"
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "dataset_id": self.dataset_id,
            "gold_ops_complete": False,
            "dual_annotation_workflow": False,
            "docs_note": self.docs_note,
            "records": [r.to_dict() for r in self.records],
        }


@dataclass
class GoldLabelImportResult:
    """导入钩子回执。"""

    dataset_id: str
    imported_count: int
    gold_ops_complete: bool = False
    dual_annotation_workflow: bool = False
    gate_role: str = EVAL_GATE_ROLE
    blocks_track_a_gate: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "imported_count": self.imported_count,
            "gold_ops_complete": False,
            "dual_annotation_workflow": False,
            "gate_role": self.gate_role,
            "blocks_track_a_gate": False,
        }


def _assert_no_completion_claim(text: str) -> None:
    for phrase in FORBIDDEN_CLAIM_PHRASES:
        if phrase in text:
            raise GoldLabelIoError(f"禁止宣称运营完成: {phrase}")


def parse_dataset(raw: dict[str, Any]) -> GoldLabelDataset:
    """校验导入 JSON：每条须有 case_id；拒绝运营完成/双人全量标志。"""
    if not isinstance(raw, dict):
        raise GoldLabelIoError("数据集须为 JSON 对象")
    dataset_id = str(raw.get("dataset_id") or "").strip()
    if not dataset_id:
        raise GoldLabelIoError("dataset_id 必填")
    if raw.get("gold_ops_complete") is True:
        raise GoldLabelIoError("金标全量运营仍延后，禁止 gold_ops_complete=true")
    if raw.get("dual_annotation_workflow") is True:
        raise GoldLabelIoError("本票不实现双人标注全量工作流")
    _assert_no_completion_claim(str(raw.get("docs_note") or ""))
    items = raw.get("records")
    if not isinstance(items, list) or not items:
        raise GoldLabelIoError("records 须为非空数组")
    records: list[GoldLabelRecord] = []
    for item in items:
        if not isinstance(item, dict):
            raise GoldLabelIoError("records 元素须为对象")
        case_id = str(item.get("case_id") or "").strip()
        if not case_id:
            raise GoldLabelIoError("每条记录必须携带 case_id")
        notes = str(item.get("notes") or "")
        _assert_no_completion_claim(notes)
        inputs = item.get("inputs") or {}
        expected = item.get("expected") or item.get("outputs") or {}
        if not isinstance(inputs, dict) or not isinstance(expected, dict):
            raise GoldLabelIoError("inputs / expected 须为对象")
        records.append(
            GoldLabelRecord(
                case_id=case_id,
                inputs=dict(inputs),
                expected=dict(expected),
                notes=notes,
            )
        )
    return GoldLabelDataset(
        dataset_id=dataset_id,
        records=records,
        gold_ops_complete=False,
        dual_annotation_workflow=False,
        schema=str(raw.get("schema") or SCHEMA_ID),
    )


def load_dataset_file(path: Path | str) -> GoldLabelDataset:
    """从 UTF-8 JSON 文件加载数据集。"""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise GoldLabelIoError("数据集文件须为 JSON 对象")
    return parse_dataset(raw)


def import_dataset(
    store: SqliteCaseStore,
    dataset: GoldLabelDataset,
    *,
    actor_user_id: str,
) -> GoldLabelImportResult:
    """写入本地 SQLite 金标钩子表。"""
    stamp = datetime.now(timezone.utc).isoformat()
    for rec in dataset.records:
        store.upsert_gold_label_record(
            dataset_id=dataset.dataset_id,
            case_id=rec.case_id,
            inputs=rec.inputs,
            expected=rec.expected,
            notes=rec.notes,
            actor_user_id=actor_user_id,
            imported_at=stamp,
        )
    return GoldLabelImportResult(
        dataset_id=dataset.dataset_id,
        imported_count=len(dataset.records),
    )


def export_dataset(
    store: SqliteCaseStore,
    *,
    dataset_id: str | None = None,
    case_id: str | None = None,
) -> GoldLabelDataset:
    """从本地表导出；完成标志始终为 false。"""
    rows = store.list_gold_label_records(dataset_id=dataset_id, case_id=case_id)
    records = [
        GoldLabelRecord(
            case_id=str(row["case_id"]),
            inputs=dict(row["inputs"]),
            expected=dict(row["expected"]),
            notes=str(row.get("notes") or ""),
        )
        for row in rows
    ]
    export_id = dataset_id or (str(rows[0]["dataset_id"]) if rows else "unspecified")
    return GoldLabelDataset(dataset_id=export_id, records=records)


def _resolve_db_path(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    env = os.environ.get("CLAIMS_GATE_DB")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / "data" / "claims_gate.sqlite"


def main(argv: list[str] | None = None) -> int:
    """约定脚本入口：python -m missions.gold_label_io import|export。"""
    parser = argparse.ArgumentParser(
        description="金标数据集导入/导出钩子（旁路，非合门禁；不宣称已达标）"
    )
    parser.add_argument("action", choices=("import", "export"))
    parser.add_argument("--file", required=True, help="JSON 文件路径")
    parser.add_argument("--db", default=None, help="SQLite 路径；默认 CLAIMS_GATE_DB")
    parser.add_argument("--dataset-id", default=None, help="导出时过滤数据集")
    parser.add_argument("--case-id", default=None, help="导出时过滤案件键")
    parser.add_argument("--actor", default="adjuster", help="导入归因用户")
    args = parser.parse_args(argv)

    store = SqliteCaseStore(_resolve_db_path(args.db))
    try:
        if args.action == "import":
            dataset = load_dataset_file(args.file)
            result = import_dataset(store, dataset, actor_user_id=str(args.actor))
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
            return 0
        exported = export_dataset(
            store,
            dataset_id=args.dataset_id,
            case_id=args.case_id,
        )
        Path(args.file).write_text(
            json.dumps(exported.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "wrote": str(args.file),
                    "dataset_id": exported.dataset_id,
                    "record_count": len(exported.records),
                    "gold_ops_complete": False,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except GoldLabelIoError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())

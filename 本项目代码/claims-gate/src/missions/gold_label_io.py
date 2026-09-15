"""金标数据集导入/导出钩子（W2 票 32）+ 金标薄切片协议加深（票 38 / P-E3）。

硬约束（旁路，非合门禁主缝）：
- 默认 CI 合门禁仍以 missions.checks.machine_check 为准；
- 本入口失败不得改写人闸语义，不得进入默认 pytest -q 必过条件；
- 记录必须关联 case_id；
- 金标薄切片：外聘核赔顾问双标 + 第三人裁决（角色占位，人名不进仓）；
- α 目标 n≥10；不足则 H4=deferred，禁止宣称 grounded；
- 不实现双人标注全量工作流；不关闭 PRD ≥300 金标运营；
- 任何导出/响应不得宣称金标已达标或 ≥300 已完成。

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
SCHEMA_ID_THIN_SLICE = "claims-gate-gold-thin-slice-v1"
THIN_SLICE_MIN_N = 10

ALLOWED_ROLE_PLACEHOLDERS = frozenset(
    {
        "external_claims_advisor_a",
        "external_claims_advisor_b",
        "third_party_adjudicator",
    }
)

FORBIDDEN_CLAIM_PHRASES = (
    "金标已达标",
    "≥300 已完成",
    ">=300 已完成",
)

FORBIDDEN_H4_CLAIM_PHRASES = (
    "grounded",
    "H4 已达标",
    "H4已达标",
    "忠实率已达标",
)

DEFAULT_DOCS_NOTE = (
    "旁路钩子，非合门禁主缝；合门禁以 machine_check 为准；"
    "金标全量运营仍延后，不得宣称已达标；禁止宣称 ≥300 已完成"
)

DEFAULT_THIN_SLICE_DOCS_NOTE = (
    "金标薄切片协议集：外聘核赔顾问双标 + 第三人裁决；角色占位、人名不进仓；"
    "旁路非合门禁；α 目标 n≥10，不足则 H4=deferred、禁止宣称 grounded；"
    "禁止宣称 ≥300 运营已完成"
)

THIN_SLICE_PROTOCOL: dict[str, Any] = {
    "dual_annotation": True,
    "third_party_adjudication": True,
    "annotator_roles": [
        "external_claims_advisor_a",
        "external_claims_advisor_b",
    ],
    "adjudicator_role": "third_party_adjudicator",
    "person_names_in_repo": False,
    "min_n_for_h4": THIN_SLICE_MIN_N,
}


class GoldLabelIoError(ValueError):
    """金标数据集外形或运营宣称不合法。"""


@dataclass
class GoldLabelRecord:
    """单条金标钩子行：必须能回到案件键；薄切片可带双标 annotation。"""

    case_id: str
    inputs: dict[str, Any] = field(default_factory=dict)
    expected: dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    annotation: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "case_id": self.case_id,
            "inputs": dict(self.inputs),
            "expected": dict(self.expected),
            "notes": self.notes,
        }
        if self.annotation is not None:
            out["annotation"] = dict(self.annotation)
        return out


@dataclass
class GoldLabelDataset:
    """金标 / 薄切片数据集外形；运营完成标志恒为未完成。"""

    dataset_id: str
    records: list[GoldLabelRecord]
    gold_ops_complete: bool = False
    dual_annotation_workflow: bool = False
    is_gold_thin_slice: bool = False
    schema: str = SCHEMA_ID
    docs_note: str = DEFAULT_DOCS_NOTE
    rewrote_from: str = "REF-CASE-OPENEVALS"

    @property
    def h4_status(self) -> str:
        return assess_h4_status(len(self.records))

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "schema": self.schema,
            "dataset_id": self.dataset_id,
            "gold_ops_complete": False,
            "dual_annotation_workflow": False,
            "is_gold_thin_slice": bool(self.is_gold_thin_slice),
            "h4_status": self.h4_status,
            "docs_note": self.docs_note,
            "rewrote_from": self.rewrote_from,
            "records": [r.to_dict() for r in self.records],
        }
        if self.is_gold_thin_slice:
            out["protocol"] = dict(THIN_SLICE_PROTOCOL)
        return out


@dataclass
class GoldLabelImportResult:
    """导入钩子回执。"""

    dataset_id: str
    imported_count: int
    gold_ops_complete: bool = False
    dual_annotation_workflow: bool = False
    is_gold_thin_slice: bool = False
    h4_status: str = "deferred"
    gate_role: str = EVAL_GATE_ROLE
    blocks_track_a_gate: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "imported_count": self.imported_count,
            "gold_ops_complete": False,
            "dual_annotation_workflow": False,
            "is_gold_thin_slice": bool(self.is_gold_thin_slice),
            "h4_status": self.h4_status,
            "gate_role": self.gate_role,
            "blocks_track_a_gate": False,
        }


def assess_h4_status(record_count: int) -> str:
    """α：n≥10 仅表示规模门槛已过；仍非 grounded 宣称许可。"""
    if record_count < THIN_SLICE_MIN_N:
        return "deferred"
    return "n_met"


def assert_h4_claim_allowed(h4_status: str, *, claim: str) -> None:
    """在忠实率/κ 门未落地前，一律禁止 grounded 等达标话术。

    `n_met` 只表示规模门槛；不得据此宣称 grounded（见 SPEC H4）。
    """
    lowered = claim.strip().lower()
    for phrase in FORBIDDEN_H4_CLAIM_PHRASES:
        if phrase.lower() in lowered or phrase.lower() == lowered:
            raise GoldLabelIoError(
                f"H4={h4_status}，禁止宣称: {claim}（须忠实率/κ 门，非仅 n）"
            )
    if lowered == "grounded":
        raise GoldLabelIoError(
            f"H4={h4_status}，禁止宣称: grounded（须忠实率/κ 门，非仅 n）"
        )


def _assert_no_completion_claim(text: str) -> None:
    """拒绝正面运营完成宣称；「禁止/不得」须与禁用短语绑定同一否定句。"""
    for phrase in FORBIDDEN_CLAIM_PHRASES:
        if phrase not in text:
            continue
        # 允许「禁止宣称 ≥300 已完成」；拒绝无否定的正面宣称
        idx = text.find(phrase)
        window = text[max(0, idx - 12) : idx]
        if "禁止" in window or "不得" in window:
            continue
        raise GoldLabelIoError(f"禁止宣称运营完成: {phrase}")
    lowered = text.lower()
    for phrase in FORBIDDEN_H4_CLAIM_PHRASES:
        if phrase.lower() not in lowered:
            continue
        idx = lowered.find(phrase.lower())
        window = text[max(0, idx - 12) : idx]
        if "禁止" in window or "不得" in window:
            continue
        raise GoldLabelIoError(f"禁止宣称 H4/grounded 达标: {phrase}")


def _validate_role_placeholder(role: str, field_name: str) -> str:
    value = str(role or "").strip()
    if not value:
        raise GoldLabelIoError(f"{field_name} 必填（角色占位）")
    expected = {
        "annotator_a_role": "external_claims_advisor_a",
        "annotator_b_role": "external_claims_advisor_b",
        "adjudicator_role": "third_party_adjudicator",
    }.get(field_name)
    if expected is not None and value != expected:
        raise GoldLabelIoError(
            f"{field_name} 须为协议角色占位 {expected}（人名不进仓）: {value}"
        )
    if value not in ALLOWED_ROLE_PLACEHOLDERS:
        raise GoldLabelIoError(
            f"{field_name} 须为角色占位 id（人名不进仓）: {value}"
        )
    return value


def _parse_annotation(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise GoldLabelIoError("annotation 须为对象")
    annotator_a = _validate_role_placeholder(
        str(raw.get("annotator_a_role") or ""), "annotator_a_role"
    )
    annotator_b = _validate_role_placeholder(
        str(raw.get("annotator_b_role") or ""), "annotator_b_role"
    )
    adjudicator = _validate_role_placeholder(
        str(raw.get("adjudicator_role") or ""), "adjudicator_role"
    )
    label_a = raw.get("label_a")
    label_b = raw.get("label_b")
    adjudication = raw.get("adjudication")
    if not isinstance(label_a, dict) or not isinstance(label_b, dict):
        raise GoldLabelIoError("label_a / label_b 须为对象")
    if not isinstance(adjudication, dict):
        raise GoldLabelIoError("adjudication 须为对象")
    disagreement = bool(raw.get("disagreement", False))
    return {
        "annotator_a_role": annotator_a,
        "annotator_b_role": annotator_b,
        "adjudicator_role": adjudicator,
        "label_a": dict(label_a),
        "label_b": dict(label_b),
        "adjudication": dict(adjudication),
        "disagreement": disagreement,
    }


def parse_dataset(raw: dict[str, Any]) -> GoldLabelDataset:
    """校验导入 JSON：每条须有 case_id；薄切片须双标+第三人；拒绝运营完成/全量标志。"""
    if not isinstance(raw, dict):
        raise GoldLabelIoError("数据集须为 JSON 对象")
    dataset_id = str(raw.get("dataset_id") or "").strip()
    if not dataset_id:
        raise GoldLabelIoError("dataset_id 必填")
    if raw.get("gold_ops_complete") is True:
        raise GoldLabelIoError("金标全量运营仍延后，禁止 gold_ops_complete=true")
    if raw.get("dual_annotation_workflow") is True:
        raise GoldLabelIoError("本票不实现双人标注全量工作流")

    schema = str(raw.get("schema") or SCHEMA_ID).strip() or SCHEMA_ID
    is_thin = bool(raw.get("is_gold_thin_slice")) or schema == SCHEMA_ID_THIN_SLICE
    if is_thin:
        schema = SCHEMA_ID_THIN_SLICE

    docs_note = str(raw.get("docs_note") or "").strip()
    if not docs_note:
        docs_note = (
            DEFAULT_THIN_SLICE_DOCS_NOTE if is_thin else DEFAULT_DOCS_NOTE
        )
    _assert_no_completion_claim(docs_note)

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
        annotation: dict[str, Any] | None = None
        if is_thin:
            if "annotation" not in item:
                raise GoldLabelIoError(
                    "金标薄切片每条须含 annotation（双标+第三人）"
                )
            annotation = _parse_annotation(item.get("annotation"))
        elif item.get("annotation") is not None:
            annotation = _parse_annotation(item.get("annotation"))
        records.append(
            GoldLabelRecord(
                case_id=case_id,
                inputs=dict(inputs),
                expected=dict(expected),
                notes=notes,
                annotation=annotation,
            )
        )

    dataset = GoldLabelDataset(
        dataset_id=dataset_id,
        records=records,
        gold_ops_complete=False,
        dual_annotation_workflow=False,
        is_gold_thin_slice=is_thin,
        schema=schema,
        docs_note=docs_note,
        rewrote_from=str(raw.get("rewrote_from") or "REF-CASE-OPENEVALS"),
    )
    # deferred 时拒绝数据集级正面 grounded 宣称字段
    claim = str(raw.get("grounding_claim") or raw.get("h4_claim") or "").strip()
    if claim:
        assert_h4_claim_allowed(dataset.h4_status, claim=claim)
    return dataset


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
    """写入本地 SQLite 金标钩子表（含薄切片 annotation）。"""
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
            annotation=rec.annotation,
            is_gold_thin_slice=dataset.is_gold_thin_slice,
        )
    return GoldLabelImportResult(
        dataset_id=dataset.dataset_id,
        imported_count=len(dataset.records),
        is_gold_thin_slice=dataset.is_gold_thin_slice,
        h4_status=dataset.h4_status,
    )


def export_dataset(
    store: SqliteCaseStore,
    *,
    dataset_id: str | None = None,
    case_id: str | None = None,
) -> GoldLabelDataset:
    """从本地表导出；完成标志始终为 false；附带 h4_status。"""
    rows = store.list_gold_label_records(dataset_id=dataset_id, case_id=case_id)
    records = [
        GoldLabelRecord(
            case_id=str(row["case_id"]),
            inputs=dict(row["inputs"]),
            expected=dict(row["expected"]),
            notes=str(row.get("notes") or ""),
            annotation=(
                dict(row["annotation"])
                if row.get("annotation") is not None
                else None
            ),
        )
        for row in rows
    ]
    export_id = dataset_id or (str(rows[0]["dataset_id"]) if rows else "unspecified")
    is_thin = any(bool(row.get("is_gold_thin_slice")) for row in rows)
    if not is_thin and records and all(r.annotation is not None for r in records):
        # 导出时若行内均有双标 annotation，按薄切片协议集对待
        is_thin = True
    return GoldLabelDataset(
        dataset_id=export_id,
        records=records,
        is_gold_thin_slice=is_thin,
        schema=SCHEMA_ID_THIN_SLICE if is_thin else SCHEMA_ID,
        docs_note=(
            DEFAULT_THIN_SLICE_DOCS_NOTE if is_thin else DEFAULT_DOCS_NOTE
        ),
    )


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
        description=(
            "金标/薄切片数据集导入导出（旁路，非合门禁；"
            "禁止宣称已达标或 ≥300 已完成）"
        )
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
                    "is_gold_thin_slice": exported.is_gold_thin_slice,
                    "h4_status": exported.h4_status,
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

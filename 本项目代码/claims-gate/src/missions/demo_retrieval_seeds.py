"""Demo 检索种子加载与结构校验（票 36 / P-G1）。

硬约束（旁路，非合门禁主缝）：
- 本集是人写冻结的检索评测查询集，用于可证伪 H1/H2；
- 不得称金标，不得冒充双人薄切片金标协议集；
- KB/LLM 造问若有，只进 artifacts/demo_retrieval_seeds/augment/，不得并入主集；
- 默认 CI 只校验冻结结构，不把 Recall 阈值写入 machine_check。

Rewrote from: 人写
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_ID = "claims-gate-demo-retrieval-seeds-v1"
LABEL = "Demo 检索种子"

BUCKET_CLAUSE = "clause_number"
BUCKET_SEMANTIC = "semantic_hard"
BUCKET_ABSTAIN = "abstain_conflict"

BUCKET_COUNTS: dict[str, int] = {
    BUCKET_CLAUSE: 15,
    BUCKET_SEMANTIC: 20,
    BUCKET_ABSTAIN: 5,
}

ABSTAIN_REASONS = frozenset(
    {
        "conflict",
        "handbook_alone",
        "low_confidence",
        "citation_unfaithful",
    }
)

FORBIDDEN_CLAIM_PHRASES = (
    "金标薄切片",
    "本集为金标",
    "本数据集是金标",
    "金标已达标",
)

DEFAULT_DOCS_NOTE = (
    "人写冻结的 Demo 检索种子；非金标；亦非双人薄切片金标协议集；"
    "不得称金标；造问增广须隔离在 augment/；合门禁以 machine_check 为准"
)


class DemoRetrievalSeedsError(ValueError):
    """Demo 检索种子外形不合法。"""


@dataclass(frozen=True)
class DemoRetrievalQuery:
    """单条人写查询：稳定 id + 分桶 + 期望相关条款。"""

    query_id: str
    bucket: str
    query: str
    expected: dict[str, Any] = field(default_factory=dict)
    authorship: str = "human"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "bucket": self.bucket,
            "query": self.query,
            "expected": dict(self.expected),
            "authorship": self.authorship,
            "notes": self.notes,
        }


@dataclass
class DemoRetrievalSeeds:
    """冻结主集外形；恒非金标。"""

    dataset_id: str
    queries: list[DemoRetrievalQuery]
    schema: str = SCHEMA_ID
    label: str = LABEL
    version: str = "1.0"
    is_gold_label: bool = False
    is_gold_thin_slice: bool = False
    docs_note: str = DEFAULT_DOCS_NOTE
    rewrote_from: str = "人写"

    def bucket_counts(self) -> dict[str, int]:
        counts = {k: 0 for k in BUCKET_COUNTS}
        for q in self.queries:
            if q.bucket not in counts:
                raise DemoRetrievalSeedsError(f"未知 bucket: {q.bucket}")
            counts[q.bucket] += 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "dataset_id": self.dataset_id,
            "label": self.label,
            "version": self.version,
            "is_gold_label": False,
            "is_gold_thin_slice": False,
            "docs_note": self.docs_note,
            "rewrote_from": self.rewrote_from,
            "queries": [q.to_dict() for q in self.queries],
        }


def _require_str(payload: dict[str, Any], key: str) -> str:
    """必填字符串字段；缺省或空白即失败（无静默默认）。"""
    if key not in payload:
        raise DemoRetrievalSeedsError(f"缺少必填字段: {key}")
    value = str(payload[key]).strip()
    if not value:
        raise DemoRetrievalSeedsError(f"字段 {key} 不得为空")
    return value


def _assert_no_forbidden_claims(raw_text: str) -> None:
    for phrase in FORBIDDEN_CLAIM_PHRASES:
        if phrase in raw_text:
            raise DemoRetrievalSeedsError(f"主集不得出现宣称短语: {phrase}")


def _parse_query(row: dict[str, Any], *, index: int) -> DemoRetrievalQuery:
    if not isinstance(row, dict):
        raise DemoRetrievalSeedsError(f"queries[{index}] 须为 object")
    try:
        query_id = _require_str(row, "query_id")
        bucket = _require_str(row, "bucket")
        query = _require_str(row, "query")
        authorship = _require_str(row, "authorship")
    except DemoRetrievalSeedsError as exc:
        raise DemoRetrievalSeedsError(f"queries[{index}]: {exc}") from exc
    if bucket not in BUCKET_COUNTS:
        raise DemoRetrievalSeedsError(f"{query_id}: 非法 bucket={bucket!r}")
    if authorship != "human":
        raise DemoRetrievalSeedsError(
            f"{query_id}: 主集 authorship 必须为 human，造问请放 augment/"
        )
    if "expected" not in row or not isinstance(row["expected"], dict):
        raise DemoRetrievalSeedsError(f"{query_id}: expected 须为 object")
    expected = dict(row["expected"])
    if bucket in (BUCKET_CLAUSE, BUCKET_SEMANTIC):
        relevant = expected.get("relevant_clause_items")
        if not isinstance(relevant, list) or not relevant:
            raise DemoRetrievalSeedsError(
                f"{query_id}: {bucket} 须含 expected.relevant_clause_items"
            )
    if bucket == BUCKET_ABSTAIN:
        if expected.get("assist_disposition") != "abstain":
            raise DemoRetrievalSeedsError(
                f"{query_id}: abstain_conflict 须 assist_disposition=abstain"
            )
        reason = expected.get("abstain_reason")
        if reason not in ABSTAIN_REASONS:
            raise DemoRetrievalSeedsError(
                f"{query_id}: abstain_reason 非法: {reason!r}"
            )
    notes = str(row["notes"]) if "notes" in row else ""
    return DemoRetrievalQuery(
        query_id=query_id,
        bucket=bucket,
        query=query,
        expected=expected,
        authorship=authorship,
        notes=notes,
    )


def parse_demo_retrieval_seeds(payload: dict[str, Any]) -> DemoRetrievalSeeds:
    """解析并校验主集结构（恰好 40=15+20+5）。"""
    if not isinstance(payload, dict):
        raise DemoRetrievalSeedsError("根须为 object")
    schema = _require_str(payload, "schema")
    if schema != SCHEMA_ID:
        raise DemoRetrievalSeedsError(f"schema 须为 {SCHEMA_ID}")
    label = _require_str(payload, "label")
    if label != LABEL:
        raise DemoRetrievalSeedsError(f"label 须为 {LABEL!r}")
    dataset_id = _require_str(payload, "dataset_id")
    version = _require_str(payload, "version")
    docs_note = _require_str(payload, "docs_note")
    rewrote_from = _require_str(payload, "rewrote_from")
    if payload.get("is_gold_label") is not False:
        raise DemoRetrievalSeedsError("is_gold_label 必须为 false")
    if payload.get("is_gold_thin_slice") is not False:
        raise DemoRetrievalSeedsError("is_gold_thin_slice 必须为 false")

    rows = payload.get("queries")
    if not isinstance(rows, list):
        raise DemoRetrievalSeedsError("queries 须为数组")
    queries = [_parse_query(row, index=i) for i, row in enumerate(rows)]
    if len(queries) != 40:
        raise DemoRetrievalSeedsError(f"queries 须恰好 40 条，实际 {len(queries)}")

    ids = [q.query_id for q in queries]
    if len(ids) != len(set(ids)):
        raise DemoRetrievalSeedsError("query_id 必须唯一")

    dataset = DemoRetrievalSeeds(
        dataset_id=dataset_id,
        queries=queries,
        schema=schema,
        label=label,
        version=version,
        docs_note=docs_note,
        rewrote_from=rewrote_from,
    )
    counts = dataset.bucket_counts()
    if counts != BUCKET_COUNTS:
        raise DemoRetrievalSeedsError(
            f"分桶计数须为 {BUCKET_COUNTS}，实际 {counts}"
        )
    return dataset


def load_demo_retrieval_seeds(path: Path | str) -> DemoRetrievalSeeds:
    """从冻结 JSON 加载主集；校验污染宣称与结构。"""
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    _assert_no_forbidden_claims(raw)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DemoRetrievalSeedsError(f"JSON 无效: {exc}") from exc
    return parse_demo_retrieval_seeds(payload)


def default_main_path(*, root: Path) -> Path:
    """主集路径：{root}/artifacts/demo_retrieval_seeds/demo_retrieval_seeds.v1.json。"""
    return root / "artifacts" / "demo_retrieval_seeds" / "demo_retrieval_seeds.v1.json"


def list_augment_paths(seeds_dir: Path | str) -> list[Path]:
    """列出隔离增广数据文件；augment/ 目录必须存在（可为空，仅占位说明）。"""
    root = Path(seeds_dir)
    augment = root / "augment"
    if not augment.is_dir():
        raise DemoRetrievalSeedsError(
            f"污染隔离目录不存在: {augment}（须预留 augment/）"
        )
    out: list[Path] = []
    for path in sorted(augment.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".json", ".jsonl"}:
            # 说明文件 / 占位 README 不计；仅数据文件
            out.append(path)
    return out

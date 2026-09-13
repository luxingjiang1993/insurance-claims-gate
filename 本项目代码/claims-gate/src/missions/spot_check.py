"""Judge–human 合成抽检占位：手工表外形 + 一致率计算。

效果评估流水线外形参考 REF-CASE-EVAL-ADVISOR（跑批/报告入口）；
报告字段扩展参考 REF-MISSIONS Validator。

本模块仅占位：支持个人用合成「标注 A / 标注 B / 裁决」对 SC 夹具做手工对照演练。
不要求真实核赔员；不阻塞轨 A 绿门；不把合成表冒充 ≥300 金标运营。

Rewrote from: REF-CASE-EVAL-ADVISOR, REF-MISSIONS
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SpotCheckRow:
    """单行合成抽检：双人标注 + 第三人裁决概念（本期用合成表代替真实核赔）。"""

    case_id: str
    system_decision: str
    synthetic_label_a: str
    synthetic_label_b: str
    synthetic_adjudication: str
    agrees_with_system: bool
    notes: str = ""


def compute_agreement_rate(rows: list[SpotCheckRow]) -> float | None:
    """由已填抽检行计算 Judge–human 一致率占位；空表返回 null。"""
    if not rows:
        return None
    agreed = sum(1 for r in rows if r.agrees_with_system)
    return agreed / len(rows)


def load_spot_check_json(path: Path | str) -> list[SpotCheckRow]:
    """从 JSON 抽检表加载行；要求顶层对象含 rows 数组。"""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "rows" not in raw:
        raise ValueError("spot check JSON 须为含 rows 数组的对象")
    items = raw["rows"]
    if not isinstance(items, list):
        raise ValueError("rows 须为数组")
    rows: list[SpotCheckRow] = []
    for item in items:
        rows.append(
            SpotCheckRow(
                case_id=str(item["case_id"]),
                system_decision=str(item["system_decision"]),
                synthetic_label_a=str(item["synthetic_label_a"]),
                synthetic_label_b=str(item["synthetic_label_b"]),
                synthetic_adjudication=str(item["synthetic_adjudication"]),
                agrees_with_system=bool(item["agrees_with_system"]),
                notes=str(item["notes"]) if "notes" in item else "",
            )
        )
    return rows

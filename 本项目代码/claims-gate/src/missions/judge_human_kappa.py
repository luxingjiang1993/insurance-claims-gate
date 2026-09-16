"""Judge–human agreement / 标者间 Cohen κ（票 50 / P-E5）。

硬约束（旁路，非合门禁主缝）：
- 绑金标薄切片（P-E3）双标 annotation；标者间 κ 可报告；
- H4：忠实率≥0.85 且 κ≥0.60 且 n≥10 且非合成，才可宣称 grounded；
- 合成样例 / 外形样例不得冒充真外聘双标运营；
- 加深 Issue 11 合成抽检占位，不平行重切 2a 主路径；
- 默认 CI 合门禁仍以 missions.checks.machine_check 为准。

Rewrote from: REF-CASE-OPENEVALS
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from missions.gold_label_io import (  # noqa: E402
    GoldLabelDataset,
    THIN_SLICE_MIN_N,
    assess_h4_status,
)
from missions.spot_check import load_spot_check_json  # noqa: E402

REWROTE_FROM = "REF-CASE-OPENEVALS"
PROTOCOL = "inter_annotator_cohen_kappa"
PAIR_METRIC_DEFAULT = "citation_faithful"
KAPPA_GROUNDED_MIN = 0.60
FAITHFULNESS_GROUNDED_MIN = 0.85

# 外形/合成标记：命中则不得宣称真双标 κ 或 grounded
# 注意：勿用单独「占位」（真协议含「角色占位」）
_SYNTHETIC_MARKERS = (
    "外形样例",
    "合成样例",
    "合成抽检",
    "合成标注",
    "非真实",
    "非真外聘",
    "example-only",
    "演示填法",
    "本票仅占位",
)


class KappaEvalError(ValueError):
    """κ / grounded 宣称不合法。"""


@dataclass
class KappaReport:
    """金标薄切片（或合成对照）上的 κ 报告。"""

    n: int
    kappa: float | None
    h4_status: str
    is_synthetic: bool
    grounded_claim_allowed: bool = False
    pair_metric: str = PAIR_METRIC_DEFAULT
    protocol: str = PROTOCOL
    kappa_grounded_min: float = KAPPA_GROUNDED_MIN
    faithfulness_rate: float | None = None
    judge_human_agreement: float | None = None
    observed_agreement: float | None = None
    detail: str = ""
    rewrote_from: str = REWROTE_FROM

    def assert_grounded_claim_allowed(self) -> None:
        """未过 H4 全部门禁时拒绝 grounded 宣称。"""
        if self.grounded_claim_allowed:
            return
        raise KappaEvalError(
            f"禁止宣称 grounded（H4={self.h4_status}；"
            f"n={self.n}；κ={self.kappa}；"
            f"faithfulness_rate={self.faithfulness_rate}；"
            f"is_synthetic={self.is_synthetic}；"
            f"须 n≥{THIN_SLICE_MIN_N}、忠实率≥{FAITHFULNESS_GROUNDED_MIN}、"
            f"κ≥{KAPPA_GROUNDED_MIN} 且非合成）"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "n": self.n,
            "kappa": self.kappa,
            "h4_status": self.h4_status,
            "is_synthetic": self.is_synthetic,
            "grounded_claim_allowed": self.grounded_claim_allowed,
            "pair_metric": self.pair_metric,
            "protocol": self.protocol,
            "kappa_grounded_min": self.kappa_grounded_min,
            "faithfulness_rate": self.faithfulness_rate,
            "judge_human_agreement": self.judge_human_agreement,
            "observed_agreement": self.observed_agreement,
            "detail": self.detail,
            "rewrote_from": self.rewrote_from,
        }


def cohen_kappa(
    labels_a: Sequence[str],
    labels_b: Sequence[str],
) -> float | None:
    """Cohen's κ（名义类别）；空表或长度不一致返回 None。

    κ = (p_o - p_e) / (1 - p_e)；当 p_e=1（无法定义）返回 None。
    """
    if not labels_a or not labels_b:
        return None
    if len(labels_a) != len(labels_b):
        return None
    n = len(labels_a)
    categories = sorted(set(labels_a) | set(labels_b))
    # 列联计数
    counts: dict[tuple[str, str], int] = {}
    for a, b in zip(labels_a, labels_b):
        counts[(a, b)] = counts.get((a, b), 0) + 1

    agree = sum(counts.get((c, c), 0) for c in categories)
    p_o = agree / n

    # 边际
    marg_a = {c: 0 for c in categories}
    marg_b = {c: 0 for c in categories}
    for (a, b), cnt in counts.items():
        marg_a[a] += cnt
        marg_b[b] += cnt
    p_e = sum((marg_a[c] / n) * (marg_b[c] / n) for c in categories)
    if abs(1.0 - p_e) < 1e-15:
        return None
    return (p_o - p_e) / (1.0 - p_e)


def detect_synthetic_dataset(dataset: GoldLabelDataset) -> bool:
    """外形样例 / 合成叙事检测：不得冒充真外聘双标。"""
    blob = " ".join(
        [
            dataset.dataset_id,
            dataset.docs_note,
            dataset.schema,
            *(r.notes for r in dataset.records),
            *(
                str((r.inputs or {}).get("suggestion_span") or "")
                for r in dataset.records
            ),
        ]
    ).lower()
    # 中文标记保留原文大小写不敏感：对中文直接搜原文
    blob_raw = " ".join(
        [
            dataset.dataset_id,
            dataset.docs_note,
            *(r.notes for r in dataset.records),
        ]
    )
    for marker in _SYNTHETIC_MARKERS:
        if marker.lower() in blob or marker in blob_raw:
            return True
    if "example" in dataset.dataset_id.lower():
        return True
    return False


def _label_category(label: dict[str, Any], *, pair_metric: str) -> str:
    """将 annotation label 对象压成可比对类别串。"""
    if pair_metric in label:
        return str(bool(label.get(pair_metric))).lower()
    # 回退：整对象稳定键
    keys = sorted(label.keys())
    parts = [f"{k}={label[k]}" for k in keys]
    return "|".join(parts) if parts else "empty"


def assess_grounded_claim_allowed(
    *,
    n: int,
    faithfulness_rate: float | None,
    kappa: float | None,
    is_synthetic: bool,
) -> bool:
    """H4 全部门：规模 + 忠实率 + κ + 非合成。"""
    if is_synthetic:
        return False
    if n < THIN_SLICE_MIN_N:
        return False
    if faithfulness_rate is None or faithfulness_rate < FAITHFULNESS_GROUNDED_MIN:
        return False
    if kappa is None or kappa < KAPPA_GROUNDED_MIN:
        return False
    return True


def assert_grounded_claim_allowed(
    *,
    n: int,
    faithfulness_rate: float | None,
    kappa: float | None,
    is_synthetic: bool,
) -> None:
    """未过门则抛 KappaEvalError。"""
    if assess_grounded_claim_allowed(
        n=n,
        faithfulness_rate=faithfulness_rate,
        kappa=kappa,
        is_synthetic=is_synthetic,
    ):
        return
    raise KappaEvalError(
        f"禁止宣称 grounded（n={n}；faithfulness_rate={faithfulness_rate}；"
        f"κ={kappa}；is_synthetic={is_synthetic}；"
        f"须 n≥{THIN_SLICE_MIN_N}、忠实率≥{FAITHFULNESS_GROUNDED_MIN}、"
        f"κ≥{KAPPA_GROUNDED_MIN} 且非合成）"
    )


def evaluate_thin_slice_kappa(
    dataset: GoldLabelDataset,
    *,
    synthetic: bool | None = None,
    faithfulness_rate: float | None = None,
    pair_metric: str = PAIR_METRIC_DEFAULT,
) -> KappaReport:
    """在金标薄切片双标上计算标者间 κ；合成不得冒充。"""
    n = len(dataset.records)
    is_synthetic = (
        bool(synthetic)
        if synthetic is not None
        else detect_synthetic_dataset(dataset)
    )
    h4 = assess_h4_status(n)

    labels_a: list[str] = []
    labels_b: list[str] = []
    judge_hits = 0
    judge_scored = 0
    skipped = 0
    for rec in dataset.records:
        ann = rec.annotation
        if not isinstance(ann, dict):
            skipped += 1
            continue
        la = ann.get("label_a")
        lb = ann.get("label_b")
        if not isinstance(la, dict) or not isinstance(lb, dict):
            skipped += 1
            continue
        ca = _label_category(la, pair_metric=pair_metric)
        cb = _label_category(lb, pair_metric=pair_metric)
        labels_a.append(ca)
        labels_b.append(cb)

        # Judge–human：系统 expected vs 第三人裁决（加深 Issue 11 一致率外形）
        expected = rec.expected or {}
        if pair_metric in expected and isinstance(ann.get("adjudication"), dict):
            sys_cat = str(bool(expected.get(pair_metric))).lower()
            # 裁决可直接带 citation_faithful，或 final=agree 表示与 expected 一致
            adj = ann["adjudication"]
            if pair_metric in adj:
                hum_cat = str(bool(adj.get(pair_metric))).lower()
            else:
                final = str(adj.get("final") or "").lower()
                if final in {"agree", "consensus", "accept"}:
                    hum_cat = sys_cat
                elif final in {"disagree", "reject"}:
                    hum_cat = "true" if sys_cat == "false" else "false"
                else:
                    hum_cat = None
            if hum_cat is not None:
                judge_scored += 1
                if hum_cat == sys_cat:
                    judge_hits += 1

    kappa = cohen_kappa(labels_a, labels_b) if labels_a else None
    observed: float | None
    if labels_a:
        observed = sum(1 for a, b in zip(labels_a, labels_b) if a == b) / len(
            labels_a
        )
    else:
        observed = None

    jha: float | None
    if judge_scored == 0:
        jha = None
    else:
        jha = judge_hits / judge_scored

    # 未显式传入忠实率时，合成/不足规模不得用 κ 自洽冒充 grounded
    allowed = assess_grounded_claim_allowed(
        n=n,
        faithfulness_rate=faithfulness_rate,
        kappa=kappa,
        is_synthetic=is_synthetic,
    )

    detail_parts = [
        f"标者间 κ 协议={PROTOCOL}",
        f"pair_metric={pair_metric}",
        f"成对 {len(labels_a)}/{n}",
        f"跳过 {skipped}",
    ]
    if is_synthetic:
        detail_parts.append("合成/外形样例：不得冒充真外聘双标或宣称 grounded")
    if kappa is None:
        detail_parts.append("κ 不可报告（样本不足或 p_e 退化）")

    return KappaReport(
        n=n,
        kappa=kappa,
        h4_status=h4,
        is_synthetic=is_synthetic,
        grounded_claim_allowed=allowed,
        pair_metric=pair_metric,
        faithfulness_rate=faithfulness_rate,
        judge_human_agreement=jha,
        observed_agreement=observed,
        detail="；".join(detail_parts),
    )


def load_spot_check_as_synthetic_kappa(path: Path | str) -> KappaReport:
    """Issue 11 合成抽检表 → 强制 synthetic 的 κ 报告（演示填法，非金标）。"""
    rows = load_spot_check_json(path)
    labels_a = [r.synthetic_label_a for r in rows]
    labels_b = [r.synthetic_label_b for r in rows]
    kappa = cohen_kappa(labels_a, labels_b)
    n = len(rows)
    observed = (
        sum(1 for a, b in zip(labels_a, labels_b) if a == b) / n if n else None
    )
    jha = None
    if n:
        jha = sum(1 for r in rows if r.agrees_with_system) / n
    return KappaReport(
        n=n,
        kappa=kappa,
        h4_status=assess_h4_status(n),
        is_synthetic=True,
        grounded_claim_allowed=False,
        pair_metric="synthetic_label",
        judge_human_agreement=jha,
        observed_agreement=observed,
        detail=(
            "合成抽检占位（Issue 11 加深）：不得冒充金标薄切片真双标；"
            "禁止宣称 grounded"
        ),
    )


def main(argv: list[str] | None = None) -> int:
    """约定入口：python -m missions.judge_human_kappa run --file ..."""
    import argparse

    from missions.gold_label_io import load_dataset_file

    parser = argparse.ArgumentParser(description="金标薄切片 κ 旁路（非合门禁）")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run_p = sub.add_parser("run", help="对薄切片 JSON 报告 κ")
    run_p.add_argument(
        "--file",
        type=Path,
        default=Path("artifacts/gold_thin_slice/gold_thin_slice.v1.example.json"),
    )
    run_p.add_argument(
        "--synthetic",
        action="store_true",
        help="强制标记为合成（不得宣称 grounded）",
    )
    args = parser.parse_args(argv)
    if args.cmd == "run":
        ds = load_dataset_file(args.file)
        report = evaluate_thin_slice_kappa(
            ds,
            synthetic=True if args.synthetic else None,
        )
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""S2/nightly：在冻结 Demo 检索种子上跑 Recall@K / MRR，对照 H1/H2。

用法（在 claims-gate 根目录）::

    python scripts/run_recall_metrics_s2.py
    python scripts/run_recall_metrics_s2.py --out artifacts/reports/recall_s2.json

退出码：0=H1 且 H2 过门；非 0=质量旁路失败（不红轨 A / 不进 machine_check）。

Rewrote from: REF-CASE-RECALL
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from missions.recall_eval_runner import (  # noqa: E402
    EVAL_RETRIEVAL_PROFILE,
    run_frozen_seed_recall,
    write_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="冻结集 Recall@K/MRR（S2/nightly，旁路合门禁）"
    )
    parser.add_argument(
        "--seeds",
        type=Path,
        default=ROOT
        / "artifacts"
        / "demo_retrieval_seeds"
        / "demo_retrieval_seeds.v1.json",
        help="冻结 Demo 检索种子 JSON",
    )
    parser.add_argument(
        "--kb",
        type=Path,
        default=ROOT / "knowledge_base",
        help="知识库根目录",
    )
    parser.add_argument(
        "--profile",
        default=EVAL_RETRIEVAL_PROFILE,
        help="检索 profile（默认 demo_seed_eval）",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="召回截断 K（H2 用 Recall@5）",
    )
    parser.add_argument(
        "--vector",
        action="store_true",
        help="启用向量腿（默认关闭以保证可复现）",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "artifacts" / "reports" / "recall_metrics_s2.json",
        help="报告输出路径",
    )
    args = parser.parse_args(argv)

    report = run_frozen_seed_recall(
        seeds_path=args.seeds,
        kb_root=args.kb,
        retrieval_profile=args.profile,
        top_k=args.top_k,
        vector_enabled=bool(args.vector),
    )
    out = write_report(report, args.out)
    summary = {
        "out": str(out),
        "exit_code": report.exit_code,
        "h1_recall_at_1": report.h1_recall_at_1,
        "h1_passed": report.gates.h1_passed if report.gates else False,
        "h2_recall_at_5": report.h2_recall_at_5,
        "h2_mrr": report.h2_mrr,
        "h2_passed": report.gates.h2_passed if report.gates else False,
        "blocks_track_a_gate": report.blocks_track_a_gate,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())

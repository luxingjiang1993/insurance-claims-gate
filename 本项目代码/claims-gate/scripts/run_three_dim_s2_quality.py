#!/usr/bin/env python3
"""S2/nightly：三维质量旁路（检索 / 引用忠实 / 建议可用性）。

用法（在 claims-gate 根目录）::

    python scripts/run_three_dim_s2_quality.py
    python scripts/run_three_dim_s2_quality.py --out artifacts/reports/three_dim_s2.json

退出码：0=三维均过门；非 0=质量旁路失败（不红轨 A / 不进 machine_check）。
LLM 打分不得当唯一主指标。

Rewrote from: REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR
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

from missions.three_dim_s2_quality import (  # noqa: E402
    run_three_dim_s2,
    write_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="三维 S2 质量旁路（检索/忠实/可用性；不红轨 A）"
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
        "--faithfulness",
        type=Path,
        default=ROOT / "artifacts" / "citation_faithfulness" / "fixtures.v1.json",
        help="引用忠实夹具",
    )
    parser.add_argument(
        "--usability",
        type=Path,
        default=ROOT / "artifacts" / "suggestion_usability" / "fixtures.v1.json",
        help="建议可用性夹具",
    )
    parser.add_argument(
        "--kb",
        type=Path,
        default=ROOT / "knowledge_base",
        help="知识库根目录",
    )
    parser.add_argument(
        "--vector",
        action="store_true",
        help="启用向量腿（默认关闭以保证可复现）",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "artifacts" / "reports" / "three_dim_s2_quality.json",
        help="报告输出路径",
    )
    args = parser.parse_args(argv)

    report = run_three_dim_s2(
        seeds_path=args.seeds,
        kb_root=args.kb,
        faithfulness_fixtures_path=args.faithfulness,
        usability_fixtures_path=args.usability,
        vector_enabled=bool(args.vector),
    )
    out = write_report(report, args.out)
    summary = {
        "out": str(out),
        "exit_code": report.exit_code,
        "all_passed": report.all_passed,
        "llm_judge_as_primary": report.llm_judge_as_primary,
        "blocks_track_a_gate": report.blocks_track_a_gate,
        "dimensions": {
            name: {
                "passed": dim.get("passed"),
                "primary_metric": dim.get("primary_metric"),
                "llm_judge_as_primary": dim.get("llm_judge_as_primary"),
            }
            for name, dim in report.dimensions.items()
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())

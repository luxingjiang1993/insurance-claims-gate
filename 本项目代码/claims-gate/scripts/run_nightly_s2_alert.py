#!/usr/bin/env python3
"""S2/nightly：三维质量旁路失败告警（日志 + 本地产物；不强制邮件）。

用法（在 claims-gate 根目录）::

    python scripts/run_nightly_s2_alert.py
    python scripts/run_nightly_s2_alert.py --alert-out artifacts/reports/nightly_s2_alert.json

退出码：0=质量过门；非 0=质量旁路失败（便于调度告警；**不红轨 A** / 不进 machine_check）。

Rewrote from: REF-MISSIONS
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from missions.nightly_s2_alert import run_nightly_s2_alert  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(
        description="夜间 S2 质量门失败告警（旁路，不红轨 A）"
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
        "--quality-out",
        type=Path,
        default=ROOT / "artifacts" / "reports" / "three_dim_s2_quality.json",
        help="三维质量报告路径",
    )
    parser.add_argument(
        "--alert-out",
        type=Path,
        default=ROOT / "artifacts" / "reports" / "nightly_s2_alert.json",
        help="告警产物路径（本地可观测；不强制邮件）",
    )
    args = parser.parse_args(argv)

    result = run_nightly_s2_alert(
        seeds_path=args.seeds,
        kb_root=args.kb,
        faithfulness_fixtures_path=args.faithfulness,
        usability_fixtures_path=args.usability,
        vector_enabled=bool(args.vector),
        quality_out=args.quality_out,
        alert_out=args.alert_out,
    )
    summary = {
        "quality_out": str(result.quality_report_path),
        "alert_out": str(result.alert_artifact_path),
        "exit_code": result.exit_code,
        "alert_raised": result.alert.alert_raised,
        "severity": result.alert.severity,
        "failed_dimensions": result.alert.failed_dimensions,
        "blocks_track_a_gate": result.alert.blocks_track_a_gate,
        "gate_role": result.alert.gate_role,
        "docs_note": result.alert.docs_note,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""S2/nightly：冻结 Demo 检索种子 Recall@K/MRR；G2 双剖面并列报告。

用法（在 claims-gate 根目录）::

    python scripts/run_recall_metrics_s2.py
    python scripts/run_recall_metrics_s2.py --dual
    python scripts/run_recall_metrics_s2.py --profile demo_seed_eval
    python scripts/run_recall_metrics_s2.py --profile pilot_cloud_embed --vector
    python scripts/run_recall_metrics_s2.py --out artifacts/reports/recall_s2.json

默认跑双剖面（demo_seed_eval 向量关 + pilot_cloud_embed 向量开）。
先剖面后数字；禁止无标签短路 1.00 冒充语义满分。

退出码：0=所选剖面 H1 且 H2 过门；非 0=质量旁路失败（不红轨 A / 不进 machine_check）。

Rewrote from: REF-CASE-RECALL；REF-CASE-KB
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
    PROFILE_DEMO_SEED_EVAL,
    PROFILE_PILOT_CLOUD_EMBED,
    MissingVectorSearcherError,
    run_dual_retrieval_profiles,
    run_frozen_seed_recall,
    write_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="冻结集 Recall@K/MRR（S2/nightly，双剖面旁路合门禁）"
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
        "--dual",
        action="store_true",
        default=True,
        help="并列跑 demo_seed_eval + pilot_cloud_embed（默认）",
    )
    parser.add_argument(
        "--single",
        action="store_true",
        help="只跑单一 --profile（关闭默认双剖面）",
    )
    parser.add_argument(
        "--profile",
        default=EVAL_RETRIEVAL_PROFILE,
        help="单剖面模式的检索 profile（默认 demo_seed_eval）",
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
        help="单剖面模式启用向量腿（pilot_cloud_embed 建议开）",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "artifacts" / "reports" / "recall_metrics_s2.json",
        help="报告输出路径",
    )
    args = parser.parse_args(argv)
    use_dual = bool(args.dual) and not bool(args.single)

    if use_dual:
        report = run_dual_retrieval_profiles(
            seeds_path=args.seeds,
            kb_root=args.kb,
            top_k=args.top_k,
        )
        out = write_report(report, args.out)
        demo = report.demo_seed_eval
        pilot = report.pilot_cloud_embed
        summary = {
            "out": str(out),
            "report_kind": "dual_retrieval_profile",
            "exit_code": report.exit_code,
            "profiles": {
                PROFILE_DEMO_SEED_EVAL: {
                    "vector_enabled": demo.vector_enabled,
                    "h1_recall_at_1": demo.h1_recall_at_1,
                    "h1_passed": demo.gates.h1_passed if demo.gates else False,
                    "h2_recall_at_5": demo.h2_recall_at_5,
                    "h2_mrr": demo.h2_mrr,
                    "h2_passed": demo.gates.h2_passed if demo.gates else False,
                },
                PROFILE_PILOT_CLOUD_EMBED: {
                    "vector_enabled": pilot.vector_enabled,
                    "h1_recall_at_1": pilot.h1_recall_at_1,
                    "h1_passed": pilot.gates.h1_passed if pilot.gates else False,
                    "h2_recall_at_5": pilot.h2_recall_at_5,
                    "h2_mrr": pilot.h2_mrr,
                    "h2_passed": pilot.gates.h2_passed if pilot.gates else False,
                },
            },
            "honesty_note": report.honesty_note,
            "blocks_track_a_gate": report.blocks_track_a_gate,
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return report.exit_code

    # 单剖面：pilot 默认开向量；demo 默认关（可用 --vector 覆盖）
    vector_enabled = bool(args.vector)
    if args.profile == PROFILE_PILOT_CLOUD_EMBED and not args.vector:
        vector_enabled = True
    if args.profile == PROFILE_DEMO_SEED_EVAL and not args.vector:
        vector_enabled = False

    try:
        report = run_frozen_seed_recall(
            seeds_path=args.seeds,
            kb_root=args.kb,
            retrieval_profile=args.profile,
            top_k=args.top_k,
            vector_enabled=vector_enabled,
            allow_missing_vector_skip=False,
        )
    except MissingVectorSearcherError as exc:
        print(
            json.dumps(
                {
                    "error": "missing_vector_searcher",
                    "retrieval_profile": args.profile,
                    "message": str(exc),
                    "exit_code": 2,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    out = write_report(report, args.out)
    summary = {
        "out": str(out),
        "retrieval_profile": report.retrieval_profile,
        "vector_enabled": report.vector_enabled,
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

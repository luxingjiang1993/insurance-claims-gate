"""Solo Demo：SC-01/02/03 HTTP 黑盒一键验收（给人看的 pass/fail）。

Rewrote from: REF-MISSIONS（Validator/TestClient 黑盒 + machine_check 合门禁语义）

合门禁仍以 pytest / machine_check 为准；本模块是个人开发验收 Demo，
不引入 L3/支付，不依赖真实 OCR/核心。
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# 保证 missions / claims_api 在 PYTHONPATH 未设时仍可被本模块加载
_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fastapi.testclient import TestClient

from missions.checks import run_machine_check
from missions.models import MachineCheck

# 主路径：与 tests/test_sc0*.py 同一 machine_check 语义
_MAIN_SCENARIOS: list[tuple[str, str, dict[str, Any]]] = [
    ("SC-01", "sc01_one_shot_supplement_approve", {"case_id": "CLM-SC01-001"}),
    ("SC-02", "sc02_exclusion_reject_latch", {"case_id": "CLM-SC02-001"}),
    ("SC-03", "sc03_endorsement_stack_reduction", {"case_id": "CLM-SC03-001"}),
]

# 可选负例：拆轮拒绝 / 无人闸 EXTERNAL_NOTIFY（检查本身 ok=正确拒绝）
_EXTRA_SCENARIOS: list[tuple[str, str, dict[str, Any]]] = [
    ("SC-01-split-round", "one_shot_split_round_rejected", {"case_id": "CLM-SC01-001"}),
    (
        "SC-02-latch-required",
        "sc02_external_notify_requires_latch",
        {"case_id": "CLM-SC02-001"},
    ),
]


@dataclass(frozen=True)
class DemoRow:
    """单条场景结果。"""

    label: str
    check_type: str
    ok: bool
    detail: str


@dataclass(frozen=True)
class DemoResult:
    """整次 Demo 汇总。"""

    rows: list[DemoRow]
    exit_code: int

    def format_report(self) -> str:
        """简明给人看的 pass/fail 文本。"""
        lines: list[str] = ["claims-gate Solo SC Demo", "-" * 40]
        for row in self.rows:
            mark = "PASS" if row.ok else "FAIL"
            lines.append(f"[{mark}] {row.label}  ({row.check_type})")
            if not row.ok and row.detail:
                lines.append(f"       {row.detail}")
        passed = sum(1 for r in self.rows if r.ok)
        total = len(self.rows)
        lines.append("-" * 40)
        lines.append(f"summary: {passed}/{total} passed  exit={self.exit_code}")
        return "\n".join(lines)


def run_sc_demo(*, include_extras: bool = False) -> DemoResult:
    """对 SC 主路径（及可选负例）走 TestClient + machine_check。"""
    from claims_api.api import app, reset_service

    scenarios = list(_MAIN_SCENARIOS)
    if include_extras:
        scenarios.extend(_EXTRA_SCENARIOS)

    rows: list[DemoRow] = []
    for label, check_type, params in scenarios:
        reset_service()
        client = TestClient(app)
        outcome = run_machine_check(
            client,
            MachineCheck(type=check_type, params=params),
        )
        rows.append(
            DemoRow(
                label=label,
                check_type=check_type,
                ok=bool(outcome.ok),
                detail=str(outcome.detail or ""),
            )
        )

    exit_code = 0 if all(r.ok for r in rows) else 1
    return DemoResult(rows=rows, exit_code=exit_code)


def main(argv: list[str] | None = None) -> int:
    """脚本入口：python -m claims_api.demo_sc。"""
    parser = argparse.ArgumentParser(
        description="Solo Demo：SC-01/02/03 HTTP 黑盒 pass/fail（个人验收）"
    )
    parser.add_argument(
        "--extras",
        action="store_true",
        help="额外跑拆轮拒绝 / 无人闸 EXTERNAL_NOTIFY 负例",
    )
    args = parser.parse_args(argv)
    result = run_sc_demo(include_extras=bool(args.extras))
    print(result.format_report())
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())

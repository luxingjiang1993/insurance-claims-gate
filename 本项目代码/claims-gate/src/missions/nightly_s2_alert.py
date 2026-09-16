"""夜间 S2 质量门失败告警（票 48 / P-E6）。

硬约束：
- 失败可观测：默认日志 WARNING + 本地 JSON 产物；不强制邮件；
- 永不 fail 默认合门禁 / 永不红轨 A；不进 machine_check；
- 旁路退出码可非 0 便于夜间调度告警，但 gate_role 标明 bypass。

Rewrote from: REF-MISSIONS（N1 精神未修宪：质量旁路诚实告警，不绑架轨 A）
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from missions.recall_eval_runner import RetrieveFn
from missions.three_dim_s2_quality import (
    ThreeDimS2Report,
    run_three_dim_s2,
    write_report,
)

logger = logging.getLogger(__name__)

GATE_ROLE = "assist_quality_s2_bypass_alert"
REWROTE_FROM = "REF-MISSIONS"
DOCS_NOTE = (
    "S2/nightly 质量门失败告警：本地 JSON + 日志可观测；"
    "不强制邮件；旁路不红轨 A / 不进 machine_check"
)


@dataclass
class NightlyS2Alert:
    """可机读夜间告警记录。"""

    alert_raised: bool
    severity: str
    failed_dimensions: list[str] = field(default_factory=list)
    source_exit_code: int = 0
    source_gate_role: str = "assist_quality_s2_bypass"
    blocks_track_a_gate: bool = False
    gate_role: str = GATE_ROLE
    rewrote_from: str = REWROTE_FROM
    docs_note: str = DOCS_NOTE
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_raised": self.alert_raised,
            "severity": self.severity,
            "failed_dimensions": list(self.failed_dimensions),
            "source_exit_code": self.source_exit_code,
            "source_gate_role": self.source_gate_role,
            "blocks_track_a_gate": self.blocks_track_a_gate,
            "gate_role": self.gate_role,
            "rewrote_from": self.rewrote_from,
            "docs_note": self.docs_note,
            "message": self.message,
        }


@dataclass
class NightlyS2AlertRun:
    """一次 nightly 跑批：质量报告 + 告警产物。"""

    alert: NightlyS2Alert
    quality_report: ThreeDimS2Report
    quality_report_path: Path
    alert_artifact_path: Path

    @property
    def exit_code(self) -> int:
        # 旁路：质量失败 → 非 0 便于调度告警；不表示轨 A 红
        return self.quality_report.exit_code


def _failed_dimensions(payload: dict[str, Any]) -> list[str]:
    dims = payload.get("dimensions") or {}
    failed: list[str] = []
    if isinstance(dims, dict):
        for name, dim in dims.items():
            if isinstance(dim, dict) and not bool(dim.get("passed")):
                failed.append(str(name))
            elif not isinstance(dim, dict) and not bool(dim):
                failed.append(str(name))
    return failed


def evaluate_s2_alert(report: ThreeDimS2Report | dict[str, Any]) -> NightlyS2Alert:
    """根据三维（或同构）质量报告判定是否升起告警。

    blocks_track_a_gate 恒为 False：告警不得阻断轨 A / machine_check。
    """
    if isinstance(report, ThreeDimS2Report):
        payload = report.to_dict()
    else:
        payload = dict(report)

    all_passed = bool(payload.get("all_passed"))
    exit_code = int(payload.get("exit_code", 0 if all_passed else 1))
    failed = _failed_dimensions(payload)
    raised = (not all_passed) or exit_code != 0 or bool(failed)

    if raised:
        dims_txt = ",".join(failed) if failed else "unknown"
        message = (
            f"[claims-gate S2 nightly] 质量门失败告警（旁路，不红轨 A）；"
            f"failed_dimensions={dims_txt}; exit_code={exit_code}"
        )
        severity = "s2_quality_fail"
    else:
        message = (
            "[claims-gate S2 nightly] 质量门通过；无告警（旁路，不进 machine_check）"
        )
        severity = "none"

    return NightlyS2Alert(
        alert_raised=raised,
        severity=severity,
        failed_dimensions=failed,
        source_exit_code=exit_code,
        source_gate_role=str(
            payload.get("gate_role") or "assist_quality_s2_bypass"
        ),
        blocks_track_a_gate=False,
        message=message,
    )


def write_alert_artifact(alert: NightlyS2Alert, path: Path | str) -> Path:
    """写出 UTF-8 JSON 告警产物（本地可观测；不强制邮件）。"""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(alert.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return out


def emit_alert_log(
    alert: NightlyS2Alert,
    *,
    log: logging.Logger | None = None,
) -> str:
    """写可检测日志行；失败用 WARNING，通过用 INFO。返回消息文本。"""
    log = log or logger
    msg = alert.message or (
        "[claims-gate S2 nightly] 质量旁路状态未知"
    )
    if alert.alert_raised:
        log.warning(msg)
    else:
        log.info(msg)
    return msg


def run_nightly_s2_alert(
    *,
    seeds_path: Path | str | None = None,
    kb_root: Path | str | None = None,
    faithfulness_fixtures_path: Path | str | None = None,
    usability_fixtures_path: Path | str | None = None,
    retrieve_fn: RetrieveFn | None = None,
    vector_enabled: bool = False,
    quality_out: Path | str | None = None,
    alert_out: Path | str | None = None,
) -> NightlyS2AlertRun:
    """跑三维 S2 旁路；失败则升起告警产物 + 日志；永不阻断轨 A。"""
    root = Path(__file__).resolve().parents[2]
    q_path = Path(quality_out) if quality_out else (
        root / "artifacts" / "reports" / "three_dim_s2_quality.json"
    )
    a_path = Path(alert_out) if alert_out else (
        root / "artifacts" / "reports" / "nightly_s2_alert.json"
    )

    quality = run_three_dim_s2(
        seeds_path=seeds_path,
        kb_root=kb_root,
        faithfulness_fixtures_path=faithfulness_fixtures_path,
        usability_fixtures_path=usability_fixtures_path,
        vector_enabled=vector_enabled,
        retrieve_fn=retrieve_fn,
    )
    write_report(quality, q_path)
    alert = evaluate_s2_alert(quality)
    write_alert_artifact(alert, a_path)
    emit_alert_log(alert)
    return NightlyS2AlertRun(
        alert=alert,
        quality_report=quality,
        quality_report_path=q_path,
        alert_artifact_path=a_path,
    )

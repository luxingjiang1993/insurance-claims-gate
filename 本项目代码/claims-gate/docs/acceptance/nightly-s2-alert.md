# Acceptance — Issue 48 / P-E6：夜间 S2 质量门失败告警

**Status:** accepted（旁路；不进默认合门禁）  
**Rewrote from:** REF-MISSIONS  
**SPEC：** `SPEC-02B-P-ASSIST-QUALITY` β DoD · 夜间告警（决策 15）

## 范围

| 能力 | 行为 |
|------|------|
| 失败可观测 | 质量失败 → `alert_raised=true`；本地 JSON + 日志 WARNING |
| 成功可观测 | 过门 → `alert_raised=false`；仍落盘告警产物（severity=`none`） |
| 不红轨 A | `blocks_track_a_gate` 恒为 `false`；不进 `machine_check` |
| 通道 | 默认日志 + 本地产物；**不强制邮件** |

## 复现命令

```text
cd 本项目代码/claims-gate
python scripts/run_nightly_s2_alert.py
pytest -q tests/test_nightly_s2_alert.py
pytest -m assist_quality -q tests/test_nightly_s2_alert.py
```

报告默认：
- 质量：`artifacts/reports/three_dim_s2_quality.json`（复用票 47）
- 告警：`artifacts/reports/nightly_s2_alert.json`

夜间调度可读非 0 退出码做告警；**不得**把该退出码并入默认 `pytest -q` / S0。

## 默认绿隔离

`pytest.ini` 的 `addopts` 含 `not assist_quality`。S0 契约测只断言告警外形与「不红轨 A」，不要求三维全绿。

## 诚实边界

- 本验收证明失败可检测/可告警且不绑架轨 A；不宣称邮件/PagerDuty 已上线。
- 不实现 γ；不把质量阈值写入 `machine_check`。

# 48: 夜间 S2 质量门失败告警；不红轨 A

**github_issue:** #35

**Status:** resolved

**Blocked by:** 44, 47

**wave:** 2b-P-β

**spec_id:** SPEC-02B-P-ASSIST-QUALITY

**ref_id:** REF-MISSIONS

**Rewrote from:** N1 精神未修宪

## 优先打开（只读参考）

路径相对于 \历史项目代码供参考/\。交付只写入 \本项目代码/claims-gate/\。

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | 见 ref_id | 加深缺口，勿平行重切 2a 主路径 |
| 2 | \docs/agents/phase2b-depth-planning-backlog.DRAFT.md\ | 已决议 registry |
| 3 | \Managerial System/SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md\ | DoD / 接缝 |

## What to build

S2 质量失败可被检测/告警（默认：日志或本地产物 + 手册说明；不强制邮件）；永不 fail 默认合门禁。

## Acceptance criteria

- [x] 失败可观测
- [x] S0 仍绿
- [x] 手册写清旁路
- [x] handoff 含 Rewrote from:

## Answer

**交付（2026-09-16）：**

- `missions/nightly_s2_alert.py`：`evaluate_s2_alert` / `write_alert_artifact` / `emit_alert_log` / `run_nightly_s2_alert`；`blocks_track_a_gate=false`；默认日志 WARNING + 本地 JSON；不强制邮件
- CLI：`scripts/run_nightly_s2_alert.py` → 质量报告 + `artifacts/reports/nightly_s2_alert.json`；旁路非 0 退出码便于调度，不红轨 A
- 测：`tests/test_nightly_s2_alert.py`（S0 契约 + `-m assist_quality` 失败可告警）
- 验收：`docs/acceptance/nightly-s2-alert.md`；手册 §3.8 + CHANGELOG Unreleased

**复现：** `python scripts/run_nightly_s2_alert.py`；`pytest -q tests/test_nightly_s2_alert.py`  
**Rewrote from:** REF-MISSIONS（N1 精神未修宪）

## Comments

- 2026-09-15：\/to-spec\ 切票；Status=ready-for-agent。
- 2026-09-15：同步 GitHub Issue #35。
- 2026-09-16：实现并关闭；失败可观测；S0 绿；手册写清旁路。

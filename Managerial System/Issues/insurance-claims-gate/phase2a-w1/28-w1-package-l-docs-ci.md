# 28: 套餐 L 验收 + Pilot 手册区分 + 默认 CI 仍绿

**github_issue:** #15

**Status:** ready-for-agent

**Blocked by:** 24, 25, 26, 27

**wave:** W1

**spec_id:** SPEC-02A-W1-PILOT-COMPLETE

**ref_id:** REF-MISSIONS

**Rewrote from:** REF-MISSIONS

## 优先打开（只读参考）

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `docs/user/MAINTENANCE.md` | 手册与 Changelog 更新义务 |
| 2 | `docs/user/USER_GUIDE.md` | W0「演示可无 Key」口径；本票须区分 Pilot |
| 3 | `spec-2a-w1-pilot-complete.md` DoD / 套餐 L | 验收清单边界 |

## What to build

完成 Pilot Complete 收口：套餐 L 验收清单（满配路径 + 关向量降级 + 关 LLM 降级）可执行；更新 `docs/user/` 标明 Pilot 配置要求（须 LangSmith 等）并与 W0 演示降级区分；确认默认 `pytest -q` 仍不要求 LangSmith/LLM 且 S0 绿。对外宣称须带「W1 / Pilot Complete」波次名，不得暗示 Eval Ops（W2）已上线。

## Acceptance criteria

- [ ] 套餐 L 清单存在且可按步骤验收（满配 / 关向量 / 关 LLM）；不强制进默认 pytest
- [ ] `USER_GUIDE.md` / `CHANGELOG.md` 区分「演示可无 Key」与「Pilot 须 LangSmith（等）」
- [ ] 默认 `pytest -q` 无 LangSmith、无 LLM 仍全绿；S2 可选测有标记
- [ ] 可对照 `spec-2a-w1-pilot-complete.md` DoD Checklist 勾选关闭 W1（实现侧）
- [ ] 文案不宣称排行榜/多人评测台已上线
- [ ] handoff 含 `Rewrote from: REF-MISSIONS`

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w1/`。
- 2026-09-14：同步 GitHub Issue #15。

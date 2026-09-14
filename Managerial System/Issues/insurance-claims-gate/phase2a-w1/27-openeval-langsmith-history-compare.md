# 27: OpenEval 旁路 ↔ LangSmith 实验历史对比

**github_issue:** #14

**Status:** ready-for-agent

**Blocked by:** 26

**wave:** W1

**spec_id:** SPEC-02A-W1-PILOT-COMPLETE

**ref_id:** REF-MISSIONS, REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR

**Rewrote from:** REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR, REF-MISSIONS

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `CASE-openevals使用/` | OpenEval 旁路跑法 |
| 2 | `CASE-投顾AI助手（效果评估）/` | 实验/历史对比外形 |
| 3 | Phase 1 票 10 旁路入口 | 不替代 machine_check |

## What to build

打通 OpenEval 旁路：跑通最小数据集 run，并将实验结果写入/关联 LangSmith，使试点方可做**实验历史对比**外形。不含排行榜与多人协作（属 W2）。OpenEval 不得替代 `machine_check`；默认 CI 不跑真 LLM/真 LangSmith。

## Acceptance criteria

- [ ] OpenEval 旁路可跑通约定最小集（S2 / 可选入口）
- [ ] 结果在 LangSmith 可见，并具备实验历史对比外形（非排行榜）
- [ ] 明确不替代 `machine_check`；S0 默认绿不受影响
- [ ] 不含排行榜、不含多人协作评测台
- [ ] handoff 含 `Rewrote from:` 所用 REF

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w1/`。
- 2026-09-14：同步 GitHub Issue #14。

# 27: OpenEval 旁路 ↔ LangSmith 实验历史对比

**github_issue:** #14

**Status:** resolved

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

- [x] OpenEval 旁路可跑通约定最小集（S2 / 可选入口）
- [x] 结果在 LangSmith 可见，并具备实验历史对比外形（非排行榜）
- [x] 明确不替代 `machine_check`；S0 默认绿不受影响
- [x] 不含排行榜、不含多人协作评测台
- [x] handoff 含 `Rewrote from:` 所用 REF

## Answer

**交付：**
- `missions/openeval_langsmith.py`：`run_openeval_experiment` / `list_experiment_history`；复用 Issue 10 `DEFAULT_EVAL_SUITE`；可注入 Fake Client；真路径 `RealLangSmithExperimentClient`（dataset + project/reference_dataset）
- 脚本：`python -m missions.openeval_langsmith`
- 默认测：`tests/eval/test_openeval_langsmith_history.py`（S0 隔离 + `eval_bypass` Fake 双实验历史对比）
- S2：`tests/langsmith_integration/test_openeval_experiment_real.py`（真 Key；缺则 skip）
- 用户手册成熟度 Preview；CHANGELOG Unreleased

**S2 / mock 策略（写明）：**
1. **默认/S0：** `FakeLangSmithExperimentClient`（无网络）。**不得**用 mock 冒充 Pilot Complete。
2. **真实验：** `pytest -m langsmith_integration`，需真实 Key；缺则 skip。
3. LangSmith 实验分 / UI **不**替代 `machine_check`；不含排行榜。

`Rewrote from: REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR, REF-MISSIONS`

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w1/`。
- 2026-09-14：同步 GitHub Issue #14。
- 2026-09-15：实现合入；S0 隔离 + Fake 历史对比绿；S2 真 Key 可选。

# 47: 三维 S2：检索 / 引用忠实 / 建议可用性

**github_issue:** #34

**Status:** resolved

**Blocked by:** 44, 46, 42

**wave:** 2b-P-β

**spec_id:** SPEC-02B-P-ASSIST-QUALITY

**ref_id:** REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR

**Rewrote from:** OPENEVALS + EVAL-ADVISOR

## 优先打开（只读参考）

路径相对于 \历史项目代码供参考/\。交付只写入 \本项目代码/claims-gate/\。

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | 见 ref_id | 加深缺口，勿平行重切 2a 主路径 |
| 2 | \docs/agents/phase2b-depth-planning-backlog.DRAFT.md\ | 已决议 registry |
| 3 | \Managerial System/SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md\ | DoD / 接缝 |

## What to build

三维质量旁路：检索、引用忠实、建议可用性；可用性以规则或人工为主；LLM 打分不得当唯一主指标。

## Acceptance criteria

- [x] 三维 S2 可跑
- [x] LLM 非唯一主指标
- [x] 不红 S0
- [x] handoff 含 Rewrote from:

## Answer

**交付（2026-09-16）：**

- `missions/suggestion_usability.py`：可用性规则/人工主指标；H5 覆盖率 100%、误起草率≤5%；禁止 LLM 唯一主指标
- `missions/three_dim_s2_quality.py`：三维编排（检索←46 / 忠实←42 / 可用性）；`llm_judge_as_primary=false`；不阻断轨 A
- 夹具：`artifacts/suggestion_usability/fixtures.v1.json`（绑 DRS-A-*）
- CLI：`scripts/run_three_dim_s2_quality.py` → `artifacts/reports/three_dim_s2_quality.json`
- 验收：`docs/acceptance/three-dim-s2-quality.md`；手册 §3.7

**复现：** `python scripts/run_three_dim_s2_quality.py`（exit 0）；`pytest -m assist_quality -q tests/test_three_dim_s2_quality.py`  
**Rewrote from:** REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR

## Comments

- 2026-09-15：\/to-spec\ 切票；Status=ready-for-agent。
- 2026-09-15：同步 GitHub Issue #34。
- 2026-09-16：实现并关闭；S0 绿；S2 `-m assist_quality` 三维过门。

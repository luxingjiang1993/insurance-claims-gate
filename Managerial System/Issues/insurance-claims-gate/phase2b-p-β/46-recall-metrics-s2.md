# 46: 冻结集上 Recall@K / MRR（S2/nightly）

**github_issue:** #33

**Status:** resolved

**Blocked by:** 44, 36, 35

**wave:** 2b-P-β

**spec_id:** SPEC-02B-P-ASSIST-QUALITY

**ref_id:** REF-CASE-RECALL

**Rewrote from:** REF-CASE-RECALL；造问仅增广隔离

## 优先打开（只读参考）

路径相对于 \历史项目代码供参考/\。交付只写入 \本项目代码/claims-gate/\。

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | 见 ref_id | 加深缺口，勿平行重切 2a 主路径 |
| 2 | \docs/agents/phase2b-depth-planning-backlog.DRAFT.md\ | 已决议 registry |
| 3 | \Managerial System/SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md\ | DoD / 接缝 |

## What to build

在 Demo 检索种子上跑 H1/H2 度量（Recall@1、Recall@5/MRR）；S2/nightly；不进默认绿。对照 SPEC 门槛；失败则停堆 γ 组件。

## Acceptance criteria

- [x] 指标可在冻结集复现
- [x] 不进默认 pytest 绿
- [x] 报告对照 H1/H2 门槛
- [x] handoff 含 Rewrote from:

## Answer

**交付（2026-09-16）：**

- `missions/recall_metrics.py`：Recall@K / MRR + H1/H2 门槛对照
- `missions/recall_eval_runner.py`：冻结 Demo 检索种子 runner；`demo_seed_eval` profile；abstain 桶不计 H1/H2
- `scripts/run_recall_metrics_s2.py`：nightly CLI；报告 `artifacts/reports/recall_metrics_s2.json`
- pytest marker `assist_quality`（默认 addopts 排除）
- 条款号短路：精确命中 `type_rank=-1`，避免手册/批单被 prefer_doc_types 淹没
- 验收：`docs/acceptance/recall-metrics-s2.md`；手册 §3.6

**复现：** `python scripts/run_recall_metrics_s2.py`（exit 0；H1 R@1=1.0；H2 R@5=1.0 / MRR≈0.92）  
**Rewrote from:** REF-CASE-RECALL

## Comments

- 2026-09-15：\/to-spec\ 切票；Status=ready-for-agent。
- 2026-09-15：同步 GitHub Issue #33。
- 2026-09-16：实现并关闭；S0 绿；S2 `-m assist_quality` 过门。

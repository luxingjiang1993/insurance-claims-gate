# Acceptance — Issue 46 / P-R3：冻结集 Recall@K / MRR（S2）

**Status:** accepted（旁路；不进默认合门禁）  
**Rewrote from:** REF-CASE-RECALL  
**SPEC：** `SPEC-02B-P-ASSIST-QUALITY` 决策 9（H1/H2）

## 范围

在冻结 Demo 检索种子（40=15+20+5）上复现：

| 假设 | 子集 | 度量 | 门槛 |
|------|------|------|------|
| H1 | `clause_number`（n≥15） | Recall@1 | ≥ 0.95 |
| H2 | `semantic_hard`（n≥20） | Recall@5 **或** MRR | ≥ 0.70 **或** ≥ 0.55 |

`abstain_conflict` 不计 H1/H2（属 H5）。造问增广只允许 `artifacts/demo_retrieval_seeds/augment/`，不得并入计量。

## 复现命令

```text
cd 本项目代码/claims-gate
python scripts/run_recall_metrics_s2.py
pytest -m assist_quality -q tests/test_recall_eval_runner.py
```

默认：`retrieval_profile=demo_seed_eval`、向量腿关闭（关键词/条款号短路可复现）。  
报告默认：`artifacts/reports/recall_metrics_s2.json`。  
退出码非 0 = H1/H2 未过门；**不**红轨 A / **不**进 `machine_check`。

## 默认绿隔离

`pytest.ini` 的 `addopts` 含 `not assist_quality`。默认 `pytest -q` 仍只跑轨 A。

## 诚实边界

- 本验收证明 **H1/H2 有数**（可复现、可对照门槛），不宣称金标 / grounded（H4 仍见薄切片协议）。
- 失败则停堆 γ（RRF / rerank / MultiQuery）；见 SPEC γ 触发附录。
- 作业默认 profile（`clause_v_current`）未因本票放宽；`demo_seed_eval` 仅评测用。

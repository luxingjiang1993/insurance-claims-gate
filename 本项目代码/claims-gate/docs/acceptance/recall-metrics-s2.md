# Acceptance — Issue 46 / P-R3 + Issue 58 / G2：冻结集 Recall@K / MRR（S2 · 双剖面）

**Status:** accepted（旁路；不进默认合门禁）  
**Rewrote from:** REF-CASE-RECALL；REF-CASE-KB（种子边界）  
**SPEC：** `SPEC-02B-P-ASSIST-QUALITY` 决策 9（H1/H2）；`SPEC-02C-LIVE-HONEST-SEAMS` G2

## 范围

在冻结 Demo 检索种子（40=15+20+5）上复现：

| 假设 | 子集 | 度量 | 门槛 |
|------|------|------|------|
| H1 | `clause_number`（n≥15） | Recall@1 | ≥ 0.95 |
| H2 | `semantic_hard`（n≥20） | Recall@5 **或** MRR | ≥ 0.70 **或** ≥ 0.55 |

`abstain_conflict` 不计 H1/H2（属 H5）。造问增广只允许 `artifacts/demo_retrieval_seeds/augment/`，不得并入计量。

## 双剖面（G2 · 必报标签）

| 剖面名 | `vector_enabled` | 含义 |
|--------|------------------|------|
| `demo_seed_eval` | `false` | 可复现基线（关键词 / 条款号短路） |
| `pilot_cloud_embed` | `true` | Pilot 语义剖面（有 embedding Key / 向量索引时可跑） |

**口头 / 文档强制：先报剖面，再报数字。**  
禁止只甩无剖面标签的短路/关键词 **1.00** 冒充语义满分。数字可低于 1.0；H1/H2 门槛语义继承 02B-P。  
γ（rerank 等）**仅当** `pilot_cloud_embed` 上 H2 失败才允许另议；本验收不实现 rerank。

## 复现命令

```text
cd 本项目代码/claims-gate
python scripts/run_recall_metrics_s2.py
python scripts/run_recall_metrics_s2.py --single --profile demo_seed_eval
python scripts/run_recall_metrics_s2.py --single --profile pilot_cloud_embed
pytest -m assist_quality -q tests/test_recall_eval_runner.py
```

默认：双剖面并列写入同一报告（`report_kind=dual_retrieval_profile`，`profiles` 分节各含剖面名）。  
单剖面：`--single --profile …`。  
缺向量索引/embedding Key 时：`pilot_cloud_embed` **诚实跳过**（`skip_reason`，不计关键词满分）；双剖面旁路 exit_code 非 0。有 Key 时先 `rebuild` 再跑 pilot。  
报告默认：`artifacts/reports/recall_metrics_s2.json`。  
退出码非 0 = 所选剖面 H1/H2 未过门或 pilot 跳过；**不**红轨 A / **不**进 `machine_check`。  
evaluate 路径仍零向量 / 零 LLM 依赖。

## 默认绿隔离

`pytest.ini` 的 `addopts` 含 `not assist_quality`。默认 `pytest -q` 仍只跑轨 A。真云 embedding 测旁路，不得绑架默认绿。

## 诚实边界

- 本验收证明 **H1/H2 有数**（可复现、可对照门槛），不宣称金标 / grounded（H4 仍见薄切片协议）。
- `demo_seed_eval` 满分 ≠ Pilot cloud embedding 语义证明。
- 失败则停堆 γ（RRF / rerank / MultiQuery）；见 SPEC γ 触发附录（触发条件 = `pilot_cloud_embed` H2 未过）。
- 作业默认 profile（`clause_v_current`）未因本票放宽；评测剖面仅旁路用。

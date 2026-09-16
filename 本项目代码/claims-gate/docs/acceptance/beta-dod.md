# Phase 2b · P-β DoD 验收 / 演示记录

`Rewrote from: SPEC-02B-P-ASSIST-QUALITY β DoD` · Issue 52 / GitHub #39

本清单关闭 **Claims Assist 可证伪质量（β）**。  
**不**宣称：H4 grounded（当前 `deferred`）；≥300 金标运营；γ（rerank / MultiQuery / fan-out / 灌榜）；流 Q 已上线。

工作目录：`本项目代码/claims-gate/`。默认合门禁：`pytest -q`（无 LLM / 无 LangSmith / 无 cloud embedding Key 仍须绿）。

---

## H1 / H2 — 冻结种子有数（S2 旁路）

**复现：**

```text
python scripts/run_recall_metrics_s2.py
```

报告默认：`artifacts/reports/recall_metrics_s2.json`（可再生成；不进 `machine_check`）。

**记录（2026-09-16 · `retrieval_profile=demo_seed_eval` · 向量腿关闭）：**

| 假设 | 子集 | n | 度量 | 数值 | 门槛 | 过门 |
|------|------|---|------|------|------|------|
| H1 | `clause_number` | 15 | Recall@1 | **1.00** | ≥ 0.95 | 是 |
| H2 | `semantic_hard` | 20 | Recall@5 | **1.00** | ≥ 0.70 | 是 |
| H2 | 同上 | 20 | MRR | **≈ 0.892** | ≥ 0.55（或门） | 是 |

退出码 `0`；`blocks_track_a_gate=false`。本记录为 **关键词/条款号短路可复现基线**（与票 46 默认一致），**不**宣称 Pilot cloud embedding 满配语义已证伪。失败则停堆未触发 γ（见 SPEC γ 附录）。

勾选：`[x] H1/H2 有数`

---

## H4 — 金标线或诚实 deferred

| 项 | 状态 |
|----|------|
| 协议 | 金标薄切片双标 + 第三人角色占位（票 38） |
| κ | 协议可报告（票 50）；外形样例 n=1 → κ 不可作 grounded 依据 |
| 忠实 | 规则/夹具主指标（票 42）；非 LLM-as-judge |
| 当前 | **H4=`deferred`**（n&lt;10；`grounded_claim_allowed=false`） |
| 禁止 | 宣称 grounded / 金标已达标 / ≥300 运营 |

**复现：**

```text
pytest -q tests/test_judge_human_kappa.py
set PYTHONPATH=src
python -m missions.judge_human_kappa run --file artifacts/gold_thin_slice/gold_thin_slice.v1.example.json
```

勾选：`[x] H4 有金标线或诚实 deferred`（本关闭取 **deferred**）

---

## H5 — 拒答金标线（规则夹具 · S2）

**复现：**

```text
python scripts/run_three_dim_s2_quality.py
```

可用性夹具：`artifacts/suggestion_usability/fixtures.v1.json`（绑 Demo 拒答种子 `DRS-A-*` 外形；分母=预登记拒答夹具条；**非** ≥300 运营）。

**记录（2026-09-16 · 三维旁路 suggestion_usability 维）：**

| 度量 | 数值 | 门槛 | 过门 |
|------|------|------|------|
| 预登记拒答覆盖率 | **1.00**（abstain_n=5；绑冻结拒答/冲突桶外形） | 100% | 是 |
| 误起草率 | **0.00** | ≤ 5% | 是 |
| `h5_passed` | true | — | 是 |

主指标 `rules_or_human`；`llm_judge_as_primary=false`。旁路失败不红轨 A。

勾选：`[x] H5 有金标线`（规则/夹具线；预登记人口=夹具 5 条拒答外形；非真用户运营金标）

---

## S0 仍绿

**复现（β 合门禁）：**

```text
pytest -q
```

**记录（2026-09-16）：** `292 passed, 24 deselected`（排除 `track_llm_optional` / `eval_bypass` / `requires_llm` / `langsmith_integration` / `assist_quality`）；无 cloud embedding Key。

勾选：`[x] S0 绿`

---

## 手册诚实（γ / Deferred 未假上线）

- USER_GUIDE：β 用户可见能力已写（H1/H2 旁路、三维 S2、夜间告警、四步预算、κ、连接状态）；H4=`deferred`；γ **未上线**；≥300 / 真连 L2 Deferred；流 Q 未写成已交付。
- CHANGELOG：Unreleased β 项折叠进 Phase 2b · P-β 节。
- 按 `docs/user/MAINTENANCE.md`：阶段 DoD 关闭时已同步。

勾选：`[x] 手册诚实` · `[x] 用户手册已同步`

---

## β DoD 总勾选

| SPEC β 项 | 状态 / 验收指针 |
|-----------|-----------------|
| 条款项切块 + 父条款回填 | 票 45 |
| 冻结种子 Recall@K / MRR（H1/H2） | 票 46 / [`recall-metrics-s2.md`](./recall-metrics-s2.md) / 本文件 |
| 三维 S2（检索 / 忠实 / 可用性） | 票 47 / [`three-dim-s2-quality.md`](./three-dim-s2-quality.md) |
| 夜间 S2 告警旁路 | 票 48 / [`nightly-s2-alert.md`](./nightly-s2-alert.md) |
| assist 步数≤4 · app-owned | 票 49 / [`assist-four-step-budget.md`](./assist-four-step-budget.md) |
| κ / judge-human 实填 | 票 50 / [`judge-human-kappa.md`](./judge-human-kappa.md) |
| 连接状态只读（无 Key） | 票 51；手册 §3.11 |
| H1/H2 有数；H4/H5 金标线或 deferred | 本文件 |
| 用户手册同步；γ 未假上线 | 本文件 |
| 默认 `pytest -q` 绿 | 本文件 S0 |

**关闭后：** 流 P（α+β）DoD closed。流 Q 仍另页 SPEC（解锁条件仅为 α DoD，已满足）。γ 未触发项不得实现。

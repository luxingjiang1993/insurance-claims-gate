# Acceptance — Issue 47 / P-E2：三维 S2 质量旁路

**Status:** accepted（旁路；不进默认合门禁）  
**Rewrote from:** REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR  
**SPEC：** `SPEC-02B-P-ASSIST-QUALITY` β DoD · 三维 S2

## 范围

| 维 | 主指标 | 门槛 / 行为 |
|----|--------|-------------|
| 检索 | `recall_metrics`（票 46） | H1 Recall@1≥0.95；H2 Recall@5≥0.70 **或** MRR≥0.55 |
| 引用忠实 | `rules_fixtures`（票 42） | 夹具全量规则通过；**非** LLM-as-judge；H4 grounded 另见薄切片/κ |
| 建议可用性 | `rules_or_human` | H5：拒答覆盖率 100%；误起草率 ≤5%（分母=预登记拒答条）；人工可并存但不得单独翻绿 |

`llm_judge_as_primary` 恒为 `false`。失败只影响旁路退出码，**不**红轨 A / **不**进 `machine_check`。

## 复现命令

```text
cd 本项目代码/claims-gate
python scripts/run_three_dim_s2_quality.py
pytest -m assist_quality -q tests/test_three_dim_s2_quality.py tests/test_suggestion_usability.py
```

报告默认：`artifacts/reports/three_dim_s2_quality.json`。  
可用性夹具：`artifacts/suggestion_usability/fixtures.v1.json`（绑 DRS-A-* 外形）。

## 默认绿隔离

`pytest.ini` 的 `addopts` 含 `not assist_quality`。默认 `pytest -q` 仍只跑轨 A。

## 诚实边界

- 本验收证明三维旁路可跑且主指标非 LLM；不宣称 H4 grounded（仍见薄切片 + κ）。
- 不实现 γ（rerank / MultiQuery / fan-out / 灌榜）。
- 夜间告警见票 48（本票只交付三维可跑门）。

# Acceptance — Issue 50 / P-E5：Judge–human agreement / κ

**Status:** accepted  
**Rewrote from:** REF-CASE-OPENEVALS  
**SPEC：** `SPEC-02B-P-ASSIST-QUALITY` β DoD · κ 实填（决策 9 H4 / P-E5）  
**加深：** Issue 11 合成抽检占位（非平行重切）

## 范围

| 能力 | 行为 |
|------|------|
| 协议 | 标者间 Cohen κ（`inter_annotator_cohen_kappa`）；默认 pair=`citation_faithful` |
| 绑定 | 金标薄切片 `annotation.label_a` / `label_b`（P-E3） |
| 可报告 | `kappa` / `n` / `observed_agreement` / `judge_human_agreement` / `h4_status` / `is_synthetic` |
| H4 门 | n≥10 **且** 忠实率≥0.85 **且** κ≥0.60 **且** 非合成 → 才可宣称 grounded |
| 合成边界 | 外形样例 / Issue 11 合成抽检 **不得**冒充真外聘双标；`grounded_claim_allowed=false` |
| 合门禁 | **不**写入 `machine_check`；κ 阈值失败不红轨 A |
| 默认测 | 纯函数/契约测进 `pytest -q`（与票 42 忠实规则同形）；无 LLM |

## 复现命令

```text
cd 本项目代码/claims-gate
pytest -q tests/test_judge_human_kappa.py
python -m missions.judge_human_kappa run --file artifacts/gold_thin_slice/gold_thin_slice.v1.example.json
```

## 诚实边界

- 当前仓库外形样例 n&lt;10 → **H4=`deferred`**；κ 可算时仍 **禁止宣称 grounded**。
- 合成抽检表（`artifacts/spot_check_sample_sc01.json`）仅演示填法，**不是**金标线。
- 未注入真外聘双标 n≥10 + 忠实率/κ 达标前，手册与 Demo **不得**称 grounded。
- 本验收证明 κ 协议与数值可报告；不宣称 ≥300 金标运营。

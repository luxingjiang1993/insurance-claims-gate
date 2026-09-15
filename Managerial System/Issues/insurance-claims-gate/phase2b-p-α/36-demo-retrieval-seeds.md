# 36: Demo 检索种子 40 条冻结进 git

**github_issue:** #23

**Status:** resolved

**Blocked by:** —

**wave:** 2b-P-α

**spec_id:** SPEC-02B-P-ASSIST-QUALITY

**ref_id:** 人写

**Rewrote from:** 人写；不用 KB 造问当主集

## 优先打开（只读参考）

路径相对于 \历史项目代码供参考/\。交付只写入 \本项目代码/claims-gate/\。

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | 见 ref_id | 加深缺口，勿平行重切 2a 主路径 |
| 2 | \docs/agents/phase2b-depth-planning-backlog.DRAFT.md\ | 已决议 registry |
| 3 | \Managerial System/SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md\ | DoD / 接缝 |

## What to build

创建并冻结 Demo 检索种子：15 条款号 + 20 语义难例 + 5 拒答/冲突负例（共 40）。版本进 git；污染隔离；文案禁止称金标。架构师可单人编写。

## Acceptance criteria

- [x] 恰好 40 条结构（15+20+5）进仓
- [x] 不得称金标 / 金标薄切片
- [x] 造问若有则隔离增广，非主集
- [x] handoff 含 Rewrote from:

## Answer

`Rewrote from: 人写`

- 主集：`本项目代码/claims-gate/artifacts/demo_retrieval_seeds/demo_retrieval_seeds.v1.json`（label=`Demo 检索种子`；`is_gold_label=false`；`is_gold_thin_slice=false`）。
- 加载器：`missions/demo_retrieval_seeds.py`（结构校验 15+20+5；禁止金标宣称短语）。
- 污染隔离：`artifacts/demo_retrieval_seeds/augment/`（造问增广非主集；默认可空）。
- 测试：S0 `tests/test_demo_retrieval_seeds.py`（9 passed）。Recall@K / MRR 留给 P-R3 / 票 46。

## Comments

- 2026-09-15：\/to-spec\ 切票；Status=ready-for-agent。
- 2026-09-15：同步 GitHub Issue #23。
- 2026-09-15：claimed → implemented → resolved。

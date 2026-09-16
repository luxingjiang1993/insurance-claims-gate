# 42: 引用→断言忠实检查（规则/夹具；非模型自评主指标）

**github_issue:** #29

**Status:** resolved

**Blocked by:** 37, 38

**wave:** 2b-P-α

**spec_id:** SPEC-02B-P-ASSIST-QUALITY

**ref_id:** REF-CASE-OPENEVALS

**Rewrote from:** REF-CASE-OPENEVALS 加深

## 优先打开（只读参考）

路径相对于 \历史项目代码供参考/\。交付只写入 \本项目代码/claims-gate/\。

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | 见 ref_id | 加深缺口，勿平行重切 2a 主路径 |
| 2 | \docs/agents/phase2b-depth-planning-backlog.DRAFT.md\ | 已决议 registry |
| 3 | \Managerial System/SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md\ | DoD / 接缝 |

## What to build

实现引用支撑断言的忠实检查：α 以规则/夹具为主；LLM-as-judge 不得作主指标。绑金标薄切片子集；n 不足则 H4 deferred。

## Acceptance criteria

- [x] 规则/夹具忠实检查可跑
- [x] 非 LLM judge 主指标
- [x] 与 P-E3 边界诚实
- [x] handoff 含 Rewrote from:

## Answer

- 模块：`missions/citation_faithfulness.py` — 规则 `stance_conflict` / `entity_overlap` / `support_registry`；主指标恒 `rules_fixtures`；`llm_judge_as_primary=false`；`evaluate_gold_thin_slice_faithfulness` 绑 P-E3，n&lt;10 → H4=`deferred`，禁止宣称 grounded。
- 夹具：`artifacts/citation_faithfulness/fixtures.v1.json`；CLI：`PYTHONPATH=src python -m missions.citation_faithfulness run --file ...`。
- 挂接：`assist_disposition` 委托 `is_citation_unfaithful_for_assist`（与夹具同缝）。
- S0：`tests/eval/test_citation_faithfulness.py` 契约（不进 `checks.py`）；S2：`@pytest.mark.eval_bypass` 夹具全量。
- Rewrote from: REF-CASE-OPENEVALS

## Comments

- 2026-09-15：\/to-spec\ 切票；Status=ready-for-agent。
- 2026-09-15：同步 GitHub Issue #29。
- 2026-09-16：\/implement\ 落地；Status=resolved。

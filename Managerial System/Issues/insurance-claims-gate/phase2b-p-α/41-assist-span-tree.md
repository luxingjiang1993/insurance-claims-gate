# 41: span 树 retrieve→fuse→gate→llm→(adopt|abstain)→evaluate

**github_issue:** #28

**Status:** resolved

**Blocked by:** 40

**wave:** 2b-P-α

**spec_id:** SPEC-02B-P-ASSIST-QUALITY

**ref_id:** REF-CASE-EVAL-ADVISOR

**Rewrote from:** REF-CASE-EVAL-ADVISOR

## 优先打开（只读参考）

路径相对于 \历史项目代码供参考/\。交付只写入 \本项目代码/claims-gate/\。

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | 见 ref_id | 加深缺口，勿平行重切 2a 主路径 |
| 2 | \docs/agents/phase2b-depth-planning-backlog.DRAFT.md\ | 已决议 registry |
| 3 | \Managerial System/SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md\ | DoD / 接缝 |

## What to build

assist 路径 span 与本地 JSONL / LangSmith 同构；无 Key 可回放；含 abstain 分支节点。

## Acceptance criteria

- [x] span 树覆盖主路径与 abstain
- [x] 无 LangSmith Key 可本地回放
- [x] 不进 S0 必过
- [x] handoff 含 Rewrote from:

## Answer

- 模块：`missions/assist_span_tree.py` — `build_assist_span_tree` 链式 `parent_run_id`：`assist→retrieve→fuse→gate→llm→(adopt|abstain)→evaluate`；JSONL 行与 LangSmith 同构（`id`/`parent_run_id`/`run_type`/`inputs`/`outputs`/`extra`）；`replay_assist_span_tree` 无 Key 回放；跳过 W0 扁平 span。
- 挂接：`ClaimsService.assist` 成功后 `emit_assist_span_tree`（仅本地 trace 开启时落盘；永不要求 LangSmith Key；旁路，非合门禁）。
- S0：`tests/test_assist_span_tree.py`（主路径/abstain、JSONL 回放、HTTP 落盘、`checks.py` 不引用、pytest.ini 仍排除 `langsmith_integration`）。
- Rewrote from: REF-CASE-EVAL-ADVISOR

## Comments

- 2026-09-15：\/to-spec\ 切票；Status=ready-for-agent。
- 2026-09-15：同步 GitHub Issue #28。
- 2026-09-16：\/implement\ 落地；Status=resolved。

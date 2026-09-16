# 40: 白名单工具环 retrieve/validate_citation/draft_slots；禁 latch/支付

**github_issue:** #27

**Status:** resolved

**Blocked by:** 37

**wave:** 2b-P-α

**spec_id:** SPEC-02B-P-ASSIST-QUALITY

**ref_id:** REF-CASE-FC

**Rewrote from:** REF-CASE-FC（外形，非 SQL 票务）

## 优先打开（只读参考）

路径相对于 \历史项目代码供参考/\。交付只写入 \本项目代码/claims-gate/\。

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | 见 ref_id | 加深缺口，勿平行重切 2a 主路径 |
| 2 | \docs/agents/phase2b-depth-planning-backlog.DRAFT.md\ | 已决议 registry |
| 3 | \Managerial System/SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md\ | DoD / 接缝 |

## What to build

app 拥有工具环：仅白名单工具；禁止写入 latch/支付/evaluate 权威字段。越权负例可测（H6）。

## Acceptance criteria

- [x] 白名单工具可用
- [x] 越权写入 = 0（H6 负例）
- [x] 非 FC SQL 票务语义
- [x] handoff 含 Rewrote from:

## Answer

- 模块：`missions/assist_tool_ring.py` — `AssistToolRing` 仅允许 `retrieve` / `validate_citation` / `draft_slots`；非白名单 → `AssistToolAclError`；结果剥除权威写字段；`draft_slots` 硬钉 `human_latch_token=None` / `payout_ready=False`。
- 管线：`track_llm_optional/pipeline.draft_assist` 经环调度 `retrieve` + `draft_slots`（禁回落到 latch/支付/evaluate 权威写）。
- H6 S0：`tests/test_assist_tool_acl.py`（白名单可用、越权工具名拒绝、权威面不变、retrieve_fn 改写面检测、KB 绑定 validate_citation、拒绝 `exc_sql` 票务语义）。
- Rewrote from: REF-CASE-FC（外形，非 SQL 票务）

## Comments

- 2026-09-15：\/to-spec\ 切票；Status=ready-for-agent。
- 2026-09-15：同步 GitHub Issue #27。
- 2026-09-16：\/implement\ 落地；Status=resolved。

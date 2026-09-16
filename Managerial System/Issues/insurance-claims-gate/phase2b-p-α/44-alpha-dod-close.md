# 44: α DoD 收口：H3/H6/H7 可演示 + S0 绿 + 手册

**github_issue:** #31

**Status:** resolved

**Blocked by:** 34, 35, 36, 37, 38, 39, 40, 41, 42, 43

**wave:** 2b-P-α

**spec_id:** SPEC-02B-P-ASSIST-QUALITY

**ref_id:** REF-MISSIONS

**Rewrote from:** SPEC-02B-P α DoD

## 优先打开（只读参考）

路径相对于 \历史项目代码供参考/\。交付只写入 \本项目代码/claims-gate/\。

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | 见 ref_id | 加深缺口，勿平行重切 2a 主路径 |
| 2 | \docs/agents/phase2b-depth-planning-backlog.DRAFT.md\ | 已决议 registry |
| 3 | \Managerial System/SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md\ | DoD / 接缝 |

## What to build

收口 α：勾选 SPEC α DoD；确认 H3/H6/H7 可演示、H1 种子存在、默认 pytest -q 绿；手册无 γ/Deferred 假上线。关闭后解阻 β 与未来 SPEC-Q。

## Acceptance criteria

- [x] SPEC α DoD Checklist 可勾选
- [x] H3/H6/H7 演示记录或可复现步骤
- [x] S0 绿
- [x] 手册诚实
- [x] Status 可改为 resolved

## Answer

`Rewrote from: SPEC-02B-P α DoD` · Issue 44 / GitHub #31

- **验收真源：** `本项目代码/claims-gate/docs/acceptance/alpha-dod.md`（H3/H6/H7 可复现步骤 + H1 种子证据）。
- **S0：** `pytest -q` → `235 passed, 20 deselected`（2026-09-16；无 LLM / 无 LangSmith / 无 cloud embedding Key）。
- **H1 种子：** `artifacts/demo_retrieval_seeds/demo_retrieval_seeds.v1.json`（15+20+5；非金标）。
- **H3：** `tests/test_assist_citation_schema_adopt.py`；**H6：** `tests/test_assist_tool_acl.py`；**H7：** 默认 S0 + evaluate 零向量依赖。
- **SPEC：** α DoD Checklist 全部勾选；β 仍 open。
- **手册：** USER_GUIDE / CHANGELOG 折叠 α；H4=`deferred`；γ / 连接状态 / ≥300 未假上线。
- **解阻：** `phase2b-p-β`（45–52）与未来 `spec-2b-q-relay-a2a3.md`。

## Comments

- 2026-09-15：/to-spec 切票；Status=ready-for-agent。
- 2026-09-15：同步 GitHub Issue #31。
- 2026-09-16：/implement 收口；Status=resolved；α DoD closed。

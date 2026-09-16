# Phase 2b · Q DoD 验收 / 演示记录（H8）

`Rewrote from: SPEC-02B-Q-RELAY-A2A3 DoD` · Issue 56 / GitHub #43

本清单关闭 **Missions Relay Honesty（流 Q · A2/A3）**。  
**不**宣称：A5 / Production latch；Q-A7 pause/resume / credential proxy；流 P Assist 质量分；H1–H6 召回/disposition；Mission Control 生产作业台。

工作目录：`本项目代码/claims-gate/`。默认合门禁：`pytest -q`（无 LLM / 无 LangSmith / 无 cloud embedding Key 仍须绿）。

**完成旗隔离：** 本文件是 Q 唯一出口。禁止把 `alpha-dod.md` / `beta-dod.md`、Issues 44–52、或 assist 指标标为 Q 完成条件。

---

## H8 — 工程中继诚实（Schema 硬停 + 真 diff+commit）

| 子项 | 证据票 | 可复现命令 |
|------|--------|------------|
| Q-S0-A 契约 Schema 硬停 | 53 | `pytest -q tests/test_schema_bound_orchestrator.py` |
| Q-S0-B 真 commit / owns_paths / 写锁 | 54 | `pytest -q tests/test_patch_worker_demo.py` |
| Q-S1 strip + 人闸不被改写 | 54 | `pytest -q tests/test_user_text_strip.py tests/test_threat_inject_ocr_remark.py` |
| Q-A6 独立 profile + 零产品写 | 55 | `pytest -q tests/test_validator_independent_profile.py` |
| Q-S0-C / H7 默认绿 | 本文件 | `pytest -q` |

**期望（H8）：**

- 缺 `goal` / 非法结构 → 入账前失败，不开工。
- `F-Q-DEMO-01` handoff：`git_commit` 非空；`files_touched` ⊆ 该特性 `owns_paths`；可检视 worktree diff。
- `git_commit=null` / 空 diff / 越权路径 → 不得标 feature `DONE`。
- 写锁争用 `owns_paths` → fail-closed。
- Validator retrieve profile（或可配置模型名）与 Worker 可区分；运行后产品树无 Validator 写入。

勾选：`[x] H8 可演示`

---

## Q-S0-A — 契约 Schema 硬停

**可复现：**

```text
pytest -q tests/test_schema_bound_orchestrator.py
```

**期望：** 缺/空白 `goal`、非法 `template_id` / 契约结构 → `PlanSchemaError` 或等价硬停；合法 plan 入账后 `goal` 可在 contract / handoff 观察；规划主路径不以 goal 子串 if/elif 冒充 Schema-bound 契约源。

勾选：`[x] Q-S0-A`

---

## Q-S0-B — handoff 真 commit / owns_paths / 写锁

**可复现：**

```text
pytest -q tests/test_patch_worker_demo.py
```

**期望：** `F-Q-DEMO-01` 在临时本地 git/worktree 内真实改文件；handoff 非空 `git_commit`；`files_touched` ⊆ owns_paths；空 diff / null commit / 硬禁或越权路径 → `BLOCKED`（不得 DONE）；写锁争用 fail-closed。不绑远端、不要求 LLM Key。

勾选：`[x] Q-S0-B`

---

## Q-S1 — F-Q-DEMO-01 strip + 提权负例

**可复现：**

```text
pytest -q tests/test_user_text_strip.py tests/test_threat_inject_ocr_remark.py
```

**期望：** OCR/备注吸收 strip 首尾空白；全空白→空串；人闸 / `payout_ready` / 金额档不被用户可控文本改写；既有 OCR 提权负例仍绿。

勾选：`[x] Q-S1`

---

## Q-A6 — Validator 独立 profile（轻量）

**可复现：**

```text
pytest -q tests/test_validator_independent_profile.py
```

**期望：** Worker/Validator `*_RETRIEVE_PROFILE`（或可配置模型名）可区分；Validator 路径产品树指纹无改写；失败只写 fail report；真多模型测旁路（`requires_llm`），不进默认绿。

勾选：`[x] Q-A6 轻量` · **未**宣称 A5 / Production latch

---

## Q-S0-C / H7 — 默认 `pytest -q` 绿

**可复现（Q 合门禁 S0）：**

```text
pytest -q
```

**记录（2026-09-16）：** `314 passed, 25 deselected`（排除 `track_llm_optional` / `eval_bypass` / `requires_llm` / `langsmith_integration` 等）；无 cloud embedding Key；无 LangSmith。

勾选：`[x] Q-S0-C` · `[x] S0 绿` · `[x] H7 保持`

---

## 完成旗隔离（对照 P）

| 禁止当作 Q 出口 | 本票态度 |
|-----------------|----------|
| Issues 44–52 / P-α·P-β DoD | 不勾选、不回写为 Q 完成 |
| `alpha-dod.md` / `beta-dod.md` | 仅对照；不复用完成旗 |
| Assist H1–H6 / disposition / 检索分 | 不作为 H8 证据 |
| Q-A7 pause/resume / credential proxy | **Deferred**；未做不得称 Production latch |

勾选：`[x] 未将 P Issues/质量分标为 Q 完成条件` · `[x] Q-A7 保持 Deferred`

---

## 手册诚实

- 流 Q 默认**用户不可见**（无 Mission Control 作业台合入）。
- 示范特性可观察面：OCR/客户备注写入前 strip（票 54 已写入 `USER_GUIDE` / `CHANGELOG`）；不改人闸规则。
- 本 DoD 关闭时同步手册：可称「2b-Q 中继诚实已关闭」，须同时标注 **未**宣称 A5 / Production latch、Q-A7 Deferred。

勾选：`[x] 手册诚实` · `[x] 用户手册已同步`

---

## Q DoD 总勾选

| SPEC 无条件项 | 状态 |
|---------------|------|
| Orchestrator Schema 硬停；缺 goal 不开工 | 票 53 / Q-S0-A |
| 规划主路径非字符串 if/elif 冒充 | 票 53 |
| Worker `F-Q-DEMO-01` 真 diff+commit；owns_paths | 票 54 / Q-S0-B |
| 空 diff / null commit / 越权 → 不得 DONE | 票 54 |
| 写锁争用 fail-closed | 票 54 |
| strip + 人闸不被改写 | 票 54 / Q-S1 |
| Validator 独立 profile + 零产品写 | 票 55 / Q-A6 |
| 默认 `pytest -q` 无 LLM/无 LangSmith 绿 | 本文件 / Q-S0-C |
| **H8 可演示**；独立验收件 | 本文件 |
| 未将 P Issues/assist 指标标为 Q 完成 | 本文件 |

| Deferred | 状态 |
|----------|------|
| Q-A7 pause/resume；credential proxy（A5） | **Deferred**（不切本期实现票） |

**关闭后：** `phase2b-q/` Frontier 为空；SPEC-02B-Q Status=`closed`。γ / ≥300 金标 / L2 / Production latch 仍勿预切。

# 55: Q-A6 Validator 独立 profile（零产品写）

**github_issue:** #42

**Status:** resolved

**Blocked by:** 54

**wave:** 2b-Q

**spec_id:** SPEC-02B-Q-RELAY-A2A3

**ref_id:** REF-MISSIONS

**Rewrote from:** REF-MISSIONS Validator；宪法 A4 预备（轻量）

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | `project 多agent`（REF-MISSIONS） | Validator 只评判、独立检索画像 |
| 2 | SPEC-02B-Q Testing Decisions | 轻量 S0 vs 真多模型旁路 |
| 3 | 现有 `missions/validator.py` | 加深缺口，勿平行重切 |

## What to build

Validator 使用与 Worker **可区分**的 retrieve profile（或可配置独立模型名）；运行后**零**产品代码写入；失败只出 fail report，由 Orchestrator 开 fix。真多模型/需 Key 调用不进默认 `pytest -q`。可与 P-E5 共用 κ **叙事**，实现与完成旗必须分离。

## Acceptance criteria

- [x] profile（或模型名配置）与 Worker 可区分（轻量 S0）
- [x] Validator 路径无产品树写入断言
- [x] 失败 → fail report；不自改产品
- [x] 真多模型测若存在则旁路标记，默认 CI 排除
- [x] 默认 `pytest -q` 仍绿；handoff 含 `Rewrote from:`
- [x] 不宣称 A5 / Production latch

## Answer

- `missions/role_profiles.py`：Worker/Validator 可区分的 `*_RETRIEVE_PROFILE` 与 `*_MODEL_NAME`（S0 配置位；不触发真 LLM）。
- Validator：构造可覆盖 `retrieve_profile` / `model_name`；事件与 handoff 记录画像；失败写 `artifacts/fail_report.json`，不开 fix、不写产品树。
- Worker：对照暴露同名配置位；检索改用 `self.retrieve_profile`。
- 测：`tests/test_validator_independent_profile.py`（profile 差、零产品写指纹、fail report、`requires_llm` 旁路）。默认 `pytest -q`：314 passed / 25 deselected。
- 未宣称 A5 / Production latch；κ 叙事与 P-E5 完成旗分离。`Rewrote from: REF-MISSIONS`。

## Comments

- 2026-09-16：`/to-spec` 切票；Status=ready-for-agent。
- 2026-09-16：同步 GitHub Issue #42。
- 2026-09-16：`/implement` 落地 Q-A6 独立 profile + 零产品写；Status=resolved。

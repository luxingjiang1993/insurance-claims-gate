# 10: Eval / 机检负例入口（不替代 machine_check）

**Status:** resolved

**Blocked by:** 09

**ref_id:** REF-CASE-OPENEVALS, REF-MISSIONS

**Backlog:** P1（eval 旁路）；对齐清单一 `REF-CASE-OPENEVALS`

**Rewrote from:** REF-CASE-OPENEVALS, REF-MISSIONS

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `CASE-openevals使用/12-openevals_evaluators.py` | 评估器注册/调用外形 |
| 2 | `CASE-openevals使用/5-rag_groundedness.py` | groundedness / 引用落地类评估灵感 |
| 3 | `CASE-openevals使用/8-hallucination.py` | 幻觉负例评估外形 |
| 4 | `project 多agent/src/missions/checks.py` | 现有 `machine_check` 分发；本票不得吞并主缝 |
| 5 | `project 多agent/tests/compliance/`（若有） | 合规失败用例风格 |

## What to build

在轨 A 旁路增加 **eval / 负例入口**：可对固定负例夹具（伪 citation、拆轮补件、通融伪通赔等已有或扩展）跑评估器外形或薄封装，产出可机读报告。  
**硬约束：** 默认 CI 合门禁仍以 `machine_check` 为准；本入口失败可告警/另标记，但不得改写人闸语义，不得要求 LLM 才能让轨 A 变绿。

## Acceptance criteria

- [x] 存在独立模块或脚本入口（如 `missions/eval_entry.py` 或 `tests/eval/`），文档标明「旁路，非合门禁主缝」
- [x] 至少覆盖 2 类负例（建议：幻觉/库外 citation；同 hash 拆轮或通融伪 citation）并给出 pass/fail 结构
- [x] 默认 `pytest -q`（轨 A）不依赖本入口才能全绿；若挂测试须明确不替代 SC machine_check
- [x] handoff 含 `Rewrote from: REF-CASE-OPENEVALS, REF-MISSIONS`
- [x] 不引入支付工具；不并入轨 B 默认绿门

## Answer

旁路入口已落地：`missions/eval_entry.py`（评估器注册 + `run_eval_negatives` 机读报告）与 `tests/eval/`；默认套件覆盖 `hallucination_citation` 与 `exgratia_fake_citation`（可选 `one_shot_split_round`）；`pytest.ini` 排除 `eval_bypass`，默认轨 A 不依赖本套件全绿；文档声明「旁路，非合门禁主缝」；`checks.py` 不路由 SC 经本入口。Rewrote from: REF-CASE-OPENEVALS, REF-MISSIONS。

## Comments

- 2026-09-13：current-phase-remaining 切票；个人开发阶段。
- 2026-09-13：实现完成；确定性评估器外形（无 LLM）；Rewrote from: REF-CASE-OPENEVALS, REF-MISSIONS。

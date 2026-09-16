# 50: Judge–human agreement / κ 实填（绑金标薄切片）

**github_issue:** #37

**Status:** resolved

**Blocked by:** 44, 38

**wave:** 2b-P-β

**spec_id:** SPEC-02B-P-ASSIST-QUALITY

**ref_id:** REF-CASE-OPENEVALS

**Rewrote from:** Issue 11 加深；REF-CASE-OPENEVALS

## 优先打开（只读参考）

路径相对于 \历史项目代码供参考/\。交付只写入 \本项目代码/claims-gate/\。

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | 见 ref_id | 加深缺口，勿平行重切 2a 主路径 |
| 2 | \docs/agents/phase2b-depth-planning-backlog.DRAFT.md\ | 已决议 registry |
| 3 | \Managerial System/SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md\ | DoD / 接缝 |

## What to build

在金标薄切片上实填 κ / judge-human agreement；合成样例不得冒充。κ≥0.60 才可宣称 grounded（与 H4）。

## Acceptance criteria

- [x] κ 协议与数值可报告
- [x] 合成不冒充
- [x] 与 H4 文案一致
- [x] handoff 含 Rewrote from:

## Answer

`missions/judge_human_kappa.py`：标者间 Cohen κ（绑薄切片 `label_a`/`label_b`）；H4 门 n≥10 + 忠实率≥0.85 + κ≥0.60 + 非合成；外形样例与 Issue 11 合成抽检强制 `is_synthetic`、禁止 grounded。忠实报告接 κ 字段。验收 `docs/acceptance/judge-human-kappa.md`；手册 §3.10。`Rewrote from: REF-CASE-OPENEVALS`（Issue 11 加深）。

## Comments

- 2026-09-15：\/to-spec\ 切票；Status=ready-for-agent。
- 2026-09-15：同步 GitHub Issue #37。
- 2026-09-16：\/implement\ 落地；Status=resolved；κ 可报告；H4 仍 deferred（样例 n&lt;10）；合成不冒充。

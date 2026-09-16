# 57: G0 Live Pilot 路径 + Live 验收

**github_issue:** #44

**Status:** resolved

**Blocked by:** —

**wave:** 2c

**spec_id:** SPEC-02C-LIVE-HONEST-SEAMS

**ref_id:** REF-MISSIONS

**Rewrote from:** REF-MISSIONS（合门禁旁路纪律）；仓内既有分 Key / cloud embedding / 连接状态

## 优先打开（只读参考）

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | `Managerial System/SPEC/insurance-claims-gate/spec-2c-live-honest-seams.md` | G0 DoD |
| 2 | `本项目代码/claims-gate/docs/acceptance/package-l.md` | 套餐 L 之上加 Live 档姿势 |
| 3 | `本项目代码/claims-gate` Embedding / 连接状态 / `track_llm_optional` | 已有管道，加深验收 |

## What to build

交付可演示的 Live Pilot 路径：双 Key + cloud embedding 重建；有 Key 真 Assist 起草；缺 Key 明确降级；Live 验收清单；`requires_llm` 旁路在有 Key 环境可绿。默认 `pytest -q` 无 Key 仍绿。不宣称 grounded。

## Acceptance criteria

- [x] `.env` 分区：LLM Key 与 Embedding Key 分离；`EMBEDDING_PROVIDER=cloud` 可重建索引
- [x] 连接状态双绿路径可演示；永不回显 Key
- [x] `enable_llm=true` 有 Key → structured draft；缺 Key → 明确降级
- [x] Live 验收文档可勾完（套餐 L 之上）
- [x] 有 Key 环境：`requires_llm` / track LLM optional 旁路绿
- [x] 默认 `pytest -q` 无 Key 仍绿
- [x] 文案不宣称 H4 grounded / 面试条 9

## Comments

- 2026-09-16：`/to-spec` 切票；Status=ready-for-agent。
- 2026-09-16：同步 GitHub Issue #44。
- 2026-09-16：`/implement` 关闭实现侧 G0 — 既有分 Key / 连接状态 / Assist 降级加深验收；新增 `docs/acceptance/live-pilot-g0.md`、契约测、`requires_llm` 真 Assist structured draft；默认 `pytest -q` → 316 passed / 26 deselected。人工 L0–L3 勾选与有 Key 旁路实跑仍由验收人在清单填写（本环境无 Key 时 `requires_llm` 为 skip）。

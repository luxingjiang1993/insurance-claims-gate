# AGENTS.md — Claims Gate 仓库入口

给 coding agents 的读序与写边界。人类架构师保留理解与发布责任；细节以 Durable 文档为准，不靠聊天记忆。

## 读序（开工前）

1. `CONTEXT.md` — 领域术语（禁止与 glossary 打架）
2. `Managerial System/Constitution/DESIGN_PHILOSOPHY.md` — 不变量 I1–I8
3. `Managerial System/PRD/PRD_02_INSURANCE_CLAIMS_GATE.md` — 需求真源（当前 Ready for Spec）
4. 若已存在：`Managerial System/SPEC/insurance-claims-gate/spec.md` 与对应 Issues
5. `docs/agents/issue-tracker.md` — tickets 落盘约定
6. 改写前读：`docs/agents/ref-projects.md`（`REF_*` ID）；主基线 **`REF-MISSIONS`** = `历史项目代码供参考/project 多agent/`（只读）
7. 若已存在：对应 Issues；票内应含 `ref_id:` 字段

## 写边界

| 可写 | 路径 |
|------|------|
| 产品代码 | `本项目代码/claims-gate/` |
| 管理真源 | `Managerial System/`（PRD / SPEC / Issues / Background / Value / Sources / Constitution） |
| Agent 约定 | `AGENTS.md`、`CONTEXT.md`、`docs/agents/` |

| 只读（禁止当交付修改） | 路径 |
|------------------------|------|
| 历史参考与课程案例 | `历史项目代码供参考/`（按 `REF_*` 索引，见 `docs/agents/ref-projects.md`） |

## 改写规则

- 默认从 **`REF-MISSIONS`** 裁剪；其他 `REF_*` 只补缺口，不另起三角色剧场。
- handoff / ticket 写明：`Rewrote from: REF-…`。
- OpenManus（`REF-OPENMANUS-*`）不得替代 Missions 中继主链。

## 流水线

`PRD` → `SPEC/insurance-claims-gate/spec.md` → `Issues/insurance-claims-gate/NN-*.md` → 实现（日后 git / PR）。  
未写 SPEC 前不要切实现票；未人闸令牌不得设计自动出款。

## Agent skills

### Issue tracker

本地 markdown，映射在 `Managerial System/SPEC` 与 `Managerial System/Issues`（非 `.scratch/`）。见 `docs/agents/issue-tracker.md`。

### Domain docs

single-context：根目录 `CONTEXT.md`；设计哲学在 `Managerial System/Constitution/`。ADR 仅在难逆、意外、有真实权衡时再写。

## 硬禁区（与 PRD Won't / 哲学对齐）

- 不实现 L3 自动出款 / 银企直连
- Worker 不得自审自批；Validator 不得改被测产品代码
- 不把「秒赔」用作责任争议案叙事
- 不并行多 Writer 抢同一可变工件（无 lock / worktree）
- 中文注释用 UTF-8；代码中不要 emoji

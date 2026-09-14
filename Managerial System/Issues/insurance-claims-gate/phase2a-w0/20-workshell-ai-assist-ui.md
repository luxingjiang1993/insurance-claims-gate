# 20: 作业壳：AI 辅助区 + 非终裁标注 + 采纳

**github_issue:** #7

**Status:** resolved

**Blocked by:** 17, 19

**wave:** W0

**spec_id:** SPEC-02A-W0-DEV-COMPLETE

**ref_id:** REF-MISSIONS, REF-CASE-HYBRID

**Rewrote from:** REF-MISSIONS, REF-CASE-HYBRID

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `CASE-投顾AI助手（混合式）/` | 助手 vs 规则结论的分治叙事 |
| 2 | 本仓 `docs/user/` 消保口径 | 「辅助非终裁」文案边界 |

## What to build

在作业壳增加 AI 辅助建议区：须显式点击才调用；无 Key 时显示降级提示且不阻断规则路径；区分辅助建议与裁决草案标签；采纳走「送交规则校验」；UI 标明裁决辅助非终裁，无秒赔误导。

## Acceptance criteria

- [x] 显式点击「AI 辅助建议」才触发 assist（无静默默认调用）
- [x] 无 Key 时降级提示可见；规则路径仍可用
- [x] 辅助建议与裁决草案分标签展示
- [x] 采纳须经规则校验路径；失败时诚实展示
- [x] UI 标明辅助非终裁；无秒赔/无人赔付误导文案
- [x] handoff 含 `Rewrote from: REF-MISSIONS`

## Answer

交付位于 `本项目代码/claims-gate/workshell/`：

- `api/client.ts`：`assistClaim` / `adoptAssist`（直连 HTTP，错误原样）
- `components/AiAssistPanel.tsx`：显式点击才调用；降级横幅；「送交规则校验（采纳）」；非终裁标签
- `DecisionDraftView`：裁决草案分标签（与辅助建议对照）
- `CaseDetailPage`：挂载 AI 区于规则路径与裁决草案之间
- 测试：`src/api/client.test.ts`（assist / adopt / 拒绝原样）
- 用户文档：`docs/user/USER_GUIDE.md` §3.1 / 成熟度表；`CHANGELOG.md` Unreleased

**Rewrote from: REF-MISSIONS, REF-CASE-HYBRID**

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w0/`。
- 2026-09-14：同步 GitHub Issue #7。
- 2026-09-14：实现完成并 Resolve。

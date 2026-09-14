# 16: 作业壳：登录 + 案件只读浏览

**github_issue:** #3

**Status:** resolved

**Blocked by:** 14

**wave:** W0

**spec_id:** SPEC-02A-W0-DEV-COMPLETE

**ref_id:** REF-MISSIONS, REF-COURSE-04

**Rewrote from:** REF-MISSIONS

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `04_多步流程编排与条件分支/` | 作业流 / 状态展示外形 |
| 2 | `project 多agent/src/transfer_api/` | 被调 HTTP 面与错误外形 |

## What to build

交付 Vite+React+TS 作业壳（套餐 C）最小可用面：浏览器登录，案件列表与详情只读浏览。详情展示 gate_status、document_status、inference_track、payout_ready。无 BFF；错误原样展示 API 拒绝。viewer 在壳内保持只读。

## Acceptance criteria

- [x] 作业壳可登录并列出持久化案件
- [x] 案详情可读 gate_status、document_status、inference_track、payout_ready
- [x] viewer 无法在壳内发起写操作（或写操作被 API/UI 诚实拒绝）
- [x] 无 BFF；API 错误原样展示
- [x] handoff 含 `Rewrote from: REF-MISSIONS`

## Answer

交付位于 `本项目代码/claims-gate/`：

- `workshell/`：Vite+React+TS 作业壳（登录 / 列表 / 详情只读）；`viewer` 不展示写操作入口；API 拒绝体原样展示
- HTTP：`GET /claims` 列表摘要；`GET /claims/{id}` 含 `document_status` / `payout_ready`；CORS 允许 `5173`
- 接缝测试：`workshell/src/api/client.test.ts`（login / list / detail / 错误原样）；`tests/test_claims_api_l1.py` 覆盖列表与详情字段
- 用户文档：`docs/user/USER_GUIDE.md` §3.1、`CHANGELOG.md` Unreleased

启动：先 `python scripts/run_api.py`，再 `cd workshell && npm run dev` → `http://127.0.0.1:5173/`。

`Rewrote from: REF-MISSIONS`

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w0/`。
- 2026-09-14：同步 GitHub Issue #3。
- 2026-09-14：实现完成并 resolved。

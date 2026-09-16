# 59: G3 L2 Core Adapter + Recorded 夹具

**github_issue:** #46

**Status:** resolved

**Blocked by:** —

**wave:** 2c

**spec_id:** SPEC-02C-LIVE-HONEST-SEAMS

**ref_id:** REF-MISSIONS

**Rewrote from:** REF-MISSIONS（L2 回写与人闸外形）

## 优先打开（只读参考）

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | SPEC-02C G3 L2 / S3 | 契约与 Ready≠Deployed |
| 2 | 仓内 L2 payout-ready / close + 人闸测 | 现有模拟回写行为须保留语义 |
| 3 | Constitution Integration L2 vs L3 | L2 回写 ≠ 支付 |

## What to build

将 Integration L2 出款就绪回写 / 结案抽成 Provider 接口；至少 InMemory（或等价进程内）与 Recorded 两实现；契约测绿。人闸与门禁校验仍在核心服务。无真核心时仅宣称 Integration-Ready。不做 A5、不做 L3。

## Acceptance criteria

- [x] L2 Provider 接口覆盖 payout_ready 回写与 close
- [x] InMemory + Recorded 两实现；契约测在无现网账号下可绿
- [x] 换适配器不改变人闸 / 出款就绪前置条件
- [x] L2 路径支付适配计数仍禁止递增
- [x] 文档写明 Integration-Ready，禁止「已接核心」
- [x] 默认 `pytest -q` 仍绿

## Answer

- 接缝：`claims_api/l2_core_provider.py` — `L2CoreProvider` + `InMemoryL2CoreProvider` + `RecordedL2CoreProvider`
- 服务：`ClaimsService` 人闸/主数据校验后调用 Provider；默认 InMemory；响应带 `l2_integration_status=Integration-Ready`
- 契约测：`tests/test_l2_core_provider_contract.py` + `tests/fixtures/l2_core/recorded_cassette.json`
- HTTP 既有 `test_l2_payout_ready_writeback.py` 仍绿；换宽松适配器仍 `LATCH_REQUIRED`
- 文档：USER_GUIDE / CHANGELOG / README / interview 梯子与 talk-track 标明 Ready≠Deployed

## Comments

- 2026-09-16：`/to-spec` 切票；Status=ready-for-agent。
- 2026-09-16：同步 GitHub Issue #46。
- 2026-09-16：`/implement` 交付；Status=resolved；默认 `pytest -q` 330 passed。

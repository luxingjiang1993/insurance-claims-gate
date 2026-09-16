# 60: G3 OCR Provider + Recorded + 威胁不变式

**github_issue:** #47

**Status:** resolved

**Blocked by:** —

**wave:** 2c

**spec_id:** SPEC-02C-LIVE-HONEST-SEAMS

**ref_id:** REF-MISSIONS

**Rewrote from:** REF-MISSIONS（用户可控文本收纳）；仓内 OCR remark 威胁测

## 优先打开（只读参考）

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | SPEC-02C G3 OCR / 威胁不变式 | extract → 规范化文本 |
| 2 | 仓内 `absorb_user_controlled_text` / threat inject 测 | 现有 strip 与 latch 不变式 |
| 3 | 诚实表「真 OCR 延后」行 | 改为 Provider + Stub/Recorded，仍非 Deployed |

## What to build

OCR Provider：`extract` → 规范化文本，再进入既有用户可控文本收纳。Stub + Recorded 必有；真实供应商可开关且非默认 CI 依赖。注入文本仍不得翻 latch / 签发人闸 / 单独造成出款就绪。本票不扩 KB≥20。

## Acceptance criteria

- [x] OcrProvider（或等价）接口 + Stub + Recorded
- [x] 规范化文本进入既有收纳路径；作业面可观察
- [x] 威胁测：注入不得签发人闸令牌、不得单独出款就绪
- [x] 默认 CI 不依赖真 OCR 账号
- [x] 诚实文案：Integration-Ready / Stub，禁止「生产 OCR 已上线」若未真连
- [x] 默认 `pytest -q` 仍绿

## Answer

- 接缝：`claims_api/ocr_provider.py` — `OcrProvider` + `StubOcrProvider` + `RecordedOcrProvider`
- 服务：`ClaimsService._absorb_via_ocr_provider`；默认 Stub；HTTP 可见 `ocr_integration_status=Integration-Ready`
- 契约测：`tests/test_ocr_provider_contract.py` + `tests/fixtures/ocr/recorded_cassette.json`
- 威胁：既有 `test_threat_inject_ocr_remark` + 契约内注入负例仍绿；无令牌写回仍拒
- 文档：USER_GUIDE / CHANGELOG / 诚实表 / 威胁模型标明 Ready≠生产 OCR 已上线
- 默认 `pytest -q`：337 passed

## Comments

- 2026-09-16：`/to-spec` 切票；Status=ready-for-agent。
- 2026-09-16：同步 GitHub Issue #47。
- 2026-09-16：`/implement` 交付；Status=resolved；默认 `pytest -q` 337 passed。
- 2026-09-16：code-review 后修：OCR 状态仅随 evaluate/materials 请求暴露；`current-phase-remaining` 恢复为单行 OCR 注记。

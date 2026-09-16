# Claims Gate — 威胁模型半页（N10）

面试口径，不是完整 STRIDE。权威仍在轨 A + 人闸；此处只报已落地的四条缝。

## 1. OCR / 客户备注不可提权

用户可控文本经 **OCR Provider**（默认 Stub）`extract` → 规范化后再收纳；`customer_remark` 仍 strip。只作可观察收纳。

**不得**改写：`human_latch_required`、`payout_ready`、金额档；不得签发 `human_latch_token`。负例夹具仍走 `threat_inject_ocr_remark_no_latch_flip`。作业面可观察 `ocr_integration_status=Integration-Ready`（≠ 生产 OCR 已上线）。

## 2. 工具 ACL（H6）

Assist / 工具环 **白名单**。越权写入 latch、支付、evaluate 权威字段 = 0。支付类工具默认拒绝。无 L3 银企。

## 3. 不自审自批

Worker 不得自审自批。Validator **不得**改被测产品代码（独立 profile、零产品写）。作业壳不自行签发 `human_latch_token`。

## 4. 人闸 fail-closed

无有效令牌 → `LATCH_REQUIRED`；`payout_ready` 保持 false。`adjuster` 批闸 `PERMISSION_DENIED`。`EXTERNAL_NOTIFY` 须令牌；草稿 `DRAFT_EXPORT` 不得冒充已对外。

**勿夸大：** 这不是生产 A5 credential proxy，也不是真 OCR 供应商隔离。

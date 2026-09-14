# Claims Gate — User-facing Changelog

格式对齐硅谷产品 docs 的 *What's new*：按 **阶段 / 里程碑** 记录用户可感知变化。内部改写票号可附注，但不替代本文件。

维护规则见 [`MAINTENANCE.md`](./MAINTENANCE.md)。

---

## Phase 1 — Pilot surface（2026-09）

**Status:** Shipped for personal acceptance (HTTP + Solo Demo).  
**Issues:** 01–13 resolved（工程侧）；真实用户实测 / 作业 UI / 真 L2 仍延后。

### Added

- 理赔门禁 HTTP API：立案只读、材料登记、evaluate、一次补件通知、文书导出、人闸、调查冻决、通融/预赔、高峰降级、L2 出款就绪与结案模拟。
- 验收场景 SC-01 / SC-02 / SC-03 与 Solo Demo：`python scripts/run_sc_demo.py`。
- 条款 KB citation 落库门与效力栈减赔路径。
- 人闸金额档矩阵（试点默认 A–D）与 ledger 可追溯字段。
- 轨 B 最小检索起草（Preview，不挡轨 A）。
- Eval 负例旁路与合成抽检表占位（不冒充金标）。

### Guarantees (user-visible)

- 无人闸令牌不得 `payout_ready=true`。
- 同 `one_shot_hash` 禁止拆轮补件。
- 不实现自动出款 / 银企直连。
- 默认合门禁不依赖 LLM 抽样。

### Not in this phase

- 核赔作业 UI 壳
- 真连核心 L2 / 现网枚举
- 真实 OCR 供应商
- Week1–4 基线实测与 ≥300 人工金标运营

---

## Phase 2 — （占位）

**Status:** Not started.  
启动条件：`docs/agents/current-phase-remaining.md` §1 DoD 满足，且修宪 / 新 PRD·SPEC 条目写入后。

本节目程用户可见能力落地后，在此追加 `Added` / `Changed` / `Deprecated`，并同步修订 [`USER_GUIDE.md`](./USER_GUIDE.md) 成熟度表与 How-to。

---

## Unreleased

### Added

- 作业壳（Vite+React+TS）Preview：浏览器登录、案件列表/详情只读浏览（`gate_status` / `document_status` / `inference_track` / `payout_ready`）；`viewer` 无写操作入口；API 错误原样展示。启动见 `USER_GUIDE` §3.1。
- 作业壳 SC 规则路径（Issue 17）：`adjuster` 可登记材料、evaluate、一次补件并查看裁决草案；无 LLM Key 可点完；拒绝不假成功。`Rewrote from: REF-MISSIONS`。
- 作业壳人闸与文书分态（Issue 18）：`supervisor` 可批/驳人闸并看到 API 令牌；`adjuster` 批闸被拒且不假成功；拒赔 `DRAFT_EXPORT` 可预览；`EXTERNAL_NOTIFY` 无人闸失败时 UI 不升对外。`Rewrote from: REF-MISSIONS`。
- HTTP：`GET /claims` 案件列表摘要；`GET /claims/{id}` 补充 `document_status` / `payout_ready` 可读字段。

### Changed

- Quickstart：仓库根可用 `python scripts/run_api.py` 启动 API；避免在根目录误用 `--app-dir src` 导致 `ModuleNotFoundError: claims_api`。

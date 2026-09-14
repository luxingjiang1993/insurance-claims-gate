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

## Phase 2a · W0 — Dev Complete（2026-09）

**Status:** Developer Preview closed for W0 DoD（Issues 14–22）。  
**Scope:** 作业壳 + SQLite + RBAC + AI 降级 + 本地 trace；默认 `pytest -q` 无 LLM / 无 LangSmith 全绿。  
**Not in W0：** Chroma / 混合检索、真 LangSmith 完工、OpenEval 排行榜与多人（属 W1/W2）。

### Added

- 作业壳（Vite+React+TS）Preview：浏览器登录、案件列表/详情只读浏览（`gate_status` / `document_status` / `inference_track` / `payout_ready`）；`viewer` 无写操作入口；API 错误原样展示。启动见 `USER_GUIDE` §3.1。
- 作业壳 SC 规则路径（Issue 17）：`adjuster` 可登记材料、evaluate、一次补件并查看裁决草案；无 LLM Key 可点完；拒绝不假成功。`Rewrote from: REF-MISSIONS`。
- 作业壳人闸与文书分态（Issue 18）：`supervisor` 可批/驳人闸并看到 API 令牌；`adjuster` 批闸被拒且不假成功；拒赔 `DRAFT_EXPORT` 可预览；`EXTERNAL_NOTIFY` 无人闸失败时 UI 不升对外。`Rewrote from: REF-MISSIONS`。
- 作业壳 AI 辅助建议区（Issue 20）：显式点击「AI 辅助建议」；无 Key 降级可见；辅助建议与裁决草案分标签；「送交规则校验（采纳）」再 evaluate；UI 标明非终裁、无秒赔误导。`Rewrote from: REF-MISSIONS, REF-CASE-HYBRID`。
- 作业壳本案流水 + 本地 trace（Issue 21）：详情页可浏览 ledger / 人闸事件；`CLAIMS_GATE_LOCAL_TRACE=1` 可导出 evaluate/assist/latch JSONL span；LangSmith 仅 `.env.example` 配置位，默认 pytest 不要求 Key。`Rewrote from: REF-MISSIONS`。
- HTTP：`GET /claims` 案件列表摘要；`GET /claims/{id}` 补充 `document_status` / `payout_ready` 可读字段；SQLite 种子三角色登录会话（Issue 14）；人闸 RBAC 硬门含 S0 负例（Issue 15）。
- 用户手册 W0 启动 / 角色 / 规则路径 / AI 降级与非终裁诚实边界（Issue 22）。`Rewrote from: REF-MISSIONS`。

### Changed

- Quickstart：仓库根可用 `python scripts/run_api.py` 启动 API；避免在根目录误用 `--app-dir src` 导致 `ModuleNotFoundError: claims_api`。
- `USER_GUIDE` 页眉与成熟度表区分 Phase 1 Shipped 与 Phase 2a W0 Preview；明确 W1/W2 未上线。

### Guarantees (user-visible)

- 默认 `pytest -q` 在无 LLM Key、无 LangSmith 下全绿（含 S0 RBAC 负例）。
- AI 辅助不签发人闸令牌、不写 `payout_ready`；采纳须再过规则 evaluate。

---

## Phase 2a · W1 / W2 — （未启动实现主路径）

**Status:** Not started as shipped surface.  
W0 DoD 关闭后方可将实现重心转到 W1；W1 关闭后再开 W2。用户可见能力落地前，勿将向量检索 / 真 LangSmith / OpenEval 排行榜写成已上线。

---

## Unreleased

### Added

- 作业壳 AI 辅助区检索来源摘要（Issue 25）：可见 doc / 条款项 / 版本；可采纳 vs 不可采纳诚实标注；不静默改写裁决草案；无秒赔/终裁误导。`Rewrote from: REF-MISSIONS, REF-CASE-HYBRID`。
- 真 LangSmith span + ledger `trace_id`（Issue 26）：配置 `LANGCHAIN_TRACING_V2` + Key 后 evaluate / assist / latch 上报；ledger 含 `retrieval_profile` 与 `trace_id`（有上报时）；本地 JSONL 仍可用；无 Key 不阻断；默认 `pytest -q` 不要求；S2 标记 `langsmith_integration`。`Rewrote from: REF-CASE-EVAL-ADVISOR, REF-MISSIONS`。
- OpenEval ↔ LangSmith 实验历史对比（Issue 27）：旁路最小集 `python -m missions.openeval_langsmith`；同 dataset 多 experiment 可历史对比；不含排行榜/多人协作；不替代 `machine_check`；默认 pytest 不要求 Key。`Rewrote from: REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR, REF-MISSIONS`。

---

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

## Phase 2a · W1 — Pilot Complete（2026-09）

**Status:** Developer Preview closed for W1 DoD（Issues 23–28）。  
**Scope:** Chroma + 混合检索挂 assist + 来源摘要 + 真 LangSmith + OpenEval 实验历史对比 + 套餐 L 验收清单；默认 `pytest -q` 仍无 LLM / 无 LangSmith 全绿。  
**Not in W1：** OpenEval 排行榜、多人协作评测台（属 **W2 Eval Ops**，未上线）。

### Added

- Chroma 索引 + 本地/云 embedding + 可重建（Issue 23）：`python scripts/rebuild_chroma_index.py`；规则 evaluate 零向量依赖。
- 混合检索挂 assist（Issue 24）：硬过滤 / 条款号短路 / 0.7·0.3 加权 / 三联门 / 关向量关键词降级；evaluate 不调向量。
- 作业壳 AI 辅助区检索来源摘要（Issue 25）：可见 doc / 条款项 / 版本；可采纳 vs 不可采纳诚实标注；不静默改写裁决草案。
- 真 LangSmith span + ledger `trace_id`（Issue 26）：配置 `LANGCHAIN_TRACING_V2` + Key 后 evaluate / assist / latch 上报；无 Key 不阻断；默认 `pytest -q` 不要求；S2 标记 `langsmith_integration`。
- OpenEval ↔ LangSmith 实验历史对比（Issue 27）：`python -m missions.openeval_langsmith`；不含排行榜/多人；不替代 `machine_check`。
- 套餐 L 验收清单 + Pilot 手册区分（Issue 28）：`本项目代码/claims-gate/docs/acceptance/package-l.md`（满配 / 关向量 / 关 LLM）；USER_GUIDE 区分「演示可无 Key」与「Pilot 须 LangSmith」；不进默认 pytest。

### Changed

- `USER_GUIDE` 页眉与 §3.2 标明 **W1 / Pilot Complete**；明确 W2 排行榜未上线。

### Guarantees (user-visible)

- 默认 `pytest -q` 在无 LLM Key、无 LangSmith 下仍全绿（S2 可选测有标记）。
- 对外宣称须带波次名；不得暗示 Eval Ops（W2）已上线。

---

## Phase 2a · W2 — Eval Ops（进行中）

**Status:** 排行榜 API（票 30）+ 作业壳「评测」入口（票 31）+ 金标 I/O 钩子（票 32）已 Preview；手册收口（票 33）未关闭。  
W1 DoD（票 28）已满足。勿将 W2 Eval Ops 写成已完全交付；金标钩子 **不是** ≥300 运营完成。

---

## Unreleased

### Added

- 评测跑次持久化 + actor 归因（Issue 29 Preview）：`POST /eval/runs`、`GET /eval/runs?actor_user_id=`；复用 W0 演示用户；OpenEval 旁路；默认 `pytest -q` 不要求评测绿。`Rewrote from: REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR, REF-MISSIONS`。
- 评测排行榜可排序（Issue 30 Preview）：`GET /eval/leaderboard`；字段含实验名 / 主指标 `pass_rate` / 时间 / 提交者；单一真源本地 SQLite `eval_runs`；榜分不进 `machine_check` / 默认 CI。`Rewrote from: REF-CASE-EVAL-ADVISOR, REF-CASE-OPENEVALS, REF-MISSIONS`。
- 作业壳「评测」独立入口（Issue 31 Preview）：主导航「评测」；触发跑次 / 排行榜 / 提交者过滤；与门禁主路径视觉分离；`adjuster`/`supervisor` 协作演示；API 拒绝不假成功。`Rewrote from: REF-MISSIONS, REF-CASE-EVAL-ADVISOR`。
- 金标导入/导出钩子（Issue 32 Preview）：`POST /eval/gold-labels/import`、`GET /eval/gold-labels/export`、`python -m missions.gold_label_io`；记录关联 `case_id`；不实现双人标注全量；文案不宣称金标已达标。`Rewrote from: REF-CASE-OPENEVALS, REF-MISSIONS`。

### Not yet（仍属 W2 未交付）

- Eval Ops 手册收口（Issue 33）。

---

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
**Not in W1：** OpenEval 排行榜、多人协作评测台（属 **W2 Eval Ops**）。

### Added

- Chroma 索引 + 本地/云 embedding + 可重建（Issue 23）：`python scripts/rebuild_chroma_index.py`；规则 evaluate 零向量依赖。
- 混合检索挂 assist（Issue 24）：硬过滤 / 条款号短路 / 0.7·0.3 加权 / 三联门 / 关向量关键词降级；evaluate 不调向量。
- 作业壳 AI 辅助区检索来源摘要（Issue 25）：可见 doc / 条款项 / 版本；可采纳 vs 不可采纳诚实标注；不静默改写裁决草案。
- 真 LangSmith span + ledger `trace_id`（Issue 26）：配置 `LANGCHAIN_TRACING_V2` + Key 后 evaluate / assist / latch 上报；无 Key 不阻断；默认 `pytest -q` 不要求；S2 标记 `langsmith_integration`。
- OpenEval ↔ LangSmith 实验历史对比（Issue 27）：`python -m missions.openeval_langsmith`；不含排行榜/多人；不替代 `machine_check`。
- 套餐 L 验收清单 + Pilot 手册区分（Issue 28）：`本项目代码/claims-gate/docs/acceptance/package-l.md`（满配 / 关向量 / 关 LLM）；USER_GUIDE 区分「演示可无 Key」与「Pilot 须 LangSmith」；不进默认 pytest。

### Changed

- `USER_GUIDE` 页眉与 §3.2 标明 **W1 / Pilot Complete**；明确 W2 排行榜未上线（当时口径；现见 W2 节）。

### Guarantees (user-visible)

- 默认 `pytest -q` 在无 LLM Key、无 LangSmith 下仍全绿（S2 可选测有标记）。
- 对外宣称须带波次名；不得暗示 Eval Ops（W2）已上线（W1 关闭时口径）。

---

## Phase 2a · W2 — Eval Ops（Developer Preview）（2026-09）

**Status:** Developer Preview closed for W2 DoD（Issues 29–33）。  
**Scope:** OpenEval 排行榜 + 多人协作评测台 + 金标 I/O 钩子 + 用户手册 Eval Ops 操作说明；默认 `pytest -q` / S0 仍绿。  
**Honest deferral：** ≥300 人工金标运营未完成；不得宣称「金标已达标」。排行榜分数 ≠ `machine_check` 通过。

### Added

- 评测跑次持久化 + actor 归因（Issue 29 Preview）：`POST /eval/runs`、`GET /eval/runs?actor_user_id=`；复用 W0 演示用户；OpenEval 旁路；默认 `pytest -q` 不要求评测绿。`Rewrote from: REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR, REF-MISSIONS`。
- 评测排行榜可排序（Issue 30 Preview）：`GET /eval/leaderboard`；字段含实验名 / 主指标 `pass_rate` / 时间 / 提交者；单一真源本地 SQLite `eval_runs`；榜分不进 `machine_check` / 默认 CI。`Rewrote from: REF-CASE-EVAL-ADVISOR, REF-CASE-OPENEVALS, REF-MISSIONS`。
- 作业壳「评测」独立入口（Issue 31 Preview）：主导航「评测」；触发跑次 / 排行榜 / 提交者过滤；与门禁主路径视觉分离；`adjuster`/`supervisor` 协作演示；API 拒绝不假成功。`Rewrote from: REF-MISSIONS, REF-CASE-EVAL-ADVISOR`。
- 金标导入/导出钩子（Issue 32 Preview）：`POST /eval/gold-labels/import`、`GET /eval/gold-labels/export`、`python -m missions.gold_label_io`；记录关联 `case_id`；不实现双人标注全量；文案不宣称金标已达标。`Rewrote from: REF-CASE-OPENEVALS, REF-MISSIONS`。
- Eval Ops 手册收口（Issue 33 Preview）：`USER_GUIDE` §3.3 操作说明；明确排行榜分数 ≠ 合门禁 / ≠ `machine_check`；金标运营延后诚实标注；默认 `pytest -q` 仍绿。`Rewrote from: REF-MISSIONS`。

### Guarantees (user-visible)

- 默认 `pytest -q` 排除 `eval_bypass` 等标记；故意失败的评测跑次不进 S0 必过。
- 可称「Phase 2a Eval Ops 已交付（Preview）」时，须同时标注金标全量运营仍延后。

### Not in this wave

- ≥300 人工金标双标运营与周回归达标宣传
- 真连核心 L2 / 生产核赔作业壳
- 用评测分替代人闸或 `machine_check`

---

## Phase 2b · P-α — Claims Assist 证据地基（2026-09）

**Status:** Closed for α DoD（Issues 34–44；验收 `本项目代码/claims-gate/docs/acceptance/alpha-dod.md`）。  
**Scope:** Pilot cloud embedding 诚实默认；BM25；Demo 检索种子；citation Schema + 拒答 disposition；工具环 ACL；span 树；忠实规则夹具；Provider 文档。默认 `pytest -q` / S0 仍绿。  
**Honest deferral：** H4=`deferred`（薄切片 n&lt;10，禁止宣称 grounded）；H1/H2 召回有数属 β；连接状态 UI 属 β；γ（rerank / MultiQuery / fan-out / 灌榜）未触发、未上线。

### Added

- Assist citation Schema 槽 + 三联门（Issue 37 / GitHub #24）：`assist/adopt` 须携带 `doc_id`+`clause_item`+`doc_version`；非法 / 缺槽不可采纳（H3）；通过后仍 evaluate。作业壳无可用 citation 时禁用采纳。`Rewrote from: REF-COURSE-03`。
- 金标薄切片协议 + 导入导出加深（Issue 38 / GitHub #25）：双标角色占位 + 第三人裁决；`case_id` 往返；α 样例 n&lt;10 → **H4=`deferred`**，禁止宣称 grounded；禁止宣称 ≥300 运营。验收见 `本项目代码/claims-gate/docs/acceptance/gold-thin-slice.md`。`Rewrote from: REF-CASE-OPENEVALS`。
- 辅助拒答 disposition（Issue 39 / GitHub #26）：`assist_disposition=draft|abstain` + 原因枚举；`abstain` 禁用采纳；作业壳可见拒答原因；可 CTA 走人闸但不自动签发 `human_latch_token`。`Rewrote from: REF-MISSIONS`。
- Demo 检索种子 40 条冻结（Issue 36 / GitHub #23）：15 条款号 + 20 语义难例 + 5 拒答/冲突；**不得称金标**。`Rewrote from: 人写`。
- 工具环白名单 ACL（Issue 40 / GitHub #27）：仅 `retrieve` / `validate_citation` / `draft_slots`；越权写 latch/支付/evaluate 权威字段 = 0（H6）。`Rewrote from: REF-CASE-FC`。
- assist span 树 + 本地 JSONL 回放（Issue 41 / GitHub #28）。`Rewrote from: REF-CASE-EVAL-ADVISOR`。
- 引用忠实规则/夹具（Issue 42 / GitHub #29）；非 LLM-as-judge 主指标。`Rewrote from: REF-CASE-OPENEVALS`。
- α DoD 收口（Issue 44 / GitHub #31）：H3/H6/H7 可复现 + H1 种子存在 + S0 绿 + 手册诚实；解阻 β 与未来 SPEC-Q。验收见 `本项目代码/claims-gate/docs/acceptance/alpha-dod.md`。

### Changed

- Pilot 默认语义 embedding：`EMBEDDING_PROVIDER=cloud` + 独立 embedding Key；CI/rebuild 可用 `local` 哈希并标明**非语义**；缺 embedding Key 不得静默复用 `OPENAI_API_KEY`（Issue 34 / GitHub #21）。`Rewrote from: REF-MISSIONS`。
- 关键词腿 Jaccard → BM25（jieba）；条款号短路保留（Issue 35 / GitHub #22）。`Rewrote from: REF-CASE-RECALL, REF-CASE-KB`。
- Provider 清单写入 USER_GUIDE §3.4 + `.env.example` 分区；分 Key；不含连接状态 UI（Issue 43 / GitHub #30）。`Rewrote from: REF-MISSIONS`。

### Guarantees (user-visible)

- 默认 `pytest -q`：无 LLM / 无 LangSmith / 无 cloud embedding Key 仍绿（H7）。
- 非法 citation 不可采纳（H3）；工具环不写人闸/支付/evaluate 权威字段（H6）。
- 可称「2b-P-α 证据地基已关闭」时，须同时标注 H4 deferred、β/γ 未上线。

### Not in this wave

- H1/H2 召回门槛有数、三维 S2、夜间告警、连接状态、κ（属 **β**）
- γ：RRF / rerank / MultiQuery / fan-out / 往榜灌质量主指标（未触发）
- 流 Q（Missions A2/A3）— 另 SPEC；α DoD 已解锁切票

---

## Phase 2b · P-β — Claims Assist 可证伪质量（2026-09）

**Status:** Closed for β DoD（Issues 45–52；验收 `本项目代码/claims-gate/docs/acceptance/beta-dod.md`）。  
**Scope:** 条款项切块；冻结种子 H1/H2 有数；三维 S2；夜间告警；四步预算；κ；连接状态。默认 `pytest -q` / S0 仍绿。  
**Honest deferral：** H4=`deferred`（薄切片 n&lt;10，禁止宣称 grounded）；H5 为规则/夹具金标线（非 ≥300 运营）；γ（rerank / MultiQuery / fan-out / 灌榜）未触发、未上线；流 Q 另 SPEC。

### Added

- 冻结集 Recall@K / MRR（Issue 46 / GitHub #33 · S2/nightly）：`python scripts/run_recall_metrics_s2.py`；`pytest -m assist_quality`；对照 H1 Recall@1≥0.95、H2 Recall@5≥0.70 或 MRR≥0.55；报告默认 `artifacts/reports/recall_metrics_s2.json`；**不**进默认 `pytest -q` / `machine_check`。验收见 `本项目代码/claims-gate/docs/acceptance/recall-metrics-s2.md`。`Rewrote from: REF-CASE-RECALL`。
- 三维 S2 质量旁路（Issue 47 / GitHub #34）：`python scripts/run_three_dim_s2_quality.py`；检索 / 引用忠实 / 建议可用性一次拉通；主指标 `recall_metrics` + `rules_fixtures` + `rules_or_human`；**禁止** LLM 作唯一主指标；报告默认 `artifacts/reports/three_dim_s2_quality.json`；**不**红轨 A。验收见 `本项目代码/claims-gate/docs/acceptance/three-dim-s2-quality.md`。`Rewrote from: REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR`。
- 夜间 S2 质量门失败告警（Issue 48 / GitHub #35 · 旁路）：`python scripts/run_nightly_s2_alert.py`；失败可观测（本地 JSON + 日志 WARNING）；**不强制邮件**；**不**红轨 A / **不**进默认 `pytest -q`。验收见 `本项目代码/claims-gate/docs/acceptance/nightly-s2-alert.md`；手册 §3.8。`Rewrote from: REF-MISSIONS`。
- Assist 四步步数预算（Issue 49 / GitHub #36）：编排外形 `retrieve→gate→draft→self-check`（≤4）；响应可测 `orchestration_steps` / `orchestration_owner=app-owned`；未知/乱序/超步强制失败；口头不卖 LangGraph / 第二套 Agent 平台。验收见 `本项目代码/claims-gate/docs/acceptance/assist-four-step-budget.md`；手册 §3.9。`Rewrote from: REF-CASE-DELIBERATIVE`。
- Judge–human / κ 实填（Issue 50 / GitHub #37）：绑金标薄切片双标；标者间 Cohen κ 可报告；**κ≥0.60**（另须 n≥10 + 忠实率≥0.85 + 非合成）才可宣称 grounded；合成/外形样例不得冒充。验收见 `本项目代码/claims-gate/docs/acceptance/judge-human-kappa.md`；手册 §3.10。`Rewrote from: REF-CASE-OPENEVALS`。
- 连接状态只读（Issue 51 / GitHub #38）：`GET /provider/connection-status` + 作业壳「连接状态」；LLM / Embedding / LangSmith 已配置？降级？模型名？**永不回显 Key**。手册 §3.11。`Rewrote from: REF-MISSIONS`。
- β DoD 收口（Issue 52 / GitHub #39）：H1/H2 有数 + H4=`deferred` + H5 夹具金标线 + S0 绿 + 手册诚实；γ 未假上线。验收见 `本项目代码/claims-gate/docs/acceptance/beta-dod.md`；手册 §3.12。

### Changed

- 条款项级切块 + 父条款回填（Issue 45 / GitHub #32）：默认一 `clause_item` 一块；过长按段落切并回填父 id；人改 KB 源 markdown 后仍用 `python scripts/rebuild_chroma_index.py` 重建；citation 仍 `doc_id`+`clause_item`+`doc_version` 三联门。`Rewrote from: RAGFlow 模板切块协议；REF-CASE-KB`。

### Guarantees (user-visible)

- 默认 `pytest -q`：无 LLM / 无 LangSmith / 无 cloud embedding Key 仍绿。
- H1/H2 / 三维质量 / 夜间告警失败只影响 S2 旁路，不红轨 A。
- 可称「2b-P-β 可证伪质量已关闭」时，须同时标注 H4 deferred、γ 未上线。

### Not in this wave

- H4 grounded 宣称（须真双标 n≥10 + 忠实率/κ 达标）
- γ：RRF / rerank / MultiQuery / fan-out / 往榜灌质量主指标（未触发）
- 流 Q（Missions A2/A3）— 另 SPEC；完成旗隔离

---

## Phase 2b · Q — Missions Relay Honesty（2026-09）

**Status:** Closed for Q DoD / H8（Issues 53–56；验收 `本项目代码/claims-gate/docs/acceptance/q-relay-a2a3-dod.md`）。  
**Scope:** Schema-bound Orchestrator（A2）；Patch-capable Worker + `F-Q-DEMO-01`（A3）；Validator 独立 profile（轻量 A4 预备）。默认 `pytest -q` / S0 仍绿。  
**Honest deferral：** Q-A7 pause/resume / credential proxy **Deferred**；**未**宣称 A5 / Production latch；**无** Mission Control 作业台；完成旗与流 P 隔离（不用 Issues 44–52 / assist 分作出口）。

### Added

- Q DoD 收口（Issue 56 / GitHub #43）：H8 可演示；独立验收件；SPEC 无条件 DoD 勾选；S0 `314 passed, 25 deselected`（2026-09-16）。手册 §3.13。

### Changed

- OCR / 客户备注写入案件时会去掉首尾空白（全空白→空串）；仍只作可观察收纳，**不会**改写人闸 / `payout_ready`（示范特性 `F-Q-DEMO-01` / Issue 54）。

### Guarantees (user-visible)

- 默认 `pytest -q`：无 LLM / 无 LangSmith / 无 cloud embedding Key 仍绿。
- 可称「2b-Q 中继诚实已关闭」时，须同时标注未宣称 A5 / Production latch、Q-A7 Deferred。

### Not in this wave

- Q-A7 pause/resume；credential proxy；A5 Production latch
- Mission Control 生产作业台
- 用流 P Assist 质量分宣称 A3

---

## Unreleased

（无）

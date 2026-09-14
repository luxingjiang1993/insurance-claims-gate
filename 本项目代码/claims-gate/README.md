# claims-gate

本目录为 **条款门禁**（`insurance-claims-gate`）唯一可写产品代码根。

- 需求真源：`Managerial System/PRD/PRD_02_INSURANCE_CLAIMS_GATE.md`
- 工程真源：`Managerial System/SPEC/insurance-claims-gate/spec.md`
- 用户操作手册：`docs/user/USER_GUIDE.md`（Changelog：`docs/user/CHANGELOG.md`）
- 参考项目 ID：`docs/agents/ref-projects.md`（主基线 **`REF-MISSIONS`**）
- 术语：`CONTEXT.md`
- Agent 约定：`AGENTS.md`

## Issue 01 脚手架

`Rewrote from: REF-MISSIONS`

已落地：

- 理赔 HTTP 空壳（`src/claims_api/`）：L1 只读案件头，门禁态 `MATERIALS_INTAKE`
- Missions 空回路（`src/missions/`）：Orchestrator → Worker → Validator
- `machine_check` 按 `type` + `params` 分发
- validation contract JSON Schema 入账前硬停
- 默认 `inference_track=deterministic`；支付工具 ACL 默认拒绝
- 最小 `error_code` 表骨架

## Issue 02 条款 KB + citation 落库门

`Rewrote from: REF-CASE-KB, REF-MISSIONS`

已落地：

- 版本化主险 / 附加险 / 批单样例（支撑 SC-02 / SC-03）
- `KnowledgeBase.resolve_clause` / `validate_citation`：doc_id + clause_item + doc_version 三联门
- `POST /kb/citations/validate`；失败映射 `CITATION_NOT_IN_KB`
- `machine_check` type=`citation_in_kb`
- `retrieval_profiles`：`clause_v_current` / `endorsement_priority` / `handbook_ops` 配置位

## Issue 03 SC-01 一次补件 → 通赔建议

`Rewrote from: REF-MISSIONS, REF-COURSE-03`

已落地：

- `POST /claims/{id}/evaluate`：缺件→`supplement`/`PENDING_SUPPLEMENT`+`one_shot_hash`；齐件→`approve_recommend` 且 `payout_ready=false`
- `POST /claims/{id}/materials`、`/supplement/notify`（同 hash 拆轮失败）、`/documents/export`（补件 `DRAFT_EXPORT` 含第22条法义）
- `machine_check`：`sc01_one_shot_supplement_approve`、`one_shot_split_round_rejected`
- 默认轨 A `inference_track=deterministic`，不依赖 LLM

## Issue 04 SC-02 除外拒赔 + 文书分态 + 人闸

`Rewrote from: REF-MISSIONS`

已落地：

- 夹具 `CLM-SC02-001`（疾病摔伤）→ `reject_draft` + 条款项级 citations + `appeal_path`
- `reject_notice`：`DRAFT_EXPORT` 可无人闸；`EXTERNAL_NOTIFY` 须 `human_latch_token`（否则 `LATCH_REQUIRED`）
- `POST /claims/{id}/human-latch/approve|reject`；无人闸/`payout_ready` 恒 false，不触发银企
- `machine_check`：`sc02_exclusion_reject_latch`、`sc02_external_notify_requires_latch`

## Issue 05 SC-03 效力栈减赔 + 理算步骤

`Rewrote from: REF-CASE-KB, REF-MISSIONS, REF-COURSE-04`

已落地：

- 夹具 `CLM-SC03-001`（批单缩责）→ `reduce` / `ADJUSTING` + `authority_rank` / `overridden_by` + `calc_steps`
- `endorsement_priority` 检索先批单后主险；理算与批单冲突 fail-closed
- `reduction_notice` 导出复用 citations / calc_steps；`payout_ready` 恒 false
- `machine_check` type=`sc03_endorsement_stack_reduction`

## Issue 06 人闸权限矩阵（金额档 / 通融 / 预赔 / 调查冻决）

`Rewrote from: REF-MISSIONS`

已落地：

- `latch_matrix.py`：PRD §7 金额档 A–D + 决定类型 + 敏感上浮表驱动（不照搬转账限额）
- 通赔建议小额可直通草案、大额必闸；减赔按金额档且 A 起主管闸；响应含 `amount_tier` / `latch_tier`
- `POST .../decisions/exgratia|prepay`：必闸；通融伪主险通赔 citation → `VALIDATION_FAILED`
- `POST .../investigate/enter|unfreeze`：进入自动冻决；解除须人闸令牌；冻决期 `payout_ready=false`
- `POST .../peak-degrade`：仅补件+人审队列，禁止静默通赔
- `machine_check`：`latch_amount_tier_approve_diff` / `latch_exgratia_prepay_and_fake_citation` / `latch_investigate_freeze_unfreeze` / `latch_sensitivity_uplift` / `latch_peak_degrade_no_silent_approve`

## Issue 07 Router 确定性策略表 + ledger

`Rewrote from: REF-COURSE-12, REF-CASE-HYBRID, REF-MISSIONS`

已落地：

- `missions/router.py`：表驱动硬层 Router（非第四 LLM 角色）；冲突优先级 Human > Invest > Rules > RAG > OCR
- 规则 vs RAG 冲突 → fail-closed + `LATCH_REQUIRED` 进人闸；`handbook_ops` 不得独撑对外拒赔
- `evaluate` 响应与 `GET /claims/{id}/ledger` 含 `route_id` / `retrieval_profile` / `decision_type` / `validator_score`
- 轨 A 同夹具复跑可复现；`machine_check` type=`router_ledger_reproducible`

## Issue 08 L2 出款就绪 / 结案回写模拟

`Rewrote from: REF-MISSIONS, REF-CASE-FC`

已落地：

- `POST /claims/{id}/l2/payout-ready`：须有效人闸令牌 → `PAYOUT_READY` / `payout_ready=true`；不触发银企/支付适配器
- 无人闸令牌 → `LATCH_REQUIRED`，`payout_ready` 保持 false
- 夹具 `CLM-MISMATCH-001`：主数据不一致 → `MASTER_DATA_MISMATCH`，禁止出款就绪
- `POST /claims/{id}/l2/close`：可达 `CLOSED`；载荷不含自动支付指令（与出款解耦）
- 支付类工具 ACL 仍默认拒绝；`machine_check`：`l2_payout_ready_writeback` / `l2_close_without_payment`

## Issue 09 轨 B 隔离 + 威胁负例

`Rewrote from: REF-CASE-HYBRID, REF-MISSIONS`

已落地：

- 轨 B 隔离：`src/missions/track_llm_optional/` 配置占位 + `tests/track_llm_optional/`；`pytest.ini` 默认 `-m "not track_llm_optional"`
- 契约：轨 B 失败不阻断轨 A；默认 CI/Demo 禁止依赖 LLM 抽样才能通过 SC
- OCR/客户备注经 `absorb_user_controlled_text` 仅收纳可观察，不得翻转 `human_latch_required` / `payout_ready`
- `machine_check` type=`threat_inject_ocr_remark_no_latch_flip`

## Issue 10 Eval / 负例旁路（不替代 machine_check）

`Rewrote from: REF-CASE-OPENEVALS, REF-MISSIONS`

**旁路，非合门禁主缝。** 默认 CI 合门禁仍以 `machine_check` 为准；本入口失败可告警，不得改写人闸语义，不得要求 LLM 才能让轨 A 变绿。

已落地：

- `src/missions/eval_entry.py`：OpenEvals 风格评估器注册表 + `run_eval_negatives` / 机读报告
- 负例类：`hallucination_citation`（库外幻觉条款）、`exgratia_fake_citation`（通融伪通赔）；可选 `one_shot_split_round`
- `tests/eval/` 契约测试进默认 CI；套件 `-m eval_bypass`（不并入合门禁）
- 脚本：`python -m missions.eval_entry`（需 PYTHONPATH 含 `src`）

## Issue 11 Judge–human 合成抽检占位（P1-7）

`Rewrote from: REF-CASE-EVAL-ADVISOR, REF-MISSIONS`

**占位，不阻塞轨 A。** 真实核赔员 / 真实用户实测 / ≥300 金标运营**延后**；合成表不得冒充金标。

已落地：

- `ValidationReport.judge_human_agreement`（缺省 `null`）；`validation_done` 事件可挂同名字段
- `artifacts/spot_check_template.md`：手工抽检表模板（case_id / 系统裁决 / 合成双标+裁决 / 是否一致 / 备注）
- `artifacts/spot_check_sample_sc01.json`：基于 SC-01 的合成样例行（演示填法）
- `src/missions/spot_check.py`：加载表 + 计算一致率占位（评估流水线外形）

## Issue 12 轨 B 最小检索起草（RAG-CY）

`Rewrote from: REF-RAG-CY, REF-MISSIONS, REF-CASE-HYBRID`

**最小可跑前置，非完整质量门。** 完整方差预算 / 金标门槛数值化仍属 SPEC P2-4（open）；本票只交付隔离目录内「检索 → 辅助起草」。

已落地：

- `missions/track_llm_optional/retrieval.py`：检索入口（复用保险 KB + `retrieval_profiles`，含 `endorsement_priority`）
- `missions/track_llm_optional/pipeline.py`：`draft_assist` → 产物含 `inference_track=llm_optional`；默认 `enable_llm=False` 确定性假检索
- 规则 vs RAG 冲突 → `human_latch_required` + `R-CONFLICT-RULES-RAG`；`handbook_ops` 不得单独支撑对外拒赔
- 测试：`tests/track_llm_optional/test_min_rag_draft.py`（仅 `-m track_llm_optional`）；失败不阻断轨 A `pytest -q`

## Issue 13 Solo Demo / SC 黑盒一键脚本

`Rewrote from: REF-MISSIONS`

**个人验收 Demo，不替代 pytest/machine_check 合门禁。** 无需真实用户 / 作业台 UI。

已落地：

- `src/claims_api/demo_sc.py`：TestClient + 同语义 `machine_check` 跑 SC-01/02/03；失败非零退出
- 可选 `--extras`：拆轮拒绝 / 无人闸 EXTERNAL_NOTIFY 负例
- 一键入口（在 `本项目代码/claims-gate` 下）：`python scripts/run_sc_demo.py`
- 也可在**仓库根**执行：`python scripts/run_sc_demo.py`（根目录转发脚本）
- 或：`python -m claims_api.demo_sc`（需将 `claims-gate/src` 加入 PYTHONPATH）
- 不引入 L3/支付；不依赖真实 OCR/核心

## 当前阶段剩余（进阶段 2 前）

Issues **10–13** 已落地。清单与延后项见仓库  
`docs/agents/current-phase-remaining.md`。

## 运行

```bash
# —— 仓库根目录（推荐）——
pip install -r "本项目代码/claims-gate/requirements.txt"
python scripts/run_api.py
python scripts/run_sc_demo.py
python scripts/run_sc_demo.py --extras

# —— 或在 本项目代码/claims-gate 目录 ——
pip install -r requirements.txt
uvicorn claims_api.api:app --app-dir src --reload
pytest -q
python scripts/run_sc_demo.py
# 可选负例：
python scripts/run_sc_demo.py --extras
# 显式跑轨 B 最小 RAG（不并入默认合门禁）：
pytest -m track_llm_optional -q
# 显式跑 eval 负例旁路（不替代 machine_check）：
pytest -m eval_bypass -q
python -m missions.eval_entry
# OpenEval → LangSmith 实验历史对比（旁路；需 Key 才真上报）：
python -m missions.openeval_langsmith
pytest tests/langsmith_integration/test_openeval_experiment_real.py -m langsmith_integration -o addopts=
```

## Issue 27 OpenEval ↔ LangSmith 实验历史对比

`Rewrote from: REF-CASE-OPENEVALS, REF-CASE-EVAL-ADVISOR, REF-MISSIONS`

**旁路，非合门禁主缝。** 最小数据集 run + LangSmith 实验历史对比外形；**不含**排行榜与多人协作（W2）。不替代 `machine_check`；默认 `pytest -q` 不要求 LLM/LangSmith。

已落地：

- `src/missions/openeval_langsmith.py`：`run_openeval_experiment` / `list_experiment_history`；可注入 Fake Client
- 复用 Issue 10 `DEFAULT_EVAL_SUITE` 负例最小集
- 默认测：`tests/eval/test_openeval_langsmith_history.py`（S0 隔离 + `-m eval_bypass` Fake 实验）
- S2：`tests/langsmith_integration/test_openeval_experiment_real.py`（真 Key；缺则 skip）

**S2 / mock 策略：**
1. **默认/S0：** FakeLangSmithExperimentClient（无网络）。不得用 mock 冒充 Pilot Complete。
2. **真实验：** `pytest -m langsmith_integration`，需真实 Key；缺则 skip。
3. LangSmith UI / 实验分 **不**替代 `machine_check`。

## Issue 16 作业壳：登录 + 案件只读浏览

`Rewrote from: REF-MISSIONS`

已落地：

- `workshell/`：Vite + React + TS 薄客户端；登录、案件列表/详情只读浏览
- HTTP：`GET /claims`；`GET /claims/{id}` 含 `document_status` / `payout_ready`
- CORS 允许作业壳源；无 BFF；API 拒绝原样展示
- `viewer` 壳内无写操作入口
- 启动：`cd workshell && npm install && npm run dev`（API 先起）

## Issue 17 作业壳：SC 规则路径

`Rewrote from: REF-MISSIONS`

已落地：详情页材料登记 / evaluate / 一次补件 / 裁决草案查看；无 LLM Key 可点完；拒绝不假成功。

## Issue 18 作业壳：人闸 + 文书分态

`Rewrote from: REF-MISSIONS`

已落地：详情页人闸批准/驳回（supervisor 获 API 令牌；adjuster 批闸拒绝不假成功）；拒赔 `DRAFT_EXPORT` 可预览；`EXTERNAL_NOTIFY` 无人闸失败时 UI 不升对外。

## Issue 20 作业壳：AI 辅助建议区

`Rewrote from: REF-MISSIONS, REF-CASE-HYBRID`

已落地：详情页 AI 辅助区须显式点击才调用；无 Key 降级提示可见；辅助建议与裁决草案分标签；「送交规则校验（采纳）」走 `assist/adopt`→evaluate；UI 标明非终裁、无秒赔误导；`viewer` 不展示该写入口。

## Issue 23 Chroma 索引 + embedding + 可重建

`Rewrote from: REF-CASE-RECALL, REF-RAG-CY, REF-MISSIONS`

已落地：

- `missions/chroma_index/`：将 `knowledge_base/` 条款块写入持久 Chroma（默认 `data/chroma`）
- 默认 `EMBEDDING_PROVIDER=local`（确定性本地向量）；`cloud` 走独立 embedding Key
- 重建入口：`python scripts/rebuild_chroma_index.py`（可重复执行）
- 规则 evaluate 路径不依赖 Chroma（见 `tests/test_chroma_index_rebuild.py`）

勿在仓库根直接执行 `uvicorn ... --app-dir src`（会找不到 `claims_api`）；请用 `python scripts/run_api.py` 或先 `cd` 进 `claims-gate`。

# claims-gate

本目录为 **条款门禁**（`insurance-claims-gate`）唯一可写产品代码根。

- 需求真源：`Managerial System/PRD/PRD_02_INSURANCE_CLAIMS_GATE.md`
- 工程真源：`Managerial System/SPEC/insurance-claims-gate/spec.md`
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

## 运行

```bash
pip install -r requirements.txt
uvicorn claims_api.api:app --app-dir src --reload
pytest -q
```

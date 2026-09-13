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

## 运行

```bash
pip install -r requirements.txt
uvicorn claims_api.api:app --app-dir src --reload
pytest -q
```

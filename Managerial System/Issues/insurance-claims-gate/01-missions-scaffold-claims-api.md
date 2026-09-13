# 01: Missions 换垂直脚手架 + 理赔 HTTP 空壳 + machine_check 分发器

**Status:** done

**Blocked by:** None (can start immediately)

**ref_id:** REF-MISSIONS

**Backlog:** P1-2, P1-4

**Rewrote from:** REF-MISSIONS

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `project 多agent/src/missions/runner.py` | 三角色回路、人闸阻塞相位 |
| 2 | `project 多agent/src/missions/orchestrator.py` | 契约先行、写出带 `machine_check` 的 contract |
| 3 | `project 多agent/src/missions/worker.py` | Worker 实现边界（不自审） |
| 4 | `project 多agent/src/missions/validator.py` | HTTP 黑盒验收、只评判不改产品代码 |
| 5 | `project 多agent/src/missions/checks.py` | **按 `type` 分发**的 `run_machine_check`（换域时替换检查体） |
| 6 | `project 多agent/src/missions/models.py` | Mission / Assertion / MachineCheck / HumanApproval 外形 |
| 7 | `project 多agent/schemas/validation_contract.schema.json` | 非法契约硬停（P1-2） |
| 8 | `project 多agent/src/transfer_api/api.py` + `service.py` + `limits.py` | 被测产品 HTTP 外壳与 `error_code` 模式（换皮成理赔域） |
| 9 | `project 多agent/tests/conftest.py` | TestClient 夹具写法 |

## What to build

从 Missions 中继换到个人意外险理赔垂直：产品代码落在本项目代码根；Orchestrator / Worker / Validator 可跑通空回路；理赔 HTTP API 可启动；至少能只读拉到案件头并进入材料受理态；`machine_check` 仅按 `type` + `params` 分发；默认推理轨为确定性轨；非法 validation contract 在入账前 JSON Schema 硬停；冻结最小 `error_code` 表骨架。不实现银企支付，不新增第四个「核赔 Agent」角色。

## Acceptance criteria

- [x] `claims-gate` 可启动；L1 只读可返回案件号、保单号、条款版本、出险日等最低字段，门禁态可达 `MATERIALS_INTAKE`
- [x] Orchestrator → Worker → Validator 空回路可跑；非法 validation contract 不得开工（JSON Schema 硬停）
- [x] `machine_check` 分发器按 `type` + `params` 执行，不存在按断言 ID（如 A-00x）硬编码开关
- [x] 默认响应/契约标注 `inference_track=deterministic`；支付类工具默认无权限
- [x] 最小 `error_code` 表已登记（至少含 `VALIDATION_FAILED`、`LATCH_REQUIRED`、`CITATION_NOT_IN_KB`、`DOCUMENT_STATUS_FORBIDDEN`、`MASTER_DATA_MISMATCH` 的占位语义）
- [x] 实现只写入约定产品代码根；历史参考仓保持只读；handoff 含 `Rewrote from: REF-MISSIONS`



## Comments

- 2026-09-13：to-tickets 批准 defaults 后落盘。
- 2026-09-13：Issue 01 实现完成（`本项目代码/claims-gate/`）；Rewrote from: REF-MISSIONS；评审 Important 已修（artifacts 隔离 + ACL 挂接只读入口）。


# 03: SC-01 一次补件 → 补传 → 通赔建议（轨 A）

**Status:** ready-for-agent

**Blocked by:** 01

**ref_id:** REF-MISSIONS, REF-COURSE-03

**Backlog:** P1-6

**Rewrote from:** REF-MISSIONS, REF-COURSE-03

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `project 多agent/src/transfer_api/api.py` + `service.py` | 被测域 HTTP + 领域服务换皮模板 |
| 2 | `project 多agent/src/missions/checks.py` | 为补件/`one_shot_hash`/通赔建议注册新 `machine_check.type` |
| 3 | `project 多agent/src/missions/orchestrator.py` | 如何为场景写出带 params 的 assertions（勿按断言 ID 分支） |
| 4 | `project 多agent/src/missions/models.py` | 裁决/契约响应字段可扩展点 |
| 5 | `project 多agent/scripts/run_interview_demo.py` | Demo/夹具驱动黑盒跑法 |
| 6 | `03_单次模型请求与结构化输出控制/examples/00_direct_json_request.py` | 结构化 JSON 外形约束 |
| 7 | `03_单次模型请求与结构化输出控制/examples/meeting_minutes_contract.py` | 契约式结构化输出样例 |
| 8 | `03_单次模型请求与结构化输出控制/examples/02_langchain_structured_output.py` | schema 约束备选（轨 A 仍以确定性规则为主） |

## What to build

端到端跑通 SC-01（确定性轨）：缺发票案件材料不齐时进入待补件，一次列出全部缺项并带 `one_shot_hash`；补件通知含缺项中文名、是否必须、示例说明，并固定引用一次性补正法义文案；客户补传后重评，旧缺项已满足才允许新清单；补齐后产出通赔建议裁决草案。同 hash 下拆轮补件必须失败。补件文书草稿字段齐全。默认 CI/Demo 不得依赖 LLM 抽样才能绿。

## Acceptance criteria

- [ ] SC-01 夹具经 HTTP 黑盒：缺发票 → 补件 → 补传 → 通赔建议草案
- [ ] 补件清单完整且带稳定 `one_shot_hash`；同 hash 拆轮补件 machine_check 失败
- [ ] 补件通知含缺项中文名、是否必须、示例说明，以及一次性补正法义文案锚点
- [ ] 裁决含 `decision_type`、`gate_status`、`document_status`、`payout_ready`；未按规定人闸前 `payout_ready=false`
- [ ] 补件文书可导出为 `DRAFT_EXPORT`（补件默认可自动，不必人闸升对外）
- [ ] 对应 machine_check 类型注册并在轨 A 下稳定绿；`inference_track=deterministic`
- [ ] handoff 含 `Rewrote from: REF-MISSIONS, REF-COURSE-03`

## Comments

- 2026-09-13：to-tickets 批准 defaults 后落盘。

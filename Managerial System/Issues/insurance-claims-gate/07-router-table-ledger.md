# 07: Router 确定性策略表 + 冲突 fail-closed + ledger

**Status:** ready-for-agent

**Blocked by:** 03, 04, 05

**ref_id:** REF-COURSE-12, REF-CASE-HYBRID, REF-MISSIONS

**Backlog:** P1-1

**Rewrote from:** REF-COURSE-12, REF-CASE-HYBRID, REF-MISSIONS

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `12_模型驱动的决策模式及复杂回路设计（上）/examples/product_plan_patterns.py` | 决策模式/回路拆分外形 |
| 2 | `12_模型驱动的决策模式及复杂回路设计（上）/第12课_模型驱动的决策模式与复杂回路（上）——从一次生成到任务计划.md` | Router/计划层概念（落地须降为确定性表） |
| 3 | `CASE-投顾AI助手（混合式）/hybrid_wealth_advisor_langgraph.py` | 协调层 `assess_query` / `processing_mode` 分流（**只借表驱动思想**，禁止做成 LLM 核赔角色） |
| 4 | `project 多agent/src/missions/rag.py` | `retrieval_profile` 记入检索 |
| 5 | `project 多agent/src/missions/store.py` | ledger / 状态持久化外形 |
| 6 | `project 多agent/src/transfer_api/audit.py` | 审计记录字段写法 |
| 7 | `project 多agent/src/missions/models.py` | handoff / report 可挂 `route_id` 的扩展点 |
| 8 | `project 多agent/src/missions/checks.py` | 冲突 fail-closed、handbook 不可独撑拒赔的检查类型 |

硬约束（P1-1）：Router = 确定性策略表挂在 Missions 硬层，不另起第四 Agent。

## What to build

将 SC 路径上的路由从硬编码演进为显式确定性策略表（硬层，禁止写成独立 LLM「核赔角色」）。多路由冲突按 Human > Invest > Rules > RAG > OCR 仲裁；规则与条款 RAG 冲突时失败关闭进人闸，不静默采信一侧。`handbook_ops` 不得单独作为对外拒赔唯一依据。Ledger 记录 `route_id`、`retrieval_profile`、`decision_type`、`validator_score`。默认绿门路径上 Router 结果须可由确定性轨复现。

## Acceptance criteria

- [ ] Router 以表/配置驱动，文档与实现均不引入第四个 LLM 核赔角色
- [ ] 冲突优先级 Human > Invest > Rules > RAG > OCR 可测；规则 vs RAG 冲突 → fail-closed + 人闸
- [ ] `handbook_ops` 单独支撑对外拒赔时失败
- [ ] 每案 ledger（或等价审计记录）含 route_id、retrieval_profile、decision_type、validator_score
- [ ] 轨 A 下同一夹具重复跑 Router 结果可复现
- [ ] handoff 含 `Rewrote from: REF-COURSE-12, REF-CASE-HYBRID, REF-MISSIONS`

## Comments

- 2026-09-13：to-tickets 批准 defaults 后落盘。

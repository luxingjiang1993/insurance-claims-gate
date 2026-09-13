# 09: 轨 B 隔离占位 + 威胁负例机检

**Status:** ready-for-agent

**Blocked by:** 03, 04, 05

**ref_id:** REF-CASE-HYBRID, REF-MISSIONS

**Backlog:** P0-1, P1-3

**Rewrote from:** REF-CASE-HYBRID, REF-MISSIONS

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `CASE-投顾AI助手（混合式）/hybrid_wealth_advisor_langgraph.py` | `reactive` vs `deliberative` 双模式隔离灵感 → 映射 `deterministic` / `llm_optional` |
| 2 | `project 多agent/src/missions/checks.py` | 轨 A 合门禁入口；轨 B 测试不得挂进默认分发全绿 |
| 3 | `project 多agent/tests/compliance/test_audit_failures.py` | 合规/注入类失败用例风格 |
| 4 | `project 多agent/src/transfer_api/service.py` | 用户可控字段不得改写限额/规则（映射：OCR/备注不得翻人闸） |
| 5 | `project 多agent/src/missions/worker.py` | Worker 工具边界；支付类保持无权限 |
| 6 | `project 多agent/DESIGN_PHILOSOPHY.md` | 诚实自治、失败关闭（叙事约束） |

轨 B 完整 RAG（`RAG-cy` 等）本期只允许隔离占位，禁止并入默认 CI。勿用 `OpenManus-*` 替代 Missions 中继。

## What to build

落实推理双轨隔离：轨 B（`llm_optional`）仅允许在独立目录/标记下存在，方差与人闸策略独立配置，失败不得阻断轨 A 合门禁；默认 CI/Demo 若调用 LLM 才能通过 SC 视为 SPEC 违规。落地最小威胁负例：OCR 文本与客户备注中的提权文案不得翻转 `human_latch_required` / `payout_ready`。本期不交付完整轨 B 质量门或真实 RAG 绿门。

## Acceptance criteria

- [ ] 存在明确的轨 B 隔离目录或测试标记（如 `track_llm_optional`）；默认 CI 只跑轨 A
- [ ] 文档/契约声明：轨 B 失败不阻断轨 A；默认绿门禁止依赖 LLM 抽样
- [ ] 注入负例夹具：备注/OCR 含提权文案时，人闸要求与 `payout_ready` 不被翻转
- [ ] 至少一条 machine_check 覆盖上述注入负例
- [ ] 不把 OpenManus 或轨 B 框架替代 Missions 中继主链
- [ ] handoff 含 `Rewrote from: REF-CASE-HYBRID, REF-MISSIONS`

## Comments

- 2026-09-13：to-tickets 批准 defaults 后落盘。

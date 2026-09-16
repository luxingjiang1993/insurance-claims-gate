# Claims Gate — 自治阶梯一页纸（N7）

| 字段 | 内容 |
|------|------|
| 配套 | 一页纸 `interview-one-pager.md` · 时序 `diagrams/claims-gate.seq-missions.html` |
| 口径 | 截至 2026-09-16；**A ≠ Integration L**；不宣称 A5 / L3 |

---

## 两套字母，不要混

| 梯子 | 量什么 | 本期怎么说 |
|------|--------|------------|
| **A0–A5** | 工程中继（Orchestrator / Worker / Validator）能诚实到哪一档 | 已交付到 **A2 / A3** |
| **Integration L1/L2/L3** | 产品与核心的读写 / 支付面 | **L1** 只读案件头已有；**L2** 出款就绪为 **Integration-Ready**（InMemory+Recorded，非真连现网 / 禁止「已接核心」）；**L3** 银企直连为本期 **Won't** |

作业壳完成 ≠ 升档到 A3–A5。UI 是产品表面，不是 Production latch。

---

## A0–A5（工程中继）

| 档 | 含义 | Claims Gate 现状 |
|----|------|------------------|
| **A0** | 编排剧本 / 固定契约 | 历史演示基线；不要用它冒充多代理生产 |
| **A1** | 失败即关；HTTP 黑盒；`machine_check` | 轨 A 地板；默认 `pytest -q` 仍绿 |
| **A2** | LLM 产出经 JSON Schema 硬停 | **已交付**（Q / H8：契约入账前硬停） |
| **A3** | Worker 真 patch + commit hash | **已交付**（`F-Q-DEMO-01`；非假 git） |
| **A4** | 独立 Judge / 校准路径 | **轻量预备**：Validator **独立 profile** + 零产品写；**不是**生产 A4 |
| **A5** | Production latch（预算、暂停、凭证代理、审计） | **Deferred**（Q-A7 未切票；无 Mission Control） |

口头句：**中继诚实到 A2/A3；A4 只有独立校验外形；未宣称 A5。**

---

## Integration L1/L2/L3（产品）

| 档 | 含义 | 现状 |
|----|------|------|
| **L1** | 只读案件头 | 已交付 |
| **L2** | 核心回写（如 `PAYOUT_READY`） | **Integration-Ready**：InMemory + Recorded Provider；须 `human_latch_token`；**禁止**宣称已接核心 / Deployed |
| **L3** | 自动出款 / 银企 | **不做**；`PAYOUT_READY` ≠ 已打款 |

---

## 禁句

- 「已经 A5 / 生产自动出款 / Mission Control 作业台」
- 「作业壳做完所以是生产多代理」
- 用 A 档字母去编号 L1/L2/L3

# Claims Gate — 面试一页纸

| 字段 | 内容 |
|------|------|
| 产品 | **条款门禁（Claims Gate）** — 个人意外险理赔裁决辅助 |
| 档位 | **面试诚实 8 分档** · 副标题 **Integration-Ready**（Ready ≠ Deployed） |
| 代码 | `本项目代码/claims-gate/` |
| 截至 | 2026-09-16 · Phase 1 + 2a（W0–W2）+ 2b（P-α/P-β + Q）+ **2c Live Honest Seams（G0/G2/G3）** |
| 架构图 | `docs/agents/diagrams/claims-gate.architecture.html` |
| 口述轨 | `docs/agents/interview-talk-track.md`（N2） |
| 演示脚本 | `docs/agents/interview-demo-script.md`（N3；默认无 Key + Live 分支） |
| 人闸时序 | `docs/agents/diagrams/claims-gate.seq-latch.html`（N4） |
| Assist 时序 | `docs/agents/diagrams/claims-gate.seq-assist.html`（N5） |
| Missions 时序 | `docs/agents/diagrams/claims-gate.seq-missions.html`（N6） |
| 自治阶梯 | `docs/agents/interview-autonomy-ladder.md`（N7，A ≠ L） |
| 诚实表 | `docs/agents/interview-honesty-table.md`（N8） |
| 威胁半页 | `docs/agents/interview-threat-model.md`（N10） |
| S2 指标卡 | `docs/agents/interview-s2-metrics.md`（N11） |

---

## 一句话

用**可回归的契约 + 人闸**辅助持牌核赔，而**不替代**终裁、**不触发**银企支付。

---

## 要解决的问题

核赔系统若把 LLM/RAG 直接接进裁决，会把「相似检索」和「合门禁」混为一谈。本产品把权威留在**确定性轨 A + 人闸**；AI 只走**可拒答、可证伪、可旁路失败**的 Assist。

---

## 不变量（口头可复述）

1. 无人闸令牌 → 不得 `PAYOUT_READY`  
2. Worker 不自审自批；Validator 不改产品代码  
3. 默认 `pytest -q` **无 LLM / 无 LangSmith** 仍须绿  
4. 评测分 / 召回分 **≠** `machine_check` 合门禁  
5. 不做 L3 银企直连 / 「秒赔」叙事

---

## 已交付（可演示）

| 层 | 你能说什么 | 怎么证 |
|----|------------|--------|
| 轨 A 主路径 | SC-01/02/03：补件、除外拒赔、效力栈减赔 | `python scripts/run_sc_demo.py`；作业壳规则路径 |
| 作业壳 · 2a | 三角色 RBAC、人闸、文书分态、Eval Ops Preview | `workshell` + USER_GUIDE §3 |
| Assist · 2b-P | BM25+Chroma、citation 三联门、拒答、≤4 步；H1/H2 有数（S2） | α/β DoD；`assist_quality` 旁路 |
| Missions · 2b-Q | A2 Schema 硬停 + A3 真 patch+commit（H8） | `q-relay-a2a3-dod.md`；相关 pytest |
| Live · 2c G0 | 有 Key 真 Assist；缺 Key 降级；双 Key cloud 重建 | `live-pilot-g0.md`；连接状态双绿 |
| 双剖面 · 2c G2 | 先报剖面再报数字；`demo_seed_eval` ∥ `pilot_cloud_embed` | `interview-s2-metrics.md`；`run_recall_metrics_s2.py` |
| L2/OCR · 2c G3 | **Integration-Ready**（InMemory/Stub + Recorded）；非 Deployed | 契约测；威胁注入不翻 latch |

---

## 故意不做 / 诚实边界（被追问时先说）

| 项 | 状态 |
|----|------|
| H4 grounded 宣称 | **deferred**（金标薄切片 n&lt;10；开场须承认） |
| 面试条 9 / grounded | **本窗口不做**（无第二核赔标人） |
| γ（rerank / MultiQuery / fan-out / 灌榜） | **未触发、未上线** |
| ≥300 人工金标运营、真连 L2、真 OCR | **延后**（现有 Adapter = Ready ≠ Deployed） |
| Q-A7 / A5 Production latch | **Deferred**（未宣称） |
| Mission Control 生产作业台 | **无** |

---

## 60 秒开场稿

> 我做的是保险理赔的**条款门禁**：系统出裁决草案和条款项引用，但出款就绪必须过人闸。默认合门禁是确定性规则，不依赖大模型。AI 辅助是旁路——能拒答、引用不过门就不可采纳，分数也不冒充合规。工程上 Missions 中继做到了 Schema 硬停和真 patch。本窗口档位是**面试诚实 8 分档**、副标题 **Integration-Ready**——**H4 仍 deferred，不宣称 grounded，也不冲面试条 9**；Ready 不等于 Deployed。

---

## 深挖指针（别一次倒完）

- 用户面：`docs/user/USER_GUIDE.md`（页眉诚实边界）  
- 验收：`本项目代码/claims-gate/docs/acceptance/`（α / β / Q / Live G0 / 套餐 L）  
- 需求/哲学：PRD-02、`DESIGN_PHILOSOPHY.md` I1–I8、自治阶梯 A≠ Integration L  
- 票图：Issues 01–61 实现侧已关（含 G4 文案已同步）；**未关票 ≠ 已冲 9**；Issue 62 为 2c DoD 收口；Q-A7 未切票  

---

## 一句话收尾

**权威在轨 A + 人闸；Assist 可证伪；中继诚实到 A2/A3；Live + 双剖面 + Integration-Ready；未宣称 A5 / grounded / 面试条 9 / 生产自动出款。**

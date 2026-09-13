# 补充说明：REF 改写 · 第二阶段 / 扩面（草案）

| 字段 | 内容 |
|------|------|
| 状态 | `draft-supplement`（非正式宪法 / 非正式 SPEC） |
| 日期 | 2026-09-13 |
| 用途 | 供未来生成正式文档（Constitution 附录、PRD 扩面、SPEC P2、新 `REF_*` 表）时参考 |
| 前置正式真源 | `docs/agents/ref-projects.md`（本期）、`DESIGN_PHILOSOPHY.md`（I1–I8）、`SPEC/insurance-claims-gate/spec.md` |
| 评审 | 硅谷技术合成评委会 2026-09-13（均分 8.2；清单二有条件通过） |

**效力声明：** 本文**不**修改 I1–I8，**不**废止 PRD Won't，**不**授权 agent 按下文放松绿门或另起中继。仅当人类架构师将对应条目写入正式 PRD/SPEC/Constitution 并改状态后，下文才可执行。

---

## 1. 何时可消费本文

同时满足：

1. 本期 Issues `01`–`09` 轨 A 合门禁稳定（或书面豁免剩余票）。  
2. 人类决定开扩面立项（新 PRD 切片或 SPEC 大修订）。  
3. 下文 **N 标准** 中拟放松项已写入 `Managerial System/Constitution/` 附录或修订正文。  
4. 新 `REF_*`（若入库代码）已登记进 `ref-projects.md` 全量目录，路径落在 `历史项目代码供参考/`。

---

## 2. 新判断标准草案（N1–N11）

扩面后**可能**覆盖旧约束；「仍建议保留」列为硬底线候选，正式修宪时应显式取舍。

| ID | 新标准（草案） | 可能放松/替换 | 仍建议保留的硬底线 | 正式落盘建议 |
|----|----------------|---------------|--------------------|--------------|
| N1 | 双轨合门禁可分立：轨 B 可有独立 CI | 「轨 B 永不进默认 CI」 | 轨 A 须可单独全绿；轨 B 失败默认不阻断轨 A | Constitution 附录 + SPEC Testing |
| N2 | 编排可多角色只读 fan-out | I4 少并行（仅只读检索/审查） | 共享可变工件单 Writer；Validator 不改被测代码（I1） | Constitution I4 注释 |
| N3 | 记忆 OS ≠ 聊天；可双总线 | I3 仅 ledger → ledger + 情景记忆 | 人闸/契约/出款就绪仍硬层；记忆写入须 schema + TTL | Constitution I3 + 数据契约 |
| N4 | 文档管线可重（多模态解析） | 夹具 KB 手工入库为主 | 对外 citation 仍 `doc_id + clause_item + version` | SPEC 决策 17 保持；解析旁路另节 |
| N5 | 推理本地/生产分流 | 轨 B 可绑 Ollama/vLLM/llama.cpp | 不把推理引擎改写进业务域；须标 `inference_track` | 运维 Runbook，非产品 SPEC 主文 |
| N6 | 沙箱成默认执行面 | Daytona/E2B「本期非目标」可升格 | 沙箱内禁支付工具；无 L3 除非改 Won't | SPEC Out of Scope 修订 |
| N7 | 可观测可外挂平台 | 仅 ledger → + Langfuse/AgentOps | route / retrieval_profile / latch 仍落 durable | SPEC ledger 节 + 运维 |
| N8 | 交互壳可独立产品化 | Dify/Kotaemon 等作业台 | 门禁 API 与人闸不得在低代码里「软通过」 | 新 PRD「作业壳」或 Won't 澄清 |
| N9 | 工程 Agent ≠ 域 Agent | SWE-agent/Aider 可进工程中继参考 | 不得把编程 ACI 当核赔 Router | AGENTS 改写规则 |
| N10 | 微调旁路合法化 | Unsloth / LLaMA-Factory 可服务域模型 | 微调模型不得单独满足合门禁；仓与 CI 物理隔离 | 独立「模型定制」仓约定 |
| N11 | L3 / 真联核心另宪法 | W-04 / 无银企可废止（仅若新 PRD） | 人闸前不得发支付指令（除非监管书面接受） | **必须新 PRD**，禁止口头废止 |

### 2.1 评委会对 N1 的强制条件（升格前必写数值/契约）

- `track_llm_optional`（或等价标记）测试目录隔离。  
- 轨 B CI 失败 **不**阻断轨 A 合门禁（除非人类显式合并质量门并改 SPEC）。  
- 方差预算与金标门槛**数值化**后再谈「轨 B 进扩面 CI」。

### 2.2 评委会对 N2 / N3 的附加机检建议

- 只读 fan-out：`owns_paths=none`（或只读路径集）可机检。  
- Letta 类记忆写入：强制 schema + TTL，防止污染 ledger。

---

## 3. 扩面改写候选（清单二 · 有条件通过）

### 3.1 入库配额（P1 共识）

- **首批扩面只许新增至多 2 个** 外部/新 `REF_*` 代码目录（防参考仓膨胀）。  
- 建议优先组合（二选一组合，勿一次全上）：  
  - **A：** LightRAG（检索增量）**或** RAGFlow（解析旁路，非整框架替门禁）  
  - **B：** `REF-CASE-LANGFUSE` 强化 **或** AgentOps 对照（可观测二选一）  
- 其余候选保持「文档级 / 依赖级」，不入库代码。

### 3.2 候选表（主题 → 改写姿态 → 触发条件）

| 主题 | 候选 | 改写姿态 | 触发条件（举例） |
|------|------|----------|------------------|
| 条款/多模态入库 | RAGFlow；次选 Kotaemon | 借解析/切块；换效力栈内容 | 真 OCR、图表/手写、条款变更回归（SPEC P2-3） |
| 图谱/增量 KB | LightRAG | 增量更新与检索画像 | 批单频繁变更；须证明不破坏 `endorsement_priority` |
| 长期记忆助手 | Letta | 记忆分层 → handoff/会话态 | 跨案核赔员助手；非替代人闸（N3） |
| 只读多专家 | CrewAI / AgentScope | 角色委派外形；挂 Missions 外 | 并行检索/双人审查模拟；禁自审自批（N2） |
| 工具协议 | FastMCP、MCP Servers | 协议与 ACL（仓内已有 MCP CASE 时优先强化既有） | 多系统只读集成 |
| 轨 B 运行时 | Ollama / vLLM / llama.cpp | **依赖文档级**，非业务改写 | 本地隐私试点或批量起草（N5） |
| 沙箱 | E2B；`REF-CASE-DAYTONA` | 执行隔离 | Worker 跑不可信脚本（N6） |
| 可观测 | AgentOps；`REF-CASE-LANGFUSE` | 追踪/成本/回放 | 生产试点、KPI 看板（N7） |
| 作业/对话壳 | Dify / Flowise / Kotaemon | UI 壳；裁决仍走 API | 内测作业台；**禁止**写 `machine_check`（N8） |
| 浏览器/影像 | Browser Use；`REF-OPENMANUS-GUI` | 仅影像/官网核验旁路 | **须先有「影像核验」子 PRD** 再开 GUI 参考（评委 Jim Fan） |
| 工程侧写码 | SWE-agent / Aider | ACI、补丁、Git 纪律 | 加强 Missions Worker 工程能力（N9） |
| 域模型定制 | Unsloth / LLaMA-Factory；ToolLLM 数据 | 训练旁路仓 | 中文条款理解专项；与产品仓隔离（N10） |
| 深思/问答旁路 | `REF-CASE-DELIBERATIVE`、`REF-CASE-REACTIVE-QA`、`REF-OPENMANUS-RAG` | 轨 B 或条款问答台 | 辅助起草/指引问答；勿替 Orchestrator |
| 端到端编排课 | `REF-COURSE-05`、`REF-COURSE-11` | 会话/IM 型编排 | 核赔员 IM 入口另立项时 |

### 3.3 扩面仍建议排除（除非新 PRD 明文）

- 用 OpenManus / CrewAI **替换** Missions 主中继。  
- 用 Dify 工作流代替 Validator / `machine_check`。  
- 「秒赔」叙事包装责任争议案。  
- 无人最终拒赔且不可申诉。  
- 将公开「2026 完整技术栈」整表升为改写基线。

### 3.4 协议阅读（与本期一致，扩面亦不升格）

Gorilla、ToolLLM、mcp-marketplace：仅协议/数据形态阅读，不进改写列（见 `ref-projects.md`）。

---

## 4. 未来正式文档生成清单（给架构师）

将本草案升格时，建议按序产出：

| 步骤 | 正式工件 | 从本文取用 |
|------|----------|------------|
| 1 | `DESIGN_PHILOSOPHY.md` 附录「扩面不变量 N*」或修订 I3/I4 注释 | §2 |
| 2 | 扩面 PRD（或 PRD 修订 Won't / Could） | §3.3、N8、N11 |
| 3 | SPEC 修订：P2 消费、Testing 轨 B 门、Out of Scope | §2.1、§3.2 触发条件 |
| 4 | `ref-projects.md`：新 `REF_*` 行 + 降低「P2」模糊项 | §3.1 配额内实际入库者 |
| 5 | Issues：新编号票，`Backlog: P2-x`，`ref_id:` | §3.2 |
| 6 | 可选：运维 Runbook（Ollama/vLLM）与模型定制仓 README | N5、N10 |

升格后：将本文状态改为 `superseded → <正式路径>`，避免双真源。

---

## 5. 评委会共识行动项（索引）

| 优先级 | 行动 | 本期 / 扩面 |
|--------|------|-------------|
| P0 | 冻结清单一入库上限 | **已写入** `ref-projects.md` |
| P0 | N1 必须带独立质量门与数值化门槛 | 本文 §2.1；升格时进 SPEC |
| P1 | 清单二首批只批 2 仓 | 本文 §3.1 |
| P1 | Gorilla / ToolLLM / marketplace 移出改写列 | **已写入** `ref-projects.md` |
| P2 | N 标准写入 Constitution 附录 | 本文 §4 步骤 1 |

---

## 6. 修订记录

- 2026-09-13：初稿。基于两份清单分类 + 硅谷技术合成评委会终稿建议落盘，供未来正式文档参考。

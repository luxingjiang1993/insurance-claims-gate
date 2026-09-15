# Spec — insurance-claims-gate · Phase 2a Runnable Product Floor

| 字段 | 内容 |
|------|------|
| feature_slug | `insurance-claims-gate` |
| spec_id | `SPEC-02A-RUNNABLE-PRODUCT-FLOOR` |
| 文件 | `spec-2a-runnable-product-floor.md`（**本文件**） |
| 关系 | **增量 SPEC**；**不废止、不修改**同目录 `spec.md`（修订 2.4，轨 A 门禁真源） |
| prd_id | `PRD-02-INSURANCE-CLAIMS-GATE` v2.0 + 本 SPEC 定义的作业壳切片 |
| Status | `closed`（**索引 / 总览**；W0–W2 各波独立 SPEC 均已 `closed`） |
| 主测试接缝 | **S0** HTTP 黑盒 + `machine_check`（合门禁唯一主缝）；**S1** 同 HTTP 面扩展（会话/RBAC、AI 辅助建议、采纳后再 evaluate）；**S2** 旁路 `track_llm_optional` / OpenEval（不进默认绿） |
| 交付波次 | **W0 → W1 → W2**（同一产品愿景，分层 DoD） |
| **各波独立 SPEC（实现时优先打开）** | W0 [`spec-2a-w0-dev-complete.md`](./spec-2a-w0-dev-complete.md) · W1 [`spec-2a-w1-pilot-complete.md`](./spec-2a-w1-pilot-complete.md) · W2 [`spec-2a-w2-eval-ops.md`](./spec-2a-w2-eval-ops.md) |
| 术语 | 仓库根 `CONTEXT.md`（作业壳、裁决草案、AI 辅助建议、人闸令牌、条款门禁等） |
| 上游输入 | `docs/agents/phase2a-runnable-product-floor.DRAFT.md`；`docs/agents/phase2a-sv-expert-panel-review.DRAFT.md`（采纳建议 A） |
| 参考目录 | `docs/agents/ref-projects.md`；扩面草案 `docs/agents/ref-projects-phase2-supplement.md`（未修宪不得放松 I1–I8） |

**继承声明：** `spec.md` 决策 16–18（文书分态、citation 三联门、推理双轨）与 Testing #7 **继续有效**。  
**阅读规则：** 本文件为 Phase 2a **总览与交叉引用**；**切票与实现以对应 wave 的独立 SPEC 为准**（W0/W1/W2 各一份；W0–W2 均已 `closed`）。

---

## Problem Statement

核赔员与演示受众面对的「条款门禁」目前只有 HTTP API、确定性轨 A 与脚本 Demo：没有**作业壳**，案件在内存里、无登录角色，轨 B 的 LLM 调用是空实现，检索偏假。结果是：门禁契约已可机检，但产品无法被当作「可运行的基础作业台」使用——配不齐环境变量就看不出 AI 辅助路径；也无法在可观测/评测栈里诚实展示「助手而非终裁」。买方与个人开发者都需要在**不削弱应闸必闸、不把 LLM 塞进默认绿门**的前提下，把系统补成可点击、可降级演示、可分波验收的 Runnable Product Floor。

## Solution

在保留 Missions 中继与 `spec.md` 条款门禁权威的前提下，交付 **Phase 2a**：

1. **作业壳**（Vite + React + TS）：薄客户端，只调用理赔 HTTP API；不持有门禁最终权威。  
2. **SQLite + 演示 RBAC**（viewer / adjuster / supervisor）：案子与人闸权限可持久、可演示。  
3. **AI 辅助建议**（OpenAI-compatible）：模型只产出辅助建议；**裁决草案**须经规则门禁校验后落库，并标注 `inference_track`。  
4. **混合检索（仅 AI 路径）**：关键词 + Chroma 向量，默认权重可配置（初值 0.7/0.3），条款号可短路；引用仍过三联门。  
5. **分层完工：** W0 无云也可宣称 Dev Complete；W1 配齐 LangSmith + 混合检索真路径为 Pilot Complete；W2 再做 OpenEval 排行榜与多人协作评测台。  
6. 默认 CI 仍只绿轨 A；支付与 L3 仍不做。

---

## Delivery Waves（DoD）

### W0 — Dev Complete（可运行地板）

- [x] 作业壳套餐 C：登录、案件、材料/一次补件、规则评估与裁决草案、人闸、文书分态、AI 辅助建议区、本案流水  
- [x] SQLite：案件/材料/草案/人闸事件/ledger 摘要/用户角色  
- [x] 三角色 RBAC：仅 supervisor 可批对外通知 / 出款就绪类人闸  
- [x] `.env.example`：LLM 与可选观测键；无 LLM Key 时规则 SC-01/02/03 仍可点完  
- [x] AI 辅助建议 API：无 Key 返回明确降级；有 Key 可出辅助建议；**不能**直接写 `payout_ready` / 签发人闸令牌  
- [x] 关键词检索支撑 AI 路径提名（向量可延后到 W1）  
- [x] 本地 trace 导出（文件或等价）；**不要求**真 LangSmith Key  
- [x] `pytest -q`（轨 A / S0）全绿；无 LangSmith、无 LLM  
- [x] 启动说明写入 `docs/user/`（Developer Preview 诚实标注）

### W1 — Pilot Complete（试点可观测）

在 W0 之上：

- [x] Chroma + 本地默认 embedding（并支持云 embedding API）  
- [x] 混合检索：硬过滤 →（条款号短路｜并行关键词+向量）→ 融合默认 0.7/0.3 → citation 三联门  
- [x] 向量不可用时自动关键词降级，规则评估不受影响  
- [x] **真实 LangSmith** 上报 evaluate / assist / latch 等关键 span  
- [x] OpenEval 旁路跑通，且实验结果可在 LangSmith 查看（含**历史对比**外形）  
- [x] 完工录像套餐 L（关向量、关 LLM 的降级检查 + 满配路径）

### W2 — Eval Ops（评测台产品化）

在 W1 之上：

- [x] OpenEval 数据集的**排行榜**  
- [x] **多人协作**评测（多本地用户或明确协作模型；写入实现票）  
- [x] 与金标运营流程的接口预留（全量 ≥300 仍属 PRD 延后项，不阻塞 W2 外形）  

**宣称规则：** 对外可说「Phase 2a Eval Ops 已交付（Preview）」；须诚实标注 ≥300 金标运营仍延后；排行榜分数 ≠ `machine_check`。不得在仅完成 W0 时宣称 Pilot Complete。

---

## User Stories

### A. 作业壳与角色

1. As a 省分作业中心核赔主管, I want 用浏览器打开作业壳并登录, so that 我不必先学 curl 才能走案件。  
2. As a viewer, I want 只能只读查看案件与裁决草案, so that 演示「权限不够」时不会误批人闸。  
3. As an adjuster, I want 登记材料、触发规则评估、发起一次补件, so that 我能完成初审作业。  
4. As an adjuster, I want 无法批准对外通知或出款就绪类人闸, so that 权限差可被看见。  
5. As a supervisor, I want 批准或驳回人闸并获得人闸令牌, so that 应闸类型受控。  
6. As a 核赔员, I want 在案件列表看到 SC 夹具与持久化案件, so that 重启后演示可续。  
7. As a 核赔员, I want 案详情展示 gate_status、document_status、inference_track、payout_ready, so that 门禁态可读。  
8. As a 消保负责人, I want UI 文案标明「裁决辅助 / 非终裁」, so that 不被理解成秒赔或无人赔付。  
9. As a 内审风控, I want 作业壳在 API 拒绝 EXTERNAL_NOTIFY 时显示失败而非假成功, so that 不能软过人闸。  
10. As a Demo 讲解人, I want 本案操作流水可浏览, so that 能回放谁点了评估/人闸/AI。

### B. 条款门禁路径（继承 spec.md，经作业壳触发）

11. As an adjuster, I want SC-01 一次补件 → 补传 → 通赔建议草案, so that 作业壳验收与 machine_check 一致。  
12. As an adjuster, I want 同 one_shot_hash 拆轮补件被拒绝, so that 一次补件不变量在 UI 可见。  
13. As an adjuster, I want SC-02 拒赔草案带条款项引用与 appeal_path, so that 除外可辩护。  
14. As a supervisor, I want 拒赔 DRAFT_EXPORT 可预览、EXTERNAL_NOTIFY 必须人闸, so that 文书分态不被 UI 抹平。  
15. As an adjuster, I want SC-03 效力栈减赔与 calc_steps 可见, so that 批单优先可演示。  
16. As a 内审风控, I want 无人闸时 payout_ready 恒 false（经 API）, so that 出款就绪不被壳绕过。  
17. As a Validator, I want 继续用 machine_check 黑盒验收上述行为, so that 合门禁不依赖前端。

### C. AI 辅助建议（非终裁）

18. As an adjuster, I want 显式点击「AI 辅助建议」而非默认静默调用, so that 自治等级诚实。  
19. As an adjuster, I want 看到 AI 辅助建议与规则草案的区分标签, so that 不与裁决草案混称。  
20. As an adjuster, I want 将辅助建议「送交规则校验 / 采纳」后才可能更新裁决草案, so that AI 不能同权直接写门禁结论。  
21. As a 系统, I want 采纳路径仍走 evaluate 契约与 citation 门, so that 幻觉条款无法落库。  
22. As a 核赔员, I want 规则与 AI 建议冲突时进入人闸而非自动和稀泥, so that fail-closed 成立。  
23. As a Demo 讲解人, I want 无 LLM Key 时 AI 区明确降级且规则路径仍可用, so that W0 可演示。  
24. As a 开发者, I want OpenAI-compatible base_url/api_key/model 配置, so that 可接云或本地（如 Ollama）。  
25. As an 内审风控, I want AI 或 OCR 文本不能改写 human_latch_required / 签发令牌, so that 注入无法提权。

### D. 混合检索（AI 路径 · W1）

26. As an AI 辅助路径, I want 检索前按效力栈/版本/retrieval_profile 硬过滤, so that 过期条款不进入提名。  
27. As an AI 辅助路径, I want 查询含明确条款号时关键词短路优先, so that 法律定位不被向量噪声淹没。  
28. As an AI 辅助路径, I want 否则并行关键词与向量检索并按可配置权重融合（默认 0.7/0.3）, so that 混合检索可演示。  
29. As an AI 辅助路径, I want 提名必须过 doc_id+clause_item+version 门才标为可采纳引用, so that 检索≠合法 citation。  
30. As a 运维, I want 向量或 Chroma 不可用时回退关键词, so that Pilot 降级诚实。  
31. As a 规则 evaluate, I want 不依赖向量库, so that 轨 A 绿门稳定。

### E. 可观测与评测

32. As a 开发者（W0）, I want 本地 trace 文件记录关键操作, so that 无 LangSmith 也能调试。  
33. As a 试点负责人（W1）, I want LangSmith 中看到 evaluate/assist/latch 的 trace, so that 试点可观测。  
34. As an Eval Owner（W1）, I want OpenEval 跑旁路集并在 LangSmith 做实验历史对比, so that 评测与追踪闭环。  
35. As an Eval Owner（W2）, I want 排行榜展示多实验分数, so that 团队能比较提示/模型版本。  
36. As an Eval Owner（W2）, I want 多人协作评测外形, so that 评测台超越单机脚本。  
37. As a CI Owner, I want 默认 pytest 永不要求真 LLM 或真 LangSmith, so that 合门禁可重复。  
38. As a 金标 Owner, I want OpenEval 不替代 machine_check, so that 合规机检与模型打分分离。

### F. 工程与改写纪律

39. As a coding agent, I want 每个模块有 ref_id 与外链, so that 先改写后发明。  
40. As a coding agent, I want 产品只写入本项目代码/claims-gate, so that 参考仓只读。  
41. As a 架构师, I want W0/W1/W2 状态可在文档中勾选, so that 不虚报完工。  
42. As a 用户文档维护者, I want 每波用户可见能力合入时更新 USER_GUIDE/CHANGELOG, so that 手册诚实。

---

## Reference Projects（改写与外链）

完整 `REF_*` 路径：`docs/agents/ref-projects.md`（相对 `历史项目代码供参考/`）。  
**改写口令：** `Rewrote from: REF-…`（动中继或合门禁时必含 `REF-MISSIONS`）。

| 能力簇 | 优先 ref_id / 来源 | 次选 | 外链（协议/上游 · 供改写对齐） |
|--------|-------------------|------|--------------------------------|
| Missions 中继、machine_check、人闸 | `REF-MISSIONS` | — | — |
| 作业流 / 状态 | `REF-COURSE-04` | `REF-MISSIONS` | — |
| 结构化输出 / 辅助建议 JSON | `REF-COURSE-03` | — | https://github.com/openai/openai-python |
| 规则+模型分治 | `REF-CASE-HYBRID` | `REF-COURSE-12` | — |
| RAG 骨架（轨 B） | `REF-RAG-CY` | `REF-OPENMANUS-RAG`（勿替中继） | — |
| 混合召回 / FAISS·Hybrid | `REF-CASE-RECALL` | `REF-CASE-RERANK` | — |
| 条款 KB | `REF-CASE-KB` | `REF-MISSIONS` knowledge_base | — |
| OpenEvals 评测器 | `REF-CASE-OPENEVALS` | — | https://github.com/langchain-ai/openevals |
| LangSmith 评测/追踪外形 | `REF-CASE-EVAL-ADVISOR`（仓内 `*langsmith*` 脚本） | `REF-CASE-LANGFUSE`（对照） | https://docs.smith.langchain.com/ · https://www.langchain.com/langsmith/evaluation |
| 可观测对照 | `REF-CASE-LANGFUSE` | — | https://github.com/langfuse/langfuse |
| 向量库（依赖级） | — | — | https://github.com/chroma-core/chroma |
| 本地推理（依赖级） | — | — | https://github.com/ollama/ollama |
| OpenAI Agents / LangGraph（**只读外形**） | — | — | https://github.com/openai/openai-agents-python · https://github.com/langchain-ai/langgraph |
| 低代码作业台（**禁止主链**） | — | 见 phase2-supplement N8 | https://github.com/langgenius/dify · https://github.com/langflow-ai/langflow |

**禁止升为门禁主改写源：** Dify / Langflow / Flowise 工作流替 Validator；OpenClaw / nanobot / GenericAgent 通用助理替条款门禁；CrewAI 替换 Missions 三角色；公开「2026 Agent 整表」一次性入库。

**本 SPEC 首批外部依赖级（非新 REF 代码仓）：** Chroma、OpenAI-compatible SDK、LangSmith SDK、openevals。若需新增代码参考仓，遵守 `ref-projects-phase2-supplement.md` **至多 2 仓**配额并先修宪登记。

---

## Implementation Decisions

1. **与 `spec.md` 的关系：** 本文件为增量；冲突时门禁不变量以 `spec.md` 决策 16–18 为准；作业壳/LLM/观测以本文件为准。  
2. **主测试接缝 S0（已确认）：** 理赔 HTTP API 外部行为 + `machine_check` 类型分发；合门禁唯一主缝。**改写：`REF-MISSIONS`。**  
3. **接缝 S1：** 在同一 HTTP 面上增加：登录/会话或等价凭证、角色授权检查、AI 辅助建议端点、可选「采纳辅助建议」后再次进入规则 evaluate。前端不实现第二套规则引擎。  
4. **接缝 S2：** `track_llm_optional` 与 OpenEval/LangSmith 集成测隔离；失败不阻断默认 `pytest -q`。  
5. **不新增接缝：** 不以 Playwright 默认绿门；不以 LangSmith UI、Chroma 内部结构、前端组件树为合规验收缝。  
6. **中继不变：** 保留 Orchestrator / Worker / Validator；不引入第四「核赔 Agent」角色；不整仓替换为 LangGraph/CrewAI。**改写：`REF-MISSIONS`。**  
7. **作业壳：** Vite + React + TS SPA；仅消费公开 HTTP API；禁用低代码主链签发人闸。UI 灵感可扫 Dify/Langflow，**不得**改写其工作流为门禁。  
8. **持久化：** SQLite 存案件域与用户角色；SC 夹具可种子化；允许开发模式内存开关但不作为 W0 默认完工定义。  
9. **RBAC（演示）：** 种子用户 `viewer` / `adjuster` / `supervisor`；supervisor 独占对外通知与出款就绪类人闸批准。无 SSO。  
10. **AI 辅助建议模块：** OpenAI-compatible 客户端；配置来自环境变量；`enable_llm` 显式；无 Key → 结构化降级响应。输出为 **AI 辅助建议**，不是裁决草案。**改写：`REF-COURSE-03` + `REF-CASE-HYBRID`；接线替换空 `_maybe_llm_draft`。**  
11. **采纳契约：** 任何将模型产出写入案件「裁决草案」的路径，必须经过规则 evaluate（或等价硬校验）与 citation 三联门；响应含 `inference_track=llm_optional` 当辅助路径曾参与。  
12. **混合检索（W1）：**  
    - 硬过滤（效力栈/版本/profile）  
    - 条款号/clause_item 命中 → 关键词短路  
    - 否则并行关键词 + Chroma 向量 → 线性融合，默认 `keyword_weight=0.7`、`vector_weight=0.3`（可配置）  
    - 提名 → citation 门  
    **改写：`REF-CASE-RECALL` + `REF-RAG-CY`；依赖 [Chroma](https://github.com/chroma-core/chroma)。**  
13. **Embedding：** 默认本地小模型；支持云 API；与 LLM Key 分离配置。  
14. **LangSmith：** W0 本地 exporter；W1 真 Key 上报。无 Key 不得宣称 W1 Complete。  
15. **OpenEval：** 扩展既有旁路；W1 打通 LangSmith 实验与历史对比；W2 排行榜与多人协作。**改写：`REF-CASE-OPENEVALS` + `REF-CASE-EVAL-ADVISOR`。**  
16. **Ledger：** 继续记录 route_id、retrieval_profile、decision_type、validator 结果；增加 actor_role、assist_invocation_id（若有）、trace_id（若有）。  
17. **启动面：** 提供脚本或文档化双命令（API + FE）；Windows 可运行。  
18. **波次门禁：** 实现票与文档必须标注 `wave: W0|W1|W2`；禁止将 W2 验收塞进 W0 CI。  
19. **用户手册：** 每波用户可见合入按 `docs/user/MAINTENANCE.md` 更新。  
20. **自治诚实：** Demo/UI/README 禁止「全自动核赔 / 秒赔」包装责任争议案。

### 接缝示意

```text
[作业壳 SPA] ──HTTP(+session)──► Claims API (权威)
                                    ├─ evaluate / latch / documents  → machine_check (S0)
                                    ├─ assist (llm_optional)         → S2 可选测
                                    └─ adopt assist → evaluate       → S0
Validator / pytest -q ───────────────────────────────► S0 only
pytest -m track_llm_optional|eval_* ─────────────────► S2 (non-blocking)
LangSmith / OpenEval (W1+) ◄── spans/experiments ──┘ (never default green gate)
```

---

## Testing Decisions

1. **好测试：** 只断言外部行为（HTTP 状态与字段、RBAC 拒绝、document_status、人闸、citation 门、assist 降级、采纳后仍 fail-closed）。不断言 React 组件内部 state、Chroma 底层段、LangSmith 专有 UI。  
2. **S0 必绿：** 继承 `spec.md` SC-01/02/03 与负例；并增加：adjuster 批人闸失败、supervisor 成功；无令牌 EXTERNAL_NOTIFY 失败；无 LLM 时核心 SC 仍过。Prior art：`REF-MISSIONS` TestClient + `run_machine_check`。  
3. **S1：** API 级登录与 assist/adopt 契约测；可与 S0 同套 TestClient。  
4. **S2：** 真 LLM / 真 LangSmith 测标记隔离；CI 默认排除；可在有密钥的 job 中可选跑。  
5. **W1 录像套餐 L：** 人工或脚本清单：满配路径 + 关向量 + 关 LLM；不写入默认 pytest 强制。  
6. **W2：** 排行榜/多人以可观察 API 或页面契约测为主，仍不进轨 A 绿门。  
7. **违规：** 默认 CI 因缺 LangSmith/LLM Key 失败 → SPEC 违规。

---

## Out of Scope

- 修改或废止同目录 `spec.md` 正文（本文件不得被用作删除旧 SPEC 的授权）  
- L3 自动出款 / 银企直连 / 支付适配器  
- 真连客户核心 L2、真实 OCR 供应商（仍可模拟）  
- ≥300 人工金标全量运营（入口可有，运营延后）  
- 用 Dify/Langflow/n8n **替代** machine_check 或签发人闸令牌  
- 用通用个人 Agent（OpenClaw/nanobot 等）替换条款门禁  
- 默认 CI 依赖非确定性 LLM  
- 车险查勘定损、重疾诊断给付、健康治疗方案生成  
- 企业 SSO / 多租户生产 IdP  
- 消费 phase2-supplement N* 放松 I1–I8（须另修宪）  
- 将「秒赔率」作为成功承诺  

---

## Further Notes

- **切票：** 按波次目录落盘——W0 → `phase2a-w0/`（14–22）；W1 → `phase2a-w1/`（23–28）；W2 → `phase2a-w2/`（29–33 已切）。Phase 1 票在 `phase1/`。票首含 `wave:`、`spec_id:`、`ref_id:`、`Blocked by:`、`Status:`。建议序：W0 持久化/RBAC → env+assist → 作业壳 SC → 流水/文档 → W1 Chroma 混合 → LangSmith → OpenEval 历史对比 → W2 排行榜/协作。
- **价值映射：** 继续 `VP-HUMAN-LATCH`、`VP-FAIL-CLOSED`、`VP-INDEP-JUDGE`、`VP-HONEST-AUTONOMY`、`VP-RAG-CITE`、`VP-THIN-SLICE`、`VP-RELAY`；作业壳不新增「低代码替门禁」类 VP。  
- **评委会：** 2026-09-14 十人合成评审采纳建议 A（三波 DoD）；详见 `docs/agents/phase2a-sv-expert-panel-review.DRAFT.md`。  
- **草稿收敛：** `phase2a-runnable-product-floor.DRAFT.md` 中「一次做完无砍项」已被本 SPEC 波次模型取代；升格后将该 DRAFT 标 `superseded → 本文件`。  
- **代码根：** `本项目代码/claims-gate/`。  

---

## Wave Backlog（本 SPEC 内）

| ID | 波次 | 摘要 | 状态 |
|----|------|------|------|
| W0-1 | W0 | SQLite + 种子 RBAC | `done` |
| W0-2 | W0 | OpenAI-compatible assist + 降级 | `done` |
| W0-3 | W0 | 作业壳套餐 C | `done` |
| W0-4 | W0 | 本地 trace + 用户文档 | `done` |
| W1-1 | W1 | Chroma 混合检索 + embedding | `done` |
| W1-2 | W1 | LangSmith 真上报 | `done` |
| W1-3 | W1 | OpenEval ↔ LangSmith 历史对比 | `done` |
| W2-1 | W2 | 排行榜 | `done` |
| W2-2 | W2 | 多人协作评测 | `done` |

---

## Comments

- 2026-09-14：to-spec 发布本增量 SPEC；用户确认接缝 S0/S1/S2 与评委会建议 A（分层 DoD）；Status=`ready-for-agent`。**未修改** `spec.md`。
- 2026-09-14：按用户要求拆出各波独立 SPEC：`spec-2a-w0-dev-complete.md`、`spec-2a-w1-pilot-complete.md`、`spec-2a-w2-eval-ops.md`；本文件降为总览索引。
- 2026-09-14：to-tickets 批准 defaults — W0 票 14–22 落盘 `phase2a-w0/`；Phase 1 的 01–13 迁入 `phase1/`。
- 2026-09-14：to-tickets 批准 defaults — W1 票 23–28 落盘 `phase2a-w1/`。
- 2026-09-14：to-tickets 批准 defaults — W2 票 29–33 落盘 `phase2a-w2/`。
- 2026-09-15：W2 DoD 关闭（票 33）；总览 W2 勾选与 Wave Backlog 标 `done`。`Rewrote from: REF-MISSIONS`。

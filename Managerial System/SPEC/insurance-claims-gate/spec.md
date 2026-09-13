# Spec — insurance-claims-gate（条款门禁）

| 字段 | 内容 |
|------|------|
| feature_slug | `insurance-claims-gate` |
| prd_id | `PRD-02-INSURANCE-CLAIMS-GATE` v2.0 |
| Status | `ready-for-agent` |
| 主测试接缝 | HTTP 黑盒 + `machine_check` 类型注册表（人闸令牌与 KB 引用门为支撑） |
| 术语 | 见仓库根 `CONTEXT.md` |
| 修订 | `2.3` — REF 本期剩余/入库上限与扩面补充文档指针（评委会终稿） |
| 参考目录 | `docs/agents/ref-projects.md` |

---

## Problem Statement

核赔作业人员与理赔管理者面对个人意外险（含意外医疗）案件时，条款、规则引擎与对外话术经常不同步：材料补件容易拆成多轮，触碰一次性告知义务；拒赔/减赔缺少可核验的条款项引用，难以辩护；复杂「疾病 vs 意外」案无法用可回归的门禁证明「应闸必闸」。持牌责任不能交给无人系统，但现有流程又缺少「裁决草案 → 独立校验 → 人闸令牌 → 出款就绪」的可验收中继。买方需要在一个薄切片上看到一次补件说清、拒赔可追溯、且零自动出款事故的条款门禁，而不是「秒赔」话术。

## Solution

交付个人意外险薄切片上的**条款门禁**：以 Missions 中继（Orchestrator 出契约、Worker 实现领域服务、Validator 只评判）驱动；产品面提供理赔案件 HTTP API。系统产出**裁决草案**（补件 / 通赔建议 / 减赔 / 拒赔草案等），材料不齐时强制**一次补件**（`one_shot_hash`）；责任与除外必须带版本化条款引用并服从**效力栈**（引用须落库到条款项）；Validator 经主接缝（`machine_check` HTTP 黑盒）独立验收，失败则失败关闭、不得进入**出款就绪**。**草稿导出**与**对外通知**分态：拒赔类对外通知与超权限给付必须取得**人闸令牌**；默认 CI/Demo 走确定性轨，可选 LLM/RAG 轨不得混入默认绿门。支付仍走核心既有人工流程（本期不做 L3）。Must 演示场景固定为 SC-01、SC-02、SC-03。

## User Stories

1. As a 省分作业中心核赔主管, I want 在材料台看到案件进入材料受理状态, so that 我知道门禁已拉到立案头信息。
2. As a 初审岗, I want 系统对影像做材料齐全断言, so that 不齐时自动进入待补件而非静默通赔。
3. As a 初审岗, I want 一次补件清单一次性列出全部缺项并带 `one_shot_hash`, so that 我不会对同缺项拆多轮通知客户。
4. As a 客户（经办视角）, I want 补件通知含缺项中文名、是否必须与示例说明, so that 我能一次交对材料。
5. As a 消保负责人, I want 补件通知固定引用一次性补正法义文案, so that 抽检能对齐《保险法》第22条义务。
6. As a 核赔员, I want 客户补传后系统重评且旧缺项已满足时才允许新清单, so that 不会在同一 hash 下偷加缺项。
7. As a 核赔员, I want SC-01 路径在补齐发票后给出通赔建议裁决草案, so that Demo 与回归能固定验收一次补件通赔。
8. As a 核赔员, I want 疾病导致摔伤案产出拒赔草案且必须条款项引用, so that 除外理由可辩护（SC-02）。
9. As a 核赔主管, I want 拒赔草案对外前必须人闸, so that 无人系统不能单独完成对外拒赔。
10. As a 消保负责人, I want 拒赔文书草稿含 appeal_path, so that 申诉/人工复核入口永不缺失。
11. As a 内审风控, I want 无人闸令牌时 `payout_ready` 恒为 false, so that 应闸必闸可机检。
12. As a 核赔员, I want 批单缩小责任时减赔草案按效力栈引用批单优于主险, so that SC-03 可验收权威消解。
13. As a 个人险产品经理, I want 每条 citation 含 doc_id、条款项、版本/生效日与 authority_rank, so that 条款 KB 变更可追溯。
14. As a 核赔员, I want 免赔额与赔付比例步骤可复核, so that 理算与条款冲突时失败关闭而非静默改数。
15. As a 理赔管理部总, I want 裁决类型结构化为补件/通赔建议/减赔/拒赔草案/调查中/预赔, so that 队列与权限表可映射。
16. As a 调查协查岗, I want 风险超阈进入调查中时自动冻决且不得出款就绪, so that 调查期间不会误通赔。
17. As a 调查协查岗, I want 解除冻决必须人闸, so that 调查出口受控。
18. As a 核赔主管, I want 通融决定必须人闸且禁止伪「主险条款通赔」citation, so that 通融与条款通赔语义分离。
19. As a 核赔主管, I want 预赔必须人闸, so that 预付风险可控。
20. As a 核赔主管, I want 通赔建议按试点金额档决定是否人闸, so that 小额可抽检直通草案、大额必闸。
21. As a 核赔主管, I want 诉讼/信访/媒体等场景权限上浮至少一档, so that 敏感案不会按普通档漏闸。
22. As an IT 理赔产品经理, I want L1 最低只读字段可用（案件号、保单号、条款版本、出险日等）, so that 门禁不瞎编保单事实。
23. As an IT 理赔产品经理, I want 门禁状态机覆盖材料受理到结案的规范态, so that 可与现网枚举对照（试点假设可先用左列）。
24. As an IT 理赔产品经理, I want L2 回写出款就绪仅在人闸后发生且不触发银企, so that 核心支付流程不被绕过。
25. As a 内审风控, I want 主数据不一致时禁止进入出款就绪, so that 保单/批单/案件对不上不能放行。
26. As a Validator（系统角色）, I want 独立检索条款 KB 并执行 machine_check, so that 我不采信 Worker 自述作为唯一证据。
27. As a Validator, I want 引用不在库内时断言失败, so that 幻觉条款无法过门。
28. As an Orchestrator, I want 先产出带 policy_clause_id 的 validation contract 再开实现特征, so that 契约先行。
29. As a Worker, I want 在写锁下只实现契约声称的行为, so that 不并行破坏共享工件。
30. As a 理赔管理部总, I want 校验失败开 fix 特征而非标完成, so that 失败关闭可运转。
31. As a Demo 讲解人, I want SC-01/02/03 可一键或脚本跑通黑盒断言, so that 面试/试点演示可重复。
32. As a 消保负责人, I want 减赔通知复用 citations 与计算步骤字段, so that 减赔同样可追溯。
33. As a 法务律师, I want 系统叙事禁止用「秒赔」包装责任争议案, so that 对外预期不被抬高。
34. As a 内审风控, I want OCR 文本与客户备注不能改写人闸规则, so that 提示注入无法提权。
35. As a 内审风控, I want 支付类工具默认无权限, so that Worker 不能越权出款。
36. As a 金标 Owner, I want 通融伪 citation 与拆轮补件负例进入回归集设计, so that 逃逸可被门禁抓住（本期至少机检负例路径）。
37. As a 周回归 Owner, I want 关键 machine_check 未达门槛时不能宣传提直通, so that 质量门禁诚实。
38. As a 分管运营副总, I want KPI 仅以相对基线与可追溯率呈报且禁止秒赔率对赌, so that Week12 决策不被虚荣指标绑架。
39. As a 核赔员, I want 导出补件/拒赔文书草稿字段齐全, so that 对外通知不缺法定要素。
40. As a Router, I want 多路由冲突时按 Human > Invest > Rules > RAG > OCR 仲裁, so that 争议案不会静默采信一侧。
41. As a 核赔员, I want 规则与条款 RAG 冲突时失败关闭进人闸, so that 不自动和稀泥。
42. As a 检索配置, I want endorsement_priority 画像先查批单再主险, so that 效力栈在检索层可落实。
43. As a 检索配置, I want handbook_ops 不得单独作为对外拒赔唯一依据, so that 内部手册不越权。
44. As an 审计读者, I want ledger 记录 route_id、retrieval_profile、decision_type、validator_score, so that 事后可回放。
45. As a 开发者, I want 从既有 Missions 中继做同中继换垂直而非重写角色剧场, so that 降低交付风险。
46. As a 开发者, I want 产品代码只落在本项目代码根, so that 历史参考仓保持只读。
47. As a 核赔员, I want 峰值降级只能变为补件+排队人审, so that 禁止静默自动通赔。
48. As a 客户申诉路径使用者, I want 人闸驳回后可回编辑态, so that 草案可修正再提。
49. As an IT, I want 结案回写不含自动支付指令, so that CLOSED 与出款解耦。
50. As a 理赔管理部总, I want 范围锁定个人意外险（含意外医疗）理赔, so that 车险/重疾不进入本期切片。

## Reference Projects（改写用 REF_*）

完整目录、**Issues 01–09 已占用**、**本期仍可供改写（入库上限）**、协议阅读降级列见 `docs/agents/ref-projects.md`。  
扩面 / 第二阶段草案（N1–N11、清单二配额）：`docs/agents/ref-projects-phase2-supplement.md`（`draft-supplement`；未修宪不得执行放松）。

下列为 **本 SPEC 能力 → 优先改写源**；agent 实现对应模块时必须先打开所列 `ref_id`，禁止无依据空写。

| 能力 / 决策簇 | 优先 ref_id | 次选 ref_id | 说明 |
|---------------|-------------|-------------|------|
| Missions 中继、契约、`machine_check`、人闸、schemas、换垂直 | `REF-MISSIONS` | — | **唯一主基线**；同中继换域 |
| HTTP 黑盒验收 / TestClient 模式 | `REF-MISSIONS` | — | 对齐既有 Validator→checks |
| 条款 KB 版本化 / 切块 / 健康检查 | `REF-CASE-KB` | `REF-MISSIONS`（`knowledge_base/`） | 效力栈内容换保险条款 |
| 检索 / RAG（轨 B 或检索画像） | `REF-RAG-CY` | `REF-CASE-RECALL`, `REF-CASE-RERANK`, `REF-OPENMANUS-RAG` | 不得替代轨 A 确定性绿门；本期剩余优先吃 RAG-CY/RECALL |
| 结构化输出 / 裁决 JSON 外形 | `REF-COURSE-03` | `REF-MISSIONS`（schemas） | 契约与 API 响应 |
| 状态机 / 多步作业流 | `REF-COURSE-04` | `REF-MISSIONS`（runner 回路） | 门禁态 + 文书态 |
| Router / 冲突仲裁 / 复杂回路 | `REF-COURSE-12` | `REF-CASE-HYBRID` | Router 为硬层策略表（P1-1） |
| 工具调用与最小权限外形 | `REF-CASE-FC` | `REF-CASE-MCP` | 无支付工具；ACL；MCP 与 FastMCP 外形二选一 |
| Eval / 负例 / 回归入口 | `REF-CASE-OPENEVALS` | `REF-CASE-EVAL-ADVISOR` | 配合 machine_check；**本期剩余可新切票**；金标运营见 P2 |
| 混合式规则+模型（轨 A/B 分治） | `REF-CASE-HYBRID` | `REF-COURSE-12` | 默认绿门仍为轨 A |
| 可观测 / 追踪（可选） | `REF-CASE-LANGFUSE` | — | 次于 ledger；P2 / 扩面补充文档 |
| 深思熟虑推理（仅轨 B） | `REF-CASE-DELIBERATIVE` | — | 禁止并入默认 CI |
| 条款问答（非门禁主链） | `REF-CASE-REACTIVE-QA` | — | 勿做成主 Orchestrator |
| OpenManus 通用框架 | `REF-OPENMANUS-CY` | `REF-OPENMANUS-GUI` | **勿替代** `REF-MISSIONS` |
| 沙箱 / GUI 自动化 | `REF-CASE-DAYTONA` | `REF-CASE-GUI-PLUS`, `REF-COURSE-05`, `REF-COURSE-11` | 本期非目标；扩面见补充文档 N6 |

**改写口令（写入 ticket / handoff）：** `Rewrote from: REF-…`（可多选，主基线必含 `REF-MISSIONS` 若动中继或合门禁）。  
**本期新票：** 遵守 `ref-projects.md` 入库上限；勿与 Issues 01–09 已占用主路径平行重复。

---

## Implementation Decisions

1. **垂直换域方式：** 保留 Missions 中继三角色与账本形态；替换被测产品（理赔案件域）、条款/批单 KB、Orchestrator 断言目录，以及 `machine_check.type` 注册表。不新增第四个「核赔 Agent」角色。**改写：`REF-MISSIONS`。**
2. **主测试接缝（已确认）：** 唯一主缝为「理赔 HTTP API 上的外部行为」经 Validator 调用 `machine_check` 分发器验收。人闸令牌门与 KB `policy_clause_id` 存在性门为同一验收链上的支撑门，不另建第二套架构。**改写：`REF-MISSIONS`。**
3. **禁止按断言 ID 分支：** `machine_check` 只按 `type` + `params` 执行；不得用 `A-00x` 硬编码开关充当验收。**改写：`REF-MISSIONS`（checks 分发模式）。**
4. **产品 API 能力（逻辑模块）：** 案件读取（L1 字段）、材料/影像元数据登记、触发门禁裁决、查询裁决草案与状态、提交补件后重评、人闸批准/驳回、文书草稿导出、L2 状态回写模拟（内存或夹具即可）。不实现银企支付适配器。**改写：`REF-MISSIONS`（替换 transfer_api 域）；编排参考 `REF-COURSE-04`。**
5. **裁决响应最低外形：** 含 `decision_type`、`gate_status`、`document_status`（见决策 16）、`payout_ready`、`supplement_checklist` / `one_shot_hash`（补件时）、`citations[]`（责任/除外/减赔/拒赔时；每条须含可落库校验字段，见决策 17）、`calc_steps[]`（理算时）、`human_latch_required`、`human_latch_token`（批准后）、`appeal_path`（拒赔草案）、`authority_rank` / `overridden_by`（效力冲突时）、`inference_track`（`deterministic` | `llm_optional`，见决策 18）。**改写：`REF-MISSIONS` schemas + `REF-COURSE-03`。**
6. **SC 夹具：** 内置三套**确定性轨**案件夹具对应 SC-01（缺发票→补传）、SC-02（疾病摔伤除外）、SC-03（批单缩责）。夹具驱动 HTTP 路径，供默认 `machine_check` 与 Demo 共用；不得依赖非确定性 LLM 抽样才能绿。**改写：`REF-MISSIONS`（artifacts/fixtures 思路）。**
7. **建议的 machine_check 类型（名称可在实现时微调，语义冻结）：**
   - 一次补件完整性与同 hash 防拆轮
   - 补齐后通赔建议且未人闸前的 `payout_ready=false`（若金额档要求闸则另检）
   - 拒赔草案：条款项级落库引用通过；`document_status=DRAFT_EXPORT` 可无人闸预览；`EXTERNAL_NOTIFY` 无人闸必失败；`payout_ready` 无人闸恒 false
   - 效力栈下批单覆盖主险的减赔引用与金额步骤
   - 伪 citation / 库外或错条款项 → 失败
   **改写：`REF-MISSIONS`；评估模式参考 `REF-CASE-OPENEVALS`。**
8. **人闸：** 拒赔草案的**对外通知**、通融、预赔、调查解除冻决默认要求人闸令牌；通赔/减赔按 PRD 试点金额档。无令牌则 `payout_ready` 必须为 false；拒赔类不得进入 `EXTERNAL_NOTIFY`。**改写：`REF-MISSIONS`（approve / latch）。**
9. **状态机：** 实现 PRD 门禁状态枚举；试点阶段现网码对照可先用规范态左列（假设 A2），回写接口保留「现网枚举」字段位但不阻塞 Demo。文书态见决策 16，与门禁态并存、勿混用。**改写：`REF-COURSE-04` + `REF-MISSIONS` runner。**
10. **Router：** 实现显式路由表与冲突优先级；规则 vs RAG 冲突 → 失败关闭进人闸。Ledger 必记路由与 retrieval_profile。默认绿门路径上 Router 结果须可由确定性轨复现（见决策 18）。**改写：`REF-COURSE-12` + `REF-CASE-HYBRID`；落地仍挂在 `REF-MISSIONS` 硬层。**
11. **KB：** 版本化主险/附加险/批单样例条款；retrieval_profile 至少支持 `clause_v_current`、`endorsement_priority`、`handbook_ops`（后者不可单独支撑对外拒赔）。引用校验粒度见决策 17。**改写：`REF-CASE-KB` + `REF-MISSIONS` knowledge_base；检索 `REF-RAG-CY` / `REF-CASE-RECALL`。**
12. **文书：** 补件与拒赔按 PRD 字段表导出（JSON 或结构化对象即可；排版次要）。导出接口必须声明 `document_status`；拒赔类从草稿升对外通知走决策 16。**改写：`REF-COURSE-03` + 域 API（自 `REF-MISSIONS` 产品面换皮）。**
13. **威胁模型落地（本期最小）：** 工具 ACL 无支付；用户/OCR 文本不可改人闸规则；引用落库到条款项；峰值只允许降级为人审队列。**改写：`REF-MISSIONS` tool ACL；工具外形 `REF-CASE-FC`。**
14. **自治标注：** Demo 与文档诚实标注为裁决辅助（低–中自治），禁止全自动无人赔付表述。**改写：`REF-MISSIONS` DESIGN_PHILOSOPHY 诚实自治。**
15. **金标规模：** 本期以 SC + 负例机检为主；≥300 人工金标属运营里程碑，不阻塞本 SPEC 的机器验收，但契约须预留回归入口。**改写入口：`REF-CASE-OPENEVALS` + `REF-CASE-EVAL-ADVISOR`（运营见 P2-1）。**
16. **【P0】文书效力分态（草稿 vs 对外通知）：** 引入 `document_status`：
    - `DRAFT_EXPORT`：内部/预览草稿；可无人闸生成以便核赔员审阅；**不代表**已对外送达；不得单独作为合规「已说明理由」完成态。
    - `EXTERNAL_NOTIFY`：对外通知定稿/已发送语义；拒赔类（及 PRD 规定必闸类型）**必须**持有有效 `human_latch_token`；缺令牌 → API 拒绝且 `machine_check` 失败。
    - 减赔/补件是否升 `EXTERNAL_NOTIFY` 需人闸：补件默认可自动；减赔按金额档与争议上浮（对齐 PRD §7）。
    **改写：`REF-MISSIONS`（latch 门）+ 域状态字段。**
17. **【P0】Citation 落库到条款项（非仅 doc 存在）：** 每条对外可用 citation 校验必须同时命中 KB 中的 `doc_id` + `clause_item` + `doc_version`（或等价 `effective_date` 键）。仅文档存在、条款项缺失、版本不匹配、或摘录无法对应库内条目 → 失败关闭。可选增强（不阻塞 MVP）：摘录哈希 / 字符偏移；**不得**用「全文最大相似」代替本校验。**改写：`REF-MISSIONS` citation/KB gate；KB 工程 `REF-CASE-KB`。**
18. **【P0】推理双轨（防绿门幻觉）：**
    - **轨 A `deterministic`（默认 CI / Demo / 合门禁）：** SC-01/02/03 与约定负例仅允许确定性规则 + 夹具 KB（及显式路由表）；禁止把非确定性 LLM 抽样作为绿门必要条件。**改写：`REF-MISSIONS` + `REF-CASE-HYBRID`（规则侧）。**
    - **轨 B `llm_optional`（可选）：** 允许 RAG/LLM 辅助起草；必须单独标注 `inference_track=llm_optional`；方差、重试与人闸策略独立配置；**不得**并入默认 `machine_check` 全绿条件；规则 vs RAG 冲突仍 fail-closed 进人闸。**改写：`REF-RAG-CY` / `REF-CASE-DELIBERATIVE`（隔离目录）。**

### 接缝示意（来自基线形态，非绑定路径）

```text
ValidationContract.assertions[]
  └─ machine_check: { type, params }
        → Validator HTTP client → 理赔案件 API
        → pass/fail 更新断言；全过仍须人闸后才出款就绪（应闸类型）
```

## Testing Decisions

1. **好测试的标准：** 只断言外部可观察行为（HTTP 响应字段、状态迁移、`document_status`、有无人闸令牌、条款项级 KB 拒收伪引用、`inference_track`）。不断言 Worker 私有函数、内部缓存结构或断言 ID 字符串。
2. **主验收模块：** `machine_check` 注册表 + 理赔 HTTP API；由 Validator（或等价黑盒运行器）对 SC-01/02/03 与约定负例执行；**默认仅跑轨 A（deterministic）**。
3. **支撑验收：** 无人闸令牌时出款就绪为 false；拒赔类无人闸升 `EXTERNAL_NOTIFY` 失败；缺失/库外/错 `clause_item` 或版本不匹配失败关闭。
4. **Prior art：** 参考仓 FinTech 垂直用同一模式（HTTP TestClient + `run_machine_check` 按 type 分发；单元测服务仅服务 Worker 开发，不作合规终裁）— **`REF-MISSIONS`**。本切片继承该分层：服务单测可有，但 **合门禁以 machine_check 为准**。评估器模式可参考 **`REF-CASE-OPENEVALS`** / **`REF-CASE-EVAL-ADVISOR`**（不替代 machine_check）。
5. **必过场景（轨 A）：** SC-01、SC-02、SC-03；同 hash 拆轮补件应失败；通融伪主险通赔 citation 应失败；错条款项/错版本 citation 应失败；拒赔 `DRAFT_EXPORT` 可无令牌、同案 `EXTERNAL_NOTIFY` 无令牌应失败。
6. **不做本期：** 真连客户核心 L2、真实 OCR 供应商、人工 300+ 金标全量跑通、轨 B 并入默认绿门，作为本 SPEC 完成定义。
7. **【P0 验收绑定】：** 任一默认 CI 任务若调用 LLM 才能通过 SC，视为 SPEC 违规；轨 B 测试须目录/标记隔离（如 `track_llm_optional`），失败不阻断轨 A 合门禁。

## Out of Scope

- L3 自动出款 / 银企直连 / 支付适配器（PRD W-04，unmet）
- 车险查勘定损主链、重疾诊断给付（W-05）
- 健康/医疗诊断或治疗方案生成（W-01）
- 无人最终拒赔且不可申诉（W-02）
- 纯客服话术机器人作为交付（W-03）
- 将历史参考仓改为可写交付、或在参考仓内演进产品
- 完整生产凭证代理、多租户 Mission Control、真实监管报送
- 把「秒赔率」或对标他司整体时效作为成功承诺
- 本 SPEC 阶段切 Issues 之外的 GitHub 远程工作流（日后迁移）

## Further Notes

- 需求真源：`Managerial System/PRD/PRD_02_INSURANCE_CLAIMS_GATE.md`；本 SPEC 为其工程化。冲突时以 PRD 行为意图为准，本 SPEC 细化接缝与模块边界。
- 试点假设 A1–A5（权限档、现网枚举、Owner 具名等）允许按 PRD §14 默认推进；上线前关闭，不阻塞本 SPEC 实现。
- 下一动作：按 `docs/agents/issue-tracker.md` 在 `Managerial System/Issues/insurance-claims-gate/` 切带 `Blocked by` 的任务图；实现只写入 `本项目代码/claims-gate/`。
- 价值映射继续只引用 `VP-*`（契约先行、独立裁判、失败关闭、人闸、薄切片、同中继换域等）。
- 硅谷合成评委会（2026-09-13）均分 8.1；P0 已写入 Implementation/Testing；P1/P2 见下方 Backlog，切票与扩面时消费。
- 参考项目 ID 目录：`docs/agents/ref-projects.md`（含本期剩余与入库上限）；扩面草案：`docs/agents/ref-projects-phase2-supplement.md`。本 SPEC「Reference Projects」表为能力→REF 映射。切票时在正文写 `ref_id:` / `Rewrote from:`。

---

## Expert Review Backlog（后续可用）

来源：硅谷级合成评委会对 `spec.md` 的评审。**P0 已落地为本 SPEC 正文决策 16–18 与 Testing #7**；以下仅保留未消化项，供切票 / 扩面 / 开 fix 时引用。状态：`open` = 尚未写入强制实现；消费后改为 `done` 并指向 ticket。

### P0（已应用 — 保留索引）

| ID | 摘要 | 落点 | 状态 |
|----|------|------|------|
| P0-1 | CI/Demo 确定性轨 vs 可选 LLM 轨拆分 | 决策 18；Testing #2/#7 | `applied` |
| P0-2 | Citation 落库到条款项（doc+clause_item+version） | 决策 17；Testing #3/#5 | `applied` |
| P0-3 | 拒赔草稿 vs 对外通知分态 + 人闸绑定 | 决策 16；决策 7/8/12 | `applied` |

### P1（切票或 MVP 削面时优先消费）

| ID | 摘要 | 建议消费方式 | 状态 |
|----|------|--------------|------|
| P1-1 | Router = 确定性策略表（硬层），禁止写成独立 LLM「核赔角色」 | Issues：脚手架/Router 票正文写死；User Story 40 实现时降级为表驱动 | `open` |
| P1-2 | Validation contract 入账前 JSON Schema 硬停；非法契约不得开工 | Issues：契约/Orchestrator 票 | `open` |
| P1-3 | 间接提示注入负例：OCR/备注含提权文案不得翻转 `human_latch_required` / `payout_ready` | Issues：威胁模型 machine_check 负例票 | `applied` |
| P1-4 | 冻结最小 `error_code` 表（如 `MASTER_DATA_MISMATCH`、`VALIDATION_FAILED`、`LATCH_REQUIRED`、`CITATION_NOT_IN_KB`、`DOCUMENT_STATUS_FORBIDDEN`） | Issues：API 合约票 | `open` |
| P1-5 | User Stories 分 Must-for-MVP（SC+人闸+引用+双轨+文书态）与 Should；首批 tickets 只吃 Must | 切票时过滤；可选在本 SPEC 加 Must 标签附录 | `done` → `Issues/insurance-claims-gate/`（01–05 Must 绿门；06–09 Should/支撑） |
| P1-6 | MVP 削面：SC 三夹具 + 核心 machine_check + 人闸 + 最小 KB；Router 仲裁可先硬编码 SC 路径再表格化 | 切票排序：先 SC 绿门，后 Router 全表 | `done` → Issues 03–05 先于 07 |
| P1-7 | Judge–human 抽检占位：预留一致率字段/手工表（每周 N 案）；不阻塞机器绿门 | Issues：金标/回归入口票；对齐 PRD §9 | `open` |
| P1-8 | Citation 可选增强：摘录哈希或字符偏移（决策 17 已标可选） | 扩面或逃逸修复时 | `open` |

### P2（扩面 / 运营里程碑）

| ID | 摘要 | 建议消费方式 | 状态 |
|----|------|--------------|------|
| P2-1 | ≥300 人工金标全量与周回归运营（PRD M3/M5） | 试点运营里程碑；非本 SPEC 完成定义 | `open` |
| P2-2 | 真连客户核心 L2 / 现网枚举关闭 A2 | 上线前；依赖客户填空 | `open` |
| P2-3 | 真实 OCR 供应商接入（替换夹具影像元数据） | 另票；保持 machine_check 黑盒不变 | `open` |
| P2-4 | 轨 B（`llm_optional`）独立质量门与方差预算 | 确定性轨稳定后；不得并入默认 CI 绿 | `open` |
| P2-5 | 完整生产凭证代理、多租户 Mission Control、监管报送 | Out of Scope 维持；另立项 | `open` |
| P2-6 | Tracker 迁 GitHub Issues（local → remote） | 建 git remote 后跑 setup-matt-pocock-skills | `open` |
| P2-7 | REF 扩面：N1–N11 修宪附录 + 首批至多 2 仓入库（LightRAG/RAGFlow 解析旁路与可观测二选一组合） | 消费 `docs/agents/ref-projects-phase2-supplement.md` → Constitution 附录 / 新 PRD / 本 SPEC 修订后再切票 | `open` |

**消费规则：** 开 Issues 时在票首引用 `Backlog: P1-x` / `P2-x`；完成后把上表状态改为 `done` 并写 `→ Issues/…/NN-….md`。

---

## Comments

- 2026-09-13：to-spec 发布；主接缝经用户确认（HTTP + machine_check）；Status=`ready-for-agent`。
- 2026-09-13：SPEC 修订 2.1 — 写入 P0-1/2/3（决策 16–18 + Testing #7）；登记 P1/P2 Backlog 供后续切票与扩面。
- 2026-09-13：SPEC 修订 2.2 — 增加 Reference Projects 与决策级 `REF_*`；目录见 `docs/agents/ref-projects.md`。
- 2026-09-13：to-tickets 落盘 `Issues/insurance-claims-gate/01`–`09`；消费 P1-5/P1-6。
- 2026-09-13：SPEC 修订 2.3 — 挂载 REF 本期剩余/入库上限与扩面补充文档；Backlog 增 P2-7；对齐硅谷技术合成评委会终稿（清单一通过、清单二有条件通过）。

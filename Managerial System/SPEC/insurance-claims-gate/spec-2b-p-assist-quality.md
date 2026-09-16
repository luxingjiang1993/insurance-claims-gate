# Spec — Phase 2b · P Claims Assist Quality

| 字段 | 内容 |
|------|------|
| feature_slug | `insurance-claims-gate` |
| spec_id | `SPEC-02B-P-ASSIST-QUALITY` |
| wave | `2b-P`（实现分 `phase2b-p-α` / `phase2b-p-β`） |
| Status | `ready-for-agent`（α DoD **closed** 2026-09-16；β 仍 open） |
| 规划真源 | [`docs/agents/phase2b-depth-planning-backlog.DRAFT.md`](../../../docs/agents/phase2b-depth-planning-backlog.DRAFT.md)（`draft-decided`） |
| 前置 | Phase 2a W0–W2 已 closed；[`spec.md`](./spec.md) 决策 16–18 继续有效 |
| 后继 | [`spec-2b-q-relay-a2a3.md`](./spec-2b-q-relay-a2a3.md)（`SPEC-02B-Q-RELAY-A2A3`；Issues `phase2b-q/` 53–56；**不在本 SPEC 范围**） |
| 主测试接缝 | **S0** 合门禁；**S1** HTTP assist 作业面；**S2** 检索/忠实/金标质量旁路（不进默认绿） |
| 术语 | `CONTEXT.md`（**Demo 检索种子**、**金标薄切片**、**辅助拒答**、**AI 辅助建议**、**裁决草案**） |

**继承声明：** 2a 作业壳 / 混检 / LangSmith / Eval Ops 外形继续有效。本 SPEC **仅**加深 Claims Assist **质量与诚实性**；默认权威仍是确定性轨 A + 人闸。

**明确废弃作 DoD：** 「RAG/Agent/Eval 均 ≥9 分」「组件清单覆盖即深度」。

---

## Problem Statement

Phase 2a 已能演示双轨与评测台外形，但核赔员点「AI 辅助」时仍面临：Pilot 默认哈希 embedding 冒充语义、自由文本易出假引用、无明确辅助拒答、作业壳几乎总是可点采纳。内审无法用冻结人写集与人工金标薄切片证伪检索/引用质量；Demo 讲解易被追问是否「真语义检索 / multi-agent」。需要把 Assist 做成**可引用、可拒答、可回归**的辅助起草，且合门禁不被评测绑架。

## Solution

交付 **Claims Assist Quality（流 P）**，分 α 证据地基与 β 可证伪质量；γ 仅在假设失败时触发（附录，不预切无条件票）：

- Pilot 默认 **cloud 语义 embedding**；CI 可用 local 哈希并标明非语义  
- Assist **JSON Schema citation 槽** + 三联门；非法不可采纳；采纳后仍须 evaluate  
- **Demo 检索种子**（40 查询）冻结进 git；**金标薄切片**（双人+第三人，α 目标 n≥10）  
- **辅助拒答**：`assist_disposition`；作业壳可见原因；abstain **禁用采纳**；可 CTA 走人闸但不自动发令牌  
- App 拥有白名单工具环；越权写入 latch/支付/evaluate 权威字段 = 0  
- 关键词腿 **BM25**；条款号短路保留；span 树可本地回放  
- α 忠实检查以**规则/夹具**为主；β 填 κ 与三维 S2 质量门（旁路）  
- **Provider 管理**：α 文档清单；β 只读连接状态（永不回显 Key）；LLM 与 Embedding Key 分离  

流 Q（Missions A2/A3）**另页 SPEC**，且须等本 SPEC 的 **α DoD** 关闭后再开。

---

## DoD Checklist

### α 证据地基（`phase2b-p-α`）— **closed 2026-09-16**（Issue 44 / GitHub #31；验收 `本项目代码/claims-gate/docs/acceptance/alpha-dod.md`）

- [x] Pilot 默认语义 embedding 路径可配置为 cloud；local 哈希仅 CI/rebuild 且文案标明非语义  
- [x] Assist 输出含 citation Schema 槽；非法 citation 不可采纳；采纳路径仍 evaluate  
- [x] Demo 检索种子 40 条（15 条款号 + 20 语义难例 + 5 拒答/冲突）进 git 冻结；**不得称金标**  
- [x] 金标薄切片协议 + 导入导出/`case_id`；α 目标 n≥10；不足则 H4 标 `deferred`、禁止宣称 grounded  
- [x] `assist_disposition=draft|abstain` + 原因枚举；abstain 禁用采纳；壳用户可见；不自动发人闸令牌  
- [x] 工具环仅 `retrieve` / `validate_citation` / `draft_slots`（或等价白名单）；越权负例可测  
- [x] span：retrieve→fuse→gate→llm→(adopt|abstain)→evaluate；无 LangSmith Key 可本地 JSONL 回放  
- [x] 关键词腿 BM25（jieba）；条款号短路保留  
- [x] 引用→断言忠实检查（规则/夹具）；非 LLM-as-judge 主指标  
- [x] Provider 清单写入 USER_GUIDE + `.env.example` 分区；分 Key 约定明确  
- [x] **H3 / H6 / H7 可演示**；H1 种子集存在  
- [x] 默认 `pytest -q` 无 LLM / 无 LangSmith 仍绿  

### β 可证伪质量（`phase2b-p-β` · Blocked by α DoD）

- [x] 条款项级切块 + 父条款回填；人可改 chunk 后重建；citation 仍三联门  
- [x] 在冻结 Demo 检索种子上跑 Recall@K / MRR（S2/nightly）；对照 H1/H2 门槛  
- [x] 三维 S2：检索 / 引用忠实 / 建议可用性；LLM 打分不得当唯一主指标  
- [x] 夜间 S2 质量门失败可告警且不红轨 A；手册写清旁路  
- [ ] assist 步数≤4 外形（retrieve→gate→draft→self-check）；架构 app-owned  
- [ ] Judge–human agreement / κ 实填（绑金标薄切片）；合成样例不得冒充  
- [ ] 只读「连接状态」页/API（已配置？降级？模型名？无 Key）  
- [ ] **H1/H2 有数**；**H4/H5 有金标线**（或诚实 deferred）  
- [ ] 用户手册已同步 α/β 用户可见行为；触发项（γ）未写成已上线  

### γ（仅触发 · 见附录 · 不预切无条件实现票）

见 Further Notes「γ 触发附录」。未触发不得实现 rerank / MultiQuery / fan-out / 往榜灌质量主指标。

---

## User Stories

1. As a 核赔员, I want 在可起草时看到带合法 citation 槽的 AI 辅助建议, so that 我能采纳可核对的引用而非自由幻觉文本。  
2. As a 核赔员, I want 辅助拒答时壳上看到原因且无法点采纳, so that 不确定时不会把 AI 辅助建议送进门禁。  
3. As a 核赔员, I want 拒答时可看到走人闸提示但不自动获得人闸令牌, so that 人闸权威不被 UI 冒领。  
4. As a 核赔员, I want AI 辅助建议区持续标明非终裁, so that 我不会把辅助当成裁决草案或出款就绪。  
5. As a 内审, I want 冻结的 Demo 检索种子可回归 Recall, so that 检索质量可证伪而非口头宣称。  
6. As a 内审, I want 金标薄切片上的忠实率与 κ 可报告, so that grounded 宣称有门槛。  
7. As a 内审, I want 评测分数永不成为默认合门禁条件, so that 轨 A 不被绑架。  
8. As a Demo 讲解人, I want 15 分钟讲清双轨、语义 embedding 诚实默认、拒答与降级, so that 不被「假 multi-agent / 假语义」追问击穿。  
9. As a 运维, I want Pilot 默认 cloud embedding 且 CI 可用 local 哈希, so that 演示有语义、CI 仍确定性。  
10. As a 运维, I want LLM Key 与 Embedding Key 分离配置, so that 一侧缺失时诚实降级而非静默复用。  
11. As a 运维, I want `.env` 为唯一密钥写处且作业壳不持 Key, so that 密钥面可审计。  
12. As a 运维, I want Provider 清单与连接状态（无 Key 回显）, so that 我知道当前用哪家模型/是否降级。  
13. As a 开发者, I want 换 OpenAI-compatible 国产端点时只需改 env、重建索引并重测 H, so that 不必另开换模大波。  
14. As an AI 辅助路径, I want 条款号查询走短路且 Recall@1 达标, so that 向量噪声不淹没法律定位（H1）。  
15. As an AI 辅助路径, I want 无条款号时混检在种子集上可报告 Recall@5/MRR, so that H2 可证伪。  
16. As an AI 辅助路径, I want 关键词腿使用 BM25（中文分词）, so that 中文检索可回归。  
17. As an AI 辅助路径, I want 提名必须过 doc_id+clause_item+version 三联门, so that 检索≠合法 citation（H3）。  
18. As an AI 辅助路径, I want 引用支撑断言的忠实检查, so that 格式合法但语义不支撑时不可宣称 grounded（H4）。  
19. As an AI 辅助路径, I want 冲突 / 手册 alone / 低置信 / 不忠实时 abstain, so that H5 成立。  
20. As an AI 辅助路径, I want 工具环不能写 latch/支付/evaluate 权威字段, so that H6 成立。  
21. As a 规则引擎, I want evaluate 永不依赖向量或 LLM, so that H7 与决策 18 成立。  
22. As a CI Owner, I want 质量门与真 LLM/LangSmith 测在 S2 标记下, so that 默认 `pytest -q` 保持绿。  
23. As a 金标 Owner, I want 导入导出与 case_id 承接薄切片, so that 不假装 ≥300 运营已完成。  
24. As a 金标 Owner, I want 双人标注 + 第三人裁决协议写入验收, so that Demo 种子不会冒充金标。  
25. As an Observability Owner, I want assist span 与本地 JSONL / LangSmith 同构, so that 无云 Key 也能回放。  
26. As a 产品经理, I want 条款项级切块与父条款回填, so that citation 粒度对齐决策 17。  
27. As a 产品经理, I want 夜间 S2 质量失败告警且不红轨 A, so that 质量旁路诚实。  
28. As a 架构师, I want assist 步数预算≤4 且 app 拥有编排, so that 不口头售卖第二套 Agent 平台。  
29. As a 架构师, I want γ 项仅在 H 失败或基线具备时才实现, so that 不堆 rerank/MultiQuery/fan-out。  
30. As a 文档维护者, I want 用户手册同步拒答、Provider、种子/薄切片边界, so that 不把 γ 或 Deferred 写成已上线。  
31. As a coding agent, I want 票内 `Rewrote from` 指向 COURSE-03 / FC / RECALL / KB / OPENEVALS / EVAL-ADVISOR / DELIBERATIVE, so that 加深缺口而非平行重切。  
32. As a coding agent, I want β 票 Blocked by α DoD, so that 证据地基先于可证伪加深。  
33. As an Eval Owner, I want 未冻结种子前不往 W2 榜灌质量主指标, so that 有榜≠有质量（P-E4 γ）。  
34. As a 安全负责人, I want 前端无法配置 API Key, so that 密钥不进浏览器。  
35. As a 合规负责人, I want 向量与 LLM 永不进入 evaluate, so that 合门禁保持确定性。

---

## Reference Projects

| 能力 | ref_id | 备注 |
|------|--------|------|
| Schema / 契约槽 | `REF-COURSE-03` | citation 槽、非法硬停外形 |
| 工具环外形 | `REF-CASE-FC` | 白名单工具；非 SQL 票务 |
| BM25 / 召回脚本 | `REF-CASE-RECALL`, `REF-CASE-KB` | Jaccard→BM25；造问仅增广隔离 |
| 切块协议 | RAGFlow **模板切块姿势**（不整仓入库） | + `REF-CASE-KB` |
| 忠实 / 实验外形 | `REF-CASE-OPENEVALS`, `REF-CASE-EVAL-ADVISOR` | 非 LLM judge 主指标 |
| 四步状态外形 | `REF-CASE-DELIBERATIVE` | ≤4 步；app-owned |
| 中继 / 门禁 | `REF-MISSIONS` | 合门禁与 ledger；本 SPEC 不升 A3 |
| rerank（γ） | `REF-CASE-RERANK` | **仅 H2 仍失败** |

禁止：OpenManus 替中继；RAGFlow Agent/MCP 替门禁；造问当金标；门票 SQL 工具当核赔工具。

---

## Implementation Decisions

1. **范围：** 本 SPEC = 流 P（α+β 无条件 + γ/Deferred/换模/P-CFG 附录）。流 Q 另页，Blocked by **α DoD**。  
2. **接缝：** S0 = 默认 `pytest -q` / `machine_check`；S1 = HTTP assist（最高用户可见缝）；S2 = 质量/真 LLM/LangSmith 旁路。作业壳只依赖 API 字段，不断言 React 内部 state。  
3. **J1 语义：** 仅 `draft` 且 citation 过门方可采纳；`abstain` 禁用采纳。  
4. **Disposition 契约（原型级形状）：**  
   `assist_disposition: "draft" | "abstain"`；  
   `abstain_reason?: "conflict" | "handbook_alone" | "low_confidence" | "citation_unfaithful"`；  
   abstain 时建议体不可送交采纳；可返回 `human_latch_suggested=true` 但不得签发 `human_latch_token`。  
5. **Embedding：** Pilot 文档与推荐默认 = `EMBEDDING_PROVIDER=cloud` + 独立 embedding Key；`local` = 确定性哈希，须标明非语义。缺 embedding Key **不得**静默使用 `OPENAI_API_KEY`。  
6. **LLM：** OpenAI-compatible；参照默认 `gpt-4o-mini`；Key 仅 `claims-gate/.env`。  
7. **Demo 检索种子：** 恰好 40 条结构（15+20+5）；人写；版本进 git；污染隔离；不得称金标。  
8. **金标薄切片：** 外聘核赔顾问 + 第三人角色占位（人名不进仓）；α n≥10 否则 H4=`deferred`。复用 W2 导入导出/`case_id` 钩子加深。  
9. **H 门槛（失败则停堆组件，不上未触发 γ）：**  
   - H1: Recall@1 ≥ 0.95（n≥15 条款号）  
   - H2: Recall@5 ≥ 0.70 **或** MRR ≥ 0.55（n≥20 语义难例）  
   - H3: 采纳路径非法 citation = 0  
   - H4: 忠实率 ≥ 0.85；κ ≥ 0.60 才可宣称 grounded  
   - H5: 预登记拒答场景覆盖率 100%；误起草率 ≤ 5%  
   - H6: 越权写入权威字段 = 0  
   - H7: 无 LLM/无 LangSmith 下轨 A 绿  
10. **工具环：** app-owned；允许 retrieve / validate_citation / draft_slots；禁止 latch/支付/evaluate 权威写。步数预算 α 可先有上限，β 收紧≤4。  
11. **检索：** 保留效力栈硬过滤与条款号短路；关键词腿改为 BM25（jieba）；线性融合默认 0.7/0.3 直至 γ 的 RRF 实验。  
12. **切块（β）：** 条款项级 + 父条款回填；重建命令保留；citation 仍三联门。粒度默认：一 clause_item 一块，过长按段落切并回填父 id。  
13. **忠实（α）：** 规则/夹具（摘录含关键实体或预登记支撑关系）；β 再填人工 κ。  
14. **P-CFG：** α = USER_GUIDE Provider 表 + `.env.example`；β = 只读连接状态 API/壳区块。  
15. **告警（β）：** 默认形态 = 本地/日志可检测的 S2 失败产物 + 手册说明；不强制邮件；永不 fail S0。  
16. **票夹：** `phase2b-p-α/`、`phase2b-p-β/`；β Blocked by α DoD 票；全局编号 34+。  
17. **用户手册：** 用户可见合入须按 `docs/user/MAINTENANCE.md` 更新；γ/Deferred 禁止写成已上线。  

---

## Testing Decisions

1. **好测试：** 只断言外部行为（HTTP 状态与字段、RBAC、disposition、采纳拒绝、citation 门、降级文案、冻结集指标文件/退出码）。不断言 React 内部 state、Chroma 底层段、LangSmith 专有 UI。  
2. **S0：** 既有轨 A / RBAC / evaluate 回归；本波不得因缺 LLM/LangSmith/cloud embedding 而红。  
3. **S1：** assist disposition、abstain 禁用采纳、Schema 非法 citation、工具 ACL 负例、连接状态无 Key 泄漏；可用假 LLM/夹具，不必真云调用进默认绿。  
4. **S2：** Demo 检索种子 H1/H2；金标薄切片 H4/H5；忠实规则；可选真 embedding/LLM。标记延续 `track_llm_optional` / `eval_bypass` / `requires_llm` / `langsmith_integration`；如需可增 `assist_quality`，但须写入 pytest markers 且默认 addopts 排除。  
5. **Prior art：** `tests/test_assist_api_degrade_adopt.py`、`tests/track_llm_optional/`、`tests/eval/`、W2 金标 IO 测、套餐 L 清单。  
6. **违规：** 默认 CI 因缺 Key 失败；质量阈值写入 machine_check；LLM-as-judge 作 H4 唯一主指标。  

---

## Out of Scope

- 流 Q（Orchestrator Schema / Worker 真 patch / Validator 独立模型）— 见 [`spec-2b-q-relay-a2a3.md`](./spec-2b-q-relay-a2a3.md)；完成旗隔离  
- γ 未触发项：RRF、rerank、MultiQuery/rewrite、只读 fan-out、往榜灌质量主指标  
- ≥300 金标运营、真用户 M3/M4、真连 L2、真 OCR/DeepDoc、GraphRAG、ES/Infinity  
- L3 出款、银企直连、UI 签发人闸、自审自批  
- RAGFlow/Dify/CrewAI/OpenManus 替门禁或中继；RAGFlow 整仓入库  
- 评测进默认绿；向量进 evaluate  
- 前端配置 API Key；Langfuse 双写主路径；成本看板（Deferred）  
- 宣称「硅谷 9 分 / Anthropic 生产档」  

---

## Further Notes

### α / β 退出与 Q 解锁

- **α DoD：** α 清单勾选 + H3/H6/H7 可演示 + H1 种子存在 + S0 绿。  
- **β DoD：** β 清单勾选 + H1/H2 有数 + H4/H5 有金标线或诚实 deferred。  
- **解锁流 Q：** 仅 α DoD（不必等满 β）。  

### γ 触发附录（失败才做）

| ID | Trigger | 工项 |
|----|---------|------|
| P-R5 | H2 失败 | 0.7/0.3 vs RRF A/B；赢家回写 |
| P-R6 | H2 在 R5 后仍失败 | 轻量 rerank；双阈；可关 |
| P-R8 | 单查询失败模式已记录 | Query rewrite / MultiQuery；可关；不进 evaluate |
| P-A5 | P-A1 延迟/覆盖不足 | 只读 fan-out；`owns_paths=none`；须宪/N2 边界 |
| P-E4 | P-G1 冻结且 H1/H2 有基线 | 实验矩阵 + 往既有 W2 榜灌质量主指标（仍 S2） |

### Deferred 指针

P-R9 OCR/多模态；P-E7 成本/Langfuse 只读；Q-A7 Production latch；N1 修宪；N11 L3 须新 PRD。

### 换模检查单（不预切票）

1. 改 `.env`（分 Key）→ 2. cloud embedding 时重建 Chroma → 3. 冻结集重测 H1–H5 → 4. 更新 Provider 清单/连接状态模型名 → 5. 手册标明参照模型；不得宣称合门禁升级。

### 修订记录

- 2026-09-15：`/to-spec` 自质询决议与 `draft-decided` 规划清单发布；接缝 S0/S1/S2 经人类确认。
- 2026-09-16：α DoD 关闭（Issue 44）；验收见 `本项目代码/claims-gate/docs/acceptance/alpha-dod.md`；解阻 β 与 SPEC-Q。  
- 2026-09-16：SPEC-Q 已发布；流 Q Issues 53–56 切票（完成旗与本 SPEC 隔离）。

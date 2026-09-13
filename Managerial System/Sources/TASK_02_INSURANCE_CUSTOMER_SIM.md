# 任务 02 — 保险承保/理赔裁决（客户模拟用）

## A. 任务介绍（给模拟 AI / 后续开发）

| 字段 | 说明 |
|------|------|
| task_id | `SIM-CUST-02-INSURANCE` |
| scenario_name | 保险承保或理赔政策到裁决/功能门禁 |
| our_product | Policy-to-Feature Missions（同中继，换保险 KB + 契约 schema + 赔付人闸） |
| value_catalog | `customer_sim/PRODUCT_VALUE_CATALOG.md` |
| industry_brief | `customer_sim/BACKGROUND_02_INSURANCE.md`（填表前必读：行业语境、AI 情报、主题库） |
| simulation_goal | 扮演**保险公司（财险/健康险/寿险择一）买方客户**，产出可驱动「规则与材料 → 验收契约 → 实现/裁决流水线 → 独立校验 → 赔付人闸」的需求与价值映射 |
| architecture_fit | 强调：承保/理赔**规则条款**进 RAG；Worker 产出可测行为或结构化裁决草案；Validator 对照条款引用打分；高额赔付/自动出单必须人闸 |
| out_of_scope | 不做临床诊断建议；不做纯客服话术机器人；不宣称无人审批自动打款到客户账户 |
| fill_policy | **第 B 节全部留空**；模拟时另存 `filled/SIM-CUST-02-*.yaml` |
| quality_bar | Must 需求须能映射到契约断言、引用覆盖、失败关闭、人闸中至少两类 VP |

### A.1 模拟角色指令（填表时遵守）

```text
你是保险公司侧客户（产品/理赔/风控/IT 需在干系人中出现）。
垂直锁定：underwriting（承保）或 claims（理赔）二选一为主，另一项可作 Should/Could。
痛点围绕：条款与系统规则不一致、材料抽取差错、拒赔理由不可追溯、自动赔付无闸。
价值主张只能引用 PRODUCT_VALUE_CATALOG 的 value_prop_id。
可用 VP-DOMAIN-SWAP 表达「与金融合规共用同一套中继」。
禁止把「AI 直接最终拒赔且不可申诉」写成 Must（与人闸/合规冲突）。
```

### A.2 期望产出物（填完后）

- 完整 B1–B4
- 明确主垂直：`underwriting` 或 `claims`
- 可选：一条薄切片（如「单险种免赔额断言 + 补件清单」）

---

## B. 客户模拟框架模板（留空，勿预填业务内容）

### B1. 客户所在行业与业务背景总体介绍

```yaml
section: industry_and_business_background
status: EMPTY_TO_FILL

industry:
  sector: "insurance"
  line_of_business: ""          # property | health | life | auto | ...
  primary_vertical_for_pilot: "" # underwriting | claims
  regulators_and_regimes: []
  company_type: ""              # 总公司/分公司/相互保险等
  company_size_hint: ""

business_context:
  products_in_scope: []         # 试点险种/条款集
  current_systems: []           # 核心、理赔系统、影像、规则引擎、文档库
  policy_and_clause_lifecycle: ""
  document_types_in_play: []    # 保单条款、投保单、案件材料、公估报告等
  recent_trigger: ""            # 错赔/监管处罚/成本/SLA
  constraints:
    compliance: []
    technical: []
    organizational: []

narrative_overview: |
  <!-- 客户描述机构、险种、为何要用「条款→可验收行为/裁决」而非纯聊天问答 -->
```

### B2. 关键干系人（目标用户是谁）

```yaml
section: stakeholders
status: EMPTY_TO_FILL

stakeholders:
  - stakeholder_id: ""
    role_title: ""
    org_unit: ""                # 承保 / 理赔 / 风控合规 / IT / 精算 等
    persona_type: ""            # decision_maker | economic_buyer | end_user | influencer | blocker
    goals: []
    pains: []
    success_looks_like: ""
    interacts_with_our_product_as: ""  # 例：维护条款 KB / 审批赔付人闸 / 查看校验报告
```

### B3. 需求（收益、痛点）与 MoSCoW 排序

```yaml
section: requirements_moscow
status: EMPTY_TO_FILL

requirements:
  - requirement_id: ""
    moscow: ""                  # Must | Should | Could | Won't
    title: ""
    pain: ""
    benefit: ""
    acceptance_hint: ""         # 例：拒赔理由带条款引用；未过人闸不得进入支付状态
    primary_stakeholders: []
    related_clause_themes: []   # 免赔、等待期、除外责任、材料齐全性等
    notes: ""

moscow_summary:
  Must: []
  Should: []
  Could: []
  Wont: []
  ranking_rationale: |
    <!-- 按错赔成本、监管、周期、可验收性排序的理由 -->
```

### B4. 需求 ↔ 我方价值主张映射

```yaml
section: value_proposition_mapping
status: EMPTY_TO_FILL
catalog_ref: customer_sim/PRODUCT_VALUE_CATALOG.md

mappings:
  - mapping_id: ""
    requirement_ids: []
    value_prop_ids: []
    cardinality: ""             # 1:1 | 1:N | N:1 | N:N
    mapping_rationale: ""
    demo_observable: ""
    unmet: false
    unmet_gap: ""

coverage_check:
  all_must_mapped: null
  unmapped_requirement_ids: []
  unused_but_relevant_vp_ids: []
```

---

## C. 填表完成后的自检清单（仍不预填答案）

- [ ] 已声明主垂直 underwriting 或 claims  
- [ ] B2 含理赔/承保业务用户与合规/风控  
- [ ] Must 含「可追溯条款引用」类需求  
- [ ] Must 含「高额或对外给付人闸」类需求，或 Won't 明确排除自动打款  
- [ ] B4 无编造 VP；建议出现 VP-RAG-CITE、VP-FAIL-CLOSED、VP-HUMAN-LATCH  
- [ ] 若强调与金融共用平台，可映射 VP-DOMAIN-SWAP  

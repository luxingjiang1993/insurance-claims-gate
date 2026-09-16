# Spec — Phase 2c · Live Honest Seams（面试诚实 8 分档 / Integration-Ready）

| 字段 | 内容 |
|------|------|
| feature_slug | `insurance-claims-gate` |
| spec_id | `SPEC-02C-LIVE-HONEST-SEAMS` |
| wave | `2c`（实现目录 `phase2c/`） |
| Status | `closed` |
| 档位决议 | 档 **2 减 G1**：G0 + G2 + G3 最小（L2+OCR）+ G4；**本窗口不冲诚实 9 / 不宣称 grounded** |
| 前置 | Phase 2b P/Q closed；[`spec-2b-p-assist-quality.md`](./spec-2b-p-assist-quality.md)、[`spec-2b-q-relay-a2a3.md`](./spec-2b-q-relay-a2a3.md) 继承；决策 16–18 与 I1–I8 继续有效 |
| 后继 | 附录 H4（双标金标）仅可选；A5 / 真连现网 / KB≥20 不在本 SPEC 必做 |
| 主测试接缝 | **S0** 合门禁；**S1** HTTP Assist / 连接状态 Live；**S2** 检索双剖面旁路；**S3** L2/OCR Provider 契约（InMemory + Recorded） |
| 术语 | `CONTEXT.md`（**AI 辅助建议**、**裁决草案**、**人闸令牌**、**出款就绪**、**Demo 检索种子**、**金标薄切片**、**Integration-Ready**） |

**继承声明：** 轨 A `machine_check`、Assist 拒答/三联门、Missions A2/A3、默认 CI 无 Key 绿继续有效。本 SPEC **仅**交付 Live 可演示路径、检索诚实双剖面、L2/OCR 可插拔接缝与面试/手册诚实同步。

**明确废弃作 DoD：** 「冲面试条 9」「H4 grounded」「雷达图堆满即过线」「Issues closed = 已上线 / 已接核心」。

**对外称呼：** 对面试官称「面试诚实 8 分档」；材料副标题可写「准生产接缝 / Integration-Ready」（Ready ≠ Deployed）。

---

## Problem Statement

Phase 2b 已关闭且 H4 诚实 `deferred`，但面试与演示仍易被三处击穿：（1）有 Key 时缺少可勾选的 **Live** 验收剖面，听众以为「只有降级」；（2）S2 召回常只报关键词/短路剖面，易留下 **Recall=1.00 假象**；（3）L2 仍是进程内模拟回写、OCR 仅 strip，听众以为「假成熟」，又没有可换真供应商的契约与录制夹具。本窗口**没有第二核赔标人**，不能诚实消灭场效度短板，故不得宣称 grounded 或冲 9；需要把「不可辩护的演示/接缝短板」变成可证伪的 Live + 双剖面 + Integration-Ready，并同步诚实表与开场话术。

## Solution

交付 **Live Honest Seams（流 2c）**，固定本窗口包：

- **G0 Live：** 双 Key + cloud embedding 重建；有 Key 真 Assist 起草；`requires_llm` / Live 套餐旁路绿；缺 Key 仍明确降级；默认 `pytest -q` 仍绿  
- **G2 语义诚实：** 并列报告 `demo_seed_eval` 与 `pilot_cloud_embed`（向量开）；口头/文档**先报剖面再报数**；γ（rerank 等）仅当 `pilot_cloud_embed` 上 H2 失败才触发  
- **G3 最小接缝：** **L2 Core Adapter** + **OCR Provider** 接口；各提供 InMemory/Stub 与 Recorded 实现；契约测绿；换适配器不改门禁；注入 OCR/用户文本仍不得翻 latch；**本窗口不扩 KB≥20**  
- **G4 叙事同步：** 诚实表 / USER_GUIDE / demo 脚本 / S2 指标卡与证据一致；开场固定承认 H4 deferred  

**G1 / H4 过线** 本窗口不做；仅附录预留「若日后真双标 n≥10 + κ + 忠实率」可选解锁，不进必做票。

---

## DoD Checklist

### 本窗口必做（`phase2c/`）

- [x] G0：双 Key 分区可用；`EMBEDDING_PROVIDER=cloud` 重建索引；连接状态双绿且永不回显 Key → 票 57 / `docs/acceptance/live-pilot-g0.md`  
- [x] G0：`enable_llm=true` 有 Key → 真 structured draft；缺 Key → 明确降级文案（回归） → 票 57  
- [x] G0：Live 验收清单可勾完；`pytest -m requires_llm`（有 Key 环境）旁路绿；默认 `pytest -q` 无 Key 仍绿 → 票 57 / 62（S0：`337 passed, 26 deselected`）  
- [x] G2：检索报告并列 `demo_seed_eval` 与 `pilot_cloud_embed`；禁止只甩短路/关键词 1.00 冒充语义满分 → 票 58  
- [x] G2：面试/手册脚本含「先剖面后数字」；evaluate 仍零向量/零 LLM 依赖 → 票 58 / 61  
- [x] G3：L2 Provider 接口（出款就绪回写 / 结案）+ InMemory + Recorded；契约测；HTTP 行为与人闸不变 → 票 59  
- [x] G3：OCR Provider 接口（extract → 规范化文本）+ Stub + Recorded（或一家可开关真实实现）；威胁测：注入文本不得翻 latch / 不得签发人闸 → 票 60  
- [x] G3：文档与诚实表写明 **Integration-Ready**，禁止「已接核心 / 已上线 OCR」 → 票 59–61  
- [x] G4：诚实表、USER_GUIDE、demo 脚本、S2 指标卡翻到与本 SPEC 证据一致；开场含 H4 deferred → 票 61  
- [x] 本窗口文案**不**宣称 grounded / 面试条 9 / A5 / L3 / ≥300 金标 → 票 61 / 62 验收摘要  

验收摘要：`本项目代码/claims-gate/docs/acceptance/package-live-honest-seams.md`（Issue 62）。

### 附录（可选 · 不预切必做票）

- [ ] H4：真双标金标薄切片 n≥10；κ≥0.60；忠实率≥0.85 → 才可改口 grounded（须新开 SPEC/票） · **本窗口未做；保持 deferred**  

---

## User Stories

1. As a Demo 讲解人, I want 有 Key 时当场跑通真 LLM Assist 起草, so that 听众看到的不是永远降级的空壳。  
2. As a Demo 讲解人, I want 缺 Key 时仍看到明确降级文案, so that 双路径都可辩护。  
3. As a Demo 讲解人, I want 60 秒开场承认 H4 deferred 且不说 grounded, so that 不被「金标已过」追问击穿。  
4. As a Demo 讲解人, I want 先报检索剖面再报 Recall 数字, so that 不会被 1.00 假象反噬。  
5. As a 核赔员, I want Live 下 Assist 仍受三联门与辅助拒答约束, so that 真模型也不能绕过 citation 纪律。  
6. As a 核赔员, I want 采纳 AI 辅助建议后仍走 evaluate, so that AI 辅助建议不变成裁决草案权威。  
7. As a 核赔员, I want 人闸令牌仍只能由合规角色签发, so that Live 不削弱人闸。  
8. As a 核赔员, I want 出款就绪仍仅在人闸后置位且不触发支付, so that Integration L2 回写 ≠ L3。  
9. As a 运维, I want LLM Key 与 Embedding Key 分离, so that 一侧缺失时诚实降级。  
10. As a 运维, I want cloud embedding 下可一键重建索引, so that Live 向量腿与索引一致。  
11. As a 运维, I want 连接状态显示已配置/降级/模型名且不回显 Key, so that 演示前可自检。  
12. As a 内审, I want `demo_seed_eval` 与 `pilot_cloud_embed` 两份可并存报告, so that 短路满分与语义剖面可对照。  
13. As a 内审, I want 评测分数永不进入默认合门禁, so that 轨 A 不被绑架。  
14. As a 内审, I want H4 在本窗口保持 deferred 文案, so that 无人双标时不假装 grounded。  
15. As a 内审, I want 将来若有真双标可走附录解锁, so that 不必推倒 Live/接缝成果。  
16. As a 集成工程师, I want L2 回写通过 Provider 接口而非写死模拟, so that 换 Recorded/真核心不必改门禁。  
17. As a 集成工程师, I want Recorded 夹具可在无保司账号时跑绿契约测, so that Integration-Ready 可验收。  
18. As a 集成工程师, I want OCR 通过 Provider 产出规范化文本, so that 不再只有不可插拔的 strip 观感。  
19. As a 安全负责人, I want OCR/用户可控文本注入仍不能翻 latch, so that 接缝加深不破威胁模型。  
20. As a 安全负责人, I want 支付适配器计数在 L2 路径仍禁止递增, so that 不暗示 L3。  
21. As a CI Owner, I want 默认 `pytest -q` 无云 Key 仍绿, so that Live 测只在旁路标记。  
22. As a CI Owner, I want Recorded/Stub 契约测进默认或明确旁路策略且不依赖现网, so that S3 可回归。  
23. As a 文档维护者, I want 诚实表与 USER_GUIDE 同步 Live / 双剖面 / Integration-Ready, so that 材料不撒谎。  
24. As a 文档维护者, I want demo 脚本含 Live 分支与 H4 deferred 开场, so that 讲解可复现。  
25. As a 产品经理, I want 本窗口不做 KB≥20, so that 日历留给接缝与 Live。  
26. As a 产品经理, I want 本窗口不做 A5 / Mission Control, so that 不把 Production latch 口头售卖。  
27. As a 架构师, I want γ 仅在 pilot_cloud_embed 的 H2 失败时触发, so that 不无谓堆 rerank。  
28. As a 架构师, I want 自治阶梯 A* 与 Integration L* 在文案中不混称, so that 面试不把 Adapter 说成 A5。  
29. As a coding agent, I want 票内 Rewrote from 指向既有 Embedding Provider / 威胁测 / Missions 基线, so that 加深缺口而非另起炉灶。  
30. As an 面试官（假想）, I want 听到 Ready≠Deployed 与 H4 deferred, so that 诚实叙述下系统接缝分可辩护。

---

## Reference Projects

| 能力 | ref_id | 备注 |
|------|--------|------|
| 中继 / 合门禁 / L2 人闸外形 | `REF-MISSIONS` | 换 Adapter 不改 latch 语义 |
| Embedding Provider 既有姿势 | （仓内既有 Protocol） | G0/G2 加深验收剖面，不重写客户端 |
| 召回 / 种子 | `REF-CASE-RECALL`, `REF-CASE-KB` | 双剖面报告；造问不得并入主集 |
| 威胁 / 注入 | 仓内既有 OCR remark 威胁测 | OCR Provider 不得削弱 |
| rerank（γ） | `REF-CASE-RERANK` | **仅** pilot_cloud_embed 上 H2 失败 |

禁止：OpenManus 替中继；一人双角色冒充金标；宣称已接核心；L3；把 Adapter 完成说成 A5。

---

## Implementation Decisions

1. **范围：** 本 SPEC = G0 + G2 + G3（仅 L2 Adapter + OCR Provider）+ G4。G1/H4 过线、KB≥20、A5、真连现网、γ 无条件项均不在必做。  
2. **成功定义：** 本窗口成功 = 「面试诚实 8 分档」过线（Live 可演示 + 双剖面诚实 + Integration-Ready 契约 + 文案一致）；**不是**预登记 H4 过线的「冲 9」。  
3. **接缝：**  
   - **S0** — 默认合门禁 / `machine_check` / 无 Key 绿  
   - **S1** — HTTP Assist、连接状态、作业壳可见 Live/降级字段  
   - **S2** — 检索指标脚本与报告产物（双 `retrieval_profile`）  
   - **S3** — L2 / OCR Provider 在服务边界的契约行为（最高新缝；避免深入供应商 SDK 测）  
4. **G0：** 沿用分 Key 与 cloud embedding 配置；新增/加深 Live 验收清单（套餐 L 之上 Live 档）；有 Key 环境旁路必跑 `requires_llm` 与 track LLM optional。  
5. **G2：** 引入/固化剖面名 `demo_seed_eval`（可短路/基线）与 `pilot_cloud_embed`（`vector_enabled=true`）；报告与面试话术强制剖面标签；数字可低于 1.0。  
6. **G3 L2：** Provider 能力至少覆盖「出款就绪回写」与「结案」；实现至少 **InMemory（或等价进程内）** + **RecordedHttp/Recorded**；门禁与人闸校验留在核心服务，不下沉到适配器擅自放行。  
7. **G3 OCR：** `extract` → 规范化文本后进入既有用户可控文本收纳路径；Stub + Recorded 必有；真实供应商 API 可开关但不得成为默认 CI 依赖。  
8. **威胁不变式：** 任意 OCR/备注注入不得签发人闸令牌、不得单独造成出款就绪、不得使支付适配计数在 L2 路径递增。  
9. **Integration-Ready 文案：** 契约测绿 + 录制夹具 = Ready；无保司现网账号时禁止 Deployed /「已接核心」。  
10. **γ：** 仅当 `pilot_cloud_embed` 报告显示 H2 未过，才允许开 RRF/轻量 rerank 实验票；默认不上 MultiQuery/fan-out/灌榜。  
11. **H4 附录：** 保持 `deferred`；协议与 IO 钩子已存在则只引用不重做；解锁条件写进 Further Notes，不切本波必做票。  
12. **票夹：** `Managerial System/Issues/insurance-claims-gate/phase2c/`；全局编号自 57 起；票首 `Status: ready-for-agent`、`wave: 2c`、`spec_id: SPEC-02C-LIVE-HONEST-SEAMS`。  
13. **用户手册：** 按 `docs/user/MAINTENANCE.md` 在用户可见合入与 DoD 关闭时更新；Deferred/附录不得写成已交付。  
14. **术语：** 文案区分 **Integration L2**（核心回写）与 **自治 A5**（Production latch）；本 SPEC 只碰前者的 Adapter 化。  

---

## Testing Decisions

1. **好测试：** 只断言外部行为（HTTP 字段与状态、RBAC、disposition、降级文案、剖面标签、Adapter 契约输入输出、注入后 latch/出款就绪不变、报告文件含剖面名）。不断言 React 内部 state、供应商 SDK 私有类型、录制文件字节级无关细节。  
2. **S0：** 既有轨 A / 人闸 / evaluate 回归；缺云 Key 不得红。  
3. **S1：** Live/降级双路径字段；连接状态无 Key 泄漏；Assist 采纳纪律回归（可用假 LLM 进默认绿）。  
4. **S2：** 双剖面指标可生成；禁止无剖面标签的「唯一满分」验收。真云调用仅旁路标记。  
5. **S3：** L2/OCR 契约：同一用例在 InMemory 与 Recorded 下行为一致（在契约范围内）；威胁注入负例保留/扩展。  
6. **Prior art：** 套餐 L 验收、`requires_llm` / `track_llm_optional`、recall S2 验收、`test_threat_inject_ocr_remark`、L2 payout-ready 人闸测、Embedding Provider Protocol。  
7. **违规：** 默认 CI 依赖真保司/真 OCR 账号；质量分写入 machine_check；一人双标冒充 H4；把 Recorded 绿写成「已接核心」。  

---

## Out of Scope

- G1：真双标金标薄切片 n≥10、κ 达标宣称、H4 grounded（本窗口）  
- KB 扩到 ≥20、作业壳「满配 Live 清单」中非本 DoD 项的美化堆料  
- A5 / Q-A7 / Mission Control / credential proxy / pause-resume  
- 真连保司现网核心（无搭档则永不宣称）  
- L3 自动出款、银企直连、秒赔叙事  
- ≥300 运营金标  
- γ 无条件实现（RRF/rerank/MultiQuery/fan-out/灌榜）  
- 放松 I1–I8；向量/LLM 进入 evaluate  
- 用 OpenManus/Dify/LangGraph 整仓替换 Missions  

---

## Further Notes

### 测试接缝确认（发布时默认采用）

| ID | 缝 | 断言焦点 |
|----|----|----------|
| S0 | 合门禁 | 无 Key 绿；权威字段不被 Assist/OCR 改写 |
| S1 | HTTP Assist / 连接状态 | Live 与降级；无 Key 回显 |
| S2 | 检索报告旁路 | 双剖面标签与指标文件 |
| S3 | L2/OCR Provider | 契约 + Recorded；威胁不变式 |

若人类要求合并缝：优先保留 S0+S3（权威与接缝），S1/S2 可降为清单手工勾选，但不得取消双剖面标签义务。

### H4 可选附录（失败停堆条件 · 非本波票）

仅当具备两名独立核赔标者 + 第三人裁决，且 n≥10、忠实率≥0.85、κ≥0.60 时，另开 SPEC/票解锁 grounded 宣称。一人双角色 **禁止**。

### γ 触发附录

| Trigger | 允许工项 |
|---------|----------|
| `pilot_cloud_embed` 上 H2 未过 | 可配置 RRF vs 线性；轻量 rerank（可关） |
| 仍失败且已记录失败模式 | 才考虑 MultiQuery（可关）；仍不进 evaluate |

### 档位溯源（质询决议 · 2026-09-16）

- 判据曾定义为「假设过线的 9」，但本窗口无第二标人 → 改写为 **诚实 8 分档**  
- 听众 = 面试；不做 A5；G3 做 L2+OCR 最小、不做 KB≥20  
- 双 Key 已具备；H4 开场固定 deferred  

### 修订记录

- 2026-09-16：`/grill-with-docs` 定档 + `/to-spec` 发布；Status=`ready-for-agent`；Issues `phase2c/` 57+。
- 2026-09-16：Issue 62 DoD 收口；本窗口必做全勾；Status=`closed`；验收 `docs/acceptance/package-live-honest-seams.md`；附录 H4 仍 deferred。

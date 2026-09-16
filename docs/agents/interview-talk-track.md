# Claims Gate — 15 分钟口述轨（N2）

| 字段 | 内容 |
|------|------|
| 配套 | 一页纸 `interview-one-pager.md` · 架构图 `diagrams/claims-gate.architecture.html` · 演示脚本 `interview-demo-script.md` |
| 时长 | 15 分钟口述 + 预留追问；演示另按 N3 计时 |
| 口径 | 截至 2026-09-16；**2c Live Honest Seams**（G0/G2/G3）；对外「面试诚实 **8** 分档」+「**Integration-Ready**」；**不**宣称 grounded / 面试条 9 / A5 / L3 / ≥300 金标 |

---

## 时间盒

| 分 | 块 | 目标 |
|----|----|------|
| 0:00–1:00 | 开场 | 辅助、不替代、不出款；**H4 deferred**；8 分档 |
| 1:00–3:30 | 问题与不变量 | 为什么不能把 RAG 接进终裁 |
| 3:30–7:00 | 架构主路径 | 对着图讲轨 A + 人闸 + L2 Ready≠Deployed |
| 7:00–10:00 | Assist 旁路 | 可拒答、可证伪、先剖面后数字、分数≠合门禁 |
| 10:00–12:30 | Missions 中继 | A2 Schema 硬停 + A3 真 patch；非角色剧场 |
| 12:30–14:00 | 诚实边界 | 先自报缺口，再收尾 |
| 14:00–15:00 | 停顿 | 把球交给面试官 |

超时优先砍：Eval Ops 细节、H1/H2 数字、Q 测试文件名。不可砍：人闸、无 Key 绿、H4 deferred、未宣称 A5 / 面试条 9。

---

## 0:00–1:00 开场（可背）

> 我做的是保险理赔的**条款门禁**：系统出裁决草案和条款项引用，但出款就绪必须过人闸。默认合门禁是确定性规则，不依赖大模型。AI 辅助是旁路——能拒答、引用不过门就不可采纳，分数也不冒充合规。工程上 Missions 中继做到了 Schema 硬停和真 patch。本窗口是**面试诚实 8 分档**、副标题 **Integration-Ready**——**H4 仍 deferred，不宣称 grounded，也不冲面试条 9**；Ready 不等于 Deployed。

若对方已看过一页纸：用半句过渡——「口头口径和一页纸一致，我按图把权威落在哪条缝上。」

---

## 1:00–3:30 问题与不变量

**问题（约 60s）**  
核赔系统若把 LLM/RAG 直接接到裁决，会把「检索到相似条款」和「合门禁」混为一谈。相似不是效力栈；召回分不是 `machine_check`。本产品把权威留在**确定性轨 A + 人闸**；AI 只走可拒答、可证伪、可旁路失败的 Assist。

**五条口头不变量（约 90s，按序，勿展开实现）**

1. 无人闸令牌 → 不得 `PAYOUT_READY`  
2. Worker 不自审自批；Validator 不改产品代码  
3. 默认 `pytest -q` **无 LLM / 无 LangSmith** 仍须绿  
4. 评测分 / 召回分 **≠** `machine_check` 合门禁  
5. 不做 L3 银企直连 / 「秒赔」叙事  

**术语别踩：** 自治阶梯 **A0–A5**（工程中继）≠ 产品 Integration **L1/L2/L3**（核心/支付）。作业壳不持有门禁权威。

---

## 3:30–7:00 架构主路径（打开 U1）

建议先切 **作业主路径** 视图，再口头扫一眼节点：核赔三角色 → 作业壳 → API → 轨 A 裁决门 → 人闸 → L2 出款就绪。上面是条款库 / 效力栈；Assist 是虚线旁路；Missions 是一块中继（A2/A3/H8），不要讲成三个剧场盒子。

**可演示事实（口述即可，点细节丢给 N3）：**

- SC-01 一次补件；SC-02 除外拒赔 + 文书分态；SC-03 批单效力栈减赔。  
- 作业壳三角色：`viewer` 只读、`adjuster` 作业但不能批闸、`supervisor` 批闸拿令牌。  
- `PAYOUT_READY` ≠ 已打款；L2 是 **Integration-Ready** 出款就绪回写 / 结案（InMemory+Recorded），无真连现网；**Ready ≠ Deployed**；禁止「已接核心」。  
- 有 Key 时可走 **Live** 分支（真 Assist）；缺 Key 仍明确降级——两路径都可辩护。

**一句话过渡：** 「壳只是客户端；合不合门，看服务端 `machine_check` 和人闸令牌。」

---

## 7:00–10:00 Assist 旁路

切 **Assist 旁路** 视图。要点只讲契约，不讲模型名。

- 显式点击才调用；无 Key **明确降级**，不挡规则路径；有 Key → Live 真起草（仍过三联门）。  
- 引用须过 citation **三联门**（doc / 条款项 / 版本）；非法或缺槽 **不可采纳**。  
- `assist_disposition=abstain` 时壳禁用采纳；可提示走人闸，**不签发**令牌。  
- 采纳后仍走规则 evaluate。  
- H1/H2 在冻结 Demo 检索种子上**有数**（S2 旁路）；质量门 **不**进默认绿。  
- **先剖面后数字：** 先说 `demo_seed_eval`（向量关）与 `pilot_cloud_embed`（向量开），再报 Recall/MRR；禁止无标签短路 1.00 冒充语义满分。  
- H4 grounded **deferred**（薄切片 n&lt;10）；γ（rerank / MultiQuery / fan-out）**未上线**。

若被追问「检索好不好」：先报测量剖面，再报数字。数字见一页纸 / S2 指标卡 / USER_GUIDE §3.12，面试口头不必背到三位小数。

---

## 10:00–12:30 Missions 中继

切 **Missions A2/A3** 视图。

- **A2：** 契约 JSON Schema 硬停；缺 `goal` / 非法结构 → 入账前失败，不开工。  
- **A3 / H8：** `F-Q-DEMO-01` 真 patch + 非空 `git_commit`；`files_touched` ⊆ `owns_paths`；空 diff / 越权 → 不得 `DONE`。  
- Validator **独立 profile**，运行后产品树无 Validator 写入（轻量 A4 预备，**未宣称 A4 生产**）。  
- **无** Mission Control 作业台；Q-A7（pause/resume + credential proxy）→ **A5 / Production latch Deferred**。

一句话：**中继诚实到 A2/A3；不是把三个角色名贴在 PPT 上。**

---

## 12:30–14:00 诚实边界与收尾

切 **诚实边界** 视图，先自报再收：

| 对方可能以为 | 实际 |
|--------------|------|
| 已 grounded / 冲到 9 | H4 deferred；本窗口停在诚实 **8** 分档 |
| 质量加深已上线 | γ 未触发 |
| 已接核心/OCR | L2/OCR 为 **Integration-Ready**（契约+录制）；**Ready≠Deployed**；真连现网延后 |
| 中继已生产闸 | Q-A7 / A5 未宣称 |
| 评测榜 = 合规 | 榜分 ≠ `machine_check` |
| Frontier 空 = 做完 | 未关票 ≠ 已冲 9；附录 H4 另开 SPEC |

**收尾（可背）：**  
**权威在轨 A + 人闸；Assist 可证伪；中继诚实到 A2/A3；Live + 双剖面 + Integration-Ready；未宣称 A5 / grounded / 面试条 9 / 生产自动出款。**

---

## 追问卡片（别一次倒完）

| 对方问 | 你答到哪停 | 证据指针 |
|--------|------------|----------|
| 无云怎么演示？ | 无 Key 地板：登录、SC、人闸、AI 降级；`pytest -q` 仍绿 | USER_GUIDE §3.1 / N3 |
| 有 Key 呢？ | Live 分支：真 Assist + 连接双绿；仍过人闸与三联门 | §3.14 / `live-pilot-g0.md` |
| Pilot 满配要什么？ | LLM + **独立** embedding Key + LangSmith；套餐 L 人工验收，不进默认 pytest | §3.2 |
| 检索分呢？ | **先剖面后数字**；demo 基线 ≠ 语义满分 | N11 / §3.6 |
| 金标呢？ | 钩子 + 薄切片协议；H4 deferred；**不得**称 ≥300 运营 | W2 / H4 |
| 为什么不做秒赔？ | 责任争议案禁止该叙事；对外拒赔须人闸与可申诉 | PRD Won't |
| 下一步工程？ | 不是切 Q-A7；H4 须真双标才解锁 grounded | SPEC-02C 附录 |

---

## 不要说的话

- 「全自动核赔 / AI 拒赔 / 已打款」  
- 「A5 Production latch 已完成」  
- 「召回 1.00 所以合门禁」 / 「无剖面标签的语义满分」  
- 「已 grounded / 已冲面试条 9」  
- 「已接核心 / 生产 OCR 已上线」（Ready ≠ Deployed）  
- 「Frontier 空所以做完了」  
- 把作业壳叫成「自动核赔台」或把 Missions 品牌当对外产品名  
- 把 Demo 检索种子叫成金标

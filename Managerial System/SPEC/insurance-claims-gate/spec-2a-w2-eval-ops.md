# Spec — Phase 2a · W2 Eval Ops

| 字段 | 内容 |
|------|------|
| feature_slug | `insurance-claims-gate` |
| spec_id | `SPEC-02A-W2-EVAL-OPS` |
| wave | `W2` |
| Status | `closed` |
| 父索引 | [`spec-2a-runnable-product-floor.md`](./spec-2a-runnable-product-floor.md) |
| 前置 | [`spec-2a-w1-pilot-complete.md`](./spec-2a-w1-pilot-complete.md) DoD 已关闭；W0 仍成立 |
| 主测试接缝 | **S0** 合门禁不变；**S2** 评测台 API/页面契约（不进默认绿） |
| 术语 | `CONTEXT.md`；**金标**定义不变（人工双标），本波只做评测台外形与协作，不假装已有 ≥300 金标运营 |

**继承：** W0+W1；本 SPEC **仅**定义 Eval Ops 产品化增量。

---

## Problem Statement

W1 已能在 LangSmith 看到单次/历史实验对比，但评测仍偏「开发者脚本」：缺少**排行榜**与**多人协作**外形，团队无法像标准 LLM Ops 台一样比较多实验、分配评测任务。需要在**不让评测分数替代 machine_check、不阻塞轨 A CI** 的前提下，把 OpenEval 使用面做成可协作的 Eval Ops。

## Solution

在 W1 之上交付 **W2 Eval Ops**：

- OpenEval 数据集实验结果的**排行榜**（按实验/模型/提示版本可排序对比）  
- **多人协作**评测外形（至少：多本地用户认领评测跑次、查看他人结果；协作模型在实现票写清）  
- 与未来金标运营的**接口预留**（导入/导出数据集、关联 case_id）；全量 ≥300 人工金标运营仍属 PRD 延后，不阻塞本波外形  

## DoD Checklist（W2）

- [x] W0 + W1 DoD 仍成立  
- [x] 排行榜：至少展示实验名、主指标、时间、提交者；可按指标排序  
- [x] 多人：≥2 个演示用户可分别触发/查看评测跑次且结果隔离或可过滤  
- [x] 评测跑次仍经 OpenEval 旁路 + LangSmith（或明确降级说明）；**永不**写入默认 `pytest -q` 必过条件  
- [x] 文档明确：排行榜分数 ≠ 条款门禁合门禁；machine_check 仍是合规主缝  
- [x] `docs/user/` 增加 Eval Ops 操作说明（Preview）  
- [x] 金标全量运营未完成时不得在文案中宣称「金标已达标」  

## User Stories

1. As an Eval Owner, I want 看到多实验排行榜, so that 我能比较提示与模型版本。  
2. As an Eval Owner, I want 按主指标排序与筛选, so that 快速找到回归。  
3. As an adjuster-evaluator, I want 用自己的登录触发评测跑次, so that 贡献可归因。  
4. As a supervisor-evaluator, I want 查看他人跑次而不覆盖我的实验, so that 协作不互相踩。  
5. As a 金标 Owner, I want 数据集导出/导入钩子预留 case_id, so that 将来接人工金标。  
6. As a CI Owner, I want 排行榜与多人评测失败不影响轨 A 绿, so that 合门禁稳定。  
7. As a 内审风控, I want 文案区分「评测分」与「machine_check 通过」, so that 不被分数冒充合规。  
8. As a Demo 讲解人, I want 用两账号演示协作跑榜, so that Eval Ops 可验收。  
9. As a 开发者, I want 优先改写 OPENEVALS + EVAL-ADVISOR 的 LangSmith 实验外形, so that 少造轮子。  
10. As a 产品经理, I want W2 完成仍不宣称 ≥300 金标运营已完成, so that 诚实自治。  
11. As a 核赔员, I want 评测台入口与作业壳门禁主路径视觉分离, so that 不把评测当核赔终裁台。  
12. As a 文档维护者, I want CHANGELOG 标明 Eval Ops Preview, so that 用户预期正确。

## Reference Projects

| 能力 | ref_id / 依赖 | 外链 |
|------|---------------|------|
| OpenEvals | `REF-CASE-OPENEVALS` | https://github.com/langchain-ai/openevals |
| LangSmith 实验/对比 | `REF-CASE-EVAL-ADVISOR` | https://www.langchain.com/langsmith/evaluation · https://docs.smith.langchain.com/ |
| 抽检占位延续 | Issues 11 合成表思路 | — |
| 可观测对照 | `REF-CASE-LANGFUSE` | https://github.com/langfuse/langfuse |
| 中继（勿替） | `REF-MISSIONS` | — |

2026 热门评测台（Braintrust / Phoenix 等）仅作产品对照，**不**强制换栈；本波绑定既有 LangSmith+OpenEvals 选择。

## Implementation Decisions

1. **Blocked by W1：** 无 W1 LangSmith+OpenEval 历史对比则不得宣称 W2 Complete。  
2. **排行榜数据源：** LangSmith 实验 API 与/或本地评测结果表（SQLite）；实现票选定单一真源并文档化。  
3. **多人模型（默认）：** 复用 W0 RBAC 用户；评测跑次记录 `actor_user_id`；不做企业租户。若需更强协作，另开票说明。  
4. **入口：** 作业壳独立「评测」导航或子路由；禁止在 evaluate 主按钮背后隐藏跑榜。  
5. **S2 only：** 任何「榜上分数阈值」不得成为 S0 machine_check 条件。  
6. **金标：** 预留字段/API 即可；不实现双人标注工作流全量。  

## Testing Decisions

1. S0 全量回归保持绿。  
2. API/页面契约：两用户创建跑次 → 排行榜可见两条；排序稳定。  
3. 故意失败的评测跑次不得导致默认 CI 红。  
4. 好测试：外部可观察的榜行字段与权限过滤；不测 LangSmith 专有前端。  

## Out of Scope（本 W2）

- ≥300 人工金标双标运营与周回归达标宣传  
- 更换主观测栈为 Braintrust/Phoenix（可文档对照）  
- L3、真 L2、真 OCR  
- 修改 `spec.md`；用评测分替代人闸  
- 消费 N* 修宪扩面（另案）  

## Further Notes

- 切票：`Managerial System/Issues/insurance-claims-gate/phase2a-w2/`（**29–33** 已切），票首 `wave: W2`；波次门禁为 W1 关闭票 **28**。  
- Phase 2a 愿景在 W2 DoD 关闭后可称「2a Eval Ops 已交付」，仍须诚实标注金标运营延后项。  
- 与 `spec.md` P2-1（金标全量）关系：本波是**外形与协作**，不是 P2-1 关闭。  

## Comments

- 2026-09-14：按波次拆分独立 SPEC；Status=`ready-for-agent`。
- 2026-09-14：to-tickets 批准 defaults；Issues 29–33 落盘 `phase2a-w2/`。
- 2026-09-15：Issue 33 收口；DoD Checklist 全部勾选；Status=`closed`（实现侧）。`Rewrote from: REF-MISSIONS`。

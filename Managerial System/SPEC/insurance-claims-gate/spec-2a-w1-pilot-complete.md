# Spec — Phase 2a · W1 Pilot Complete

| 字段 | 内容 |
|------|------|
| feature_slug | `insurance-claims-gate` |
| spec_id | `SPEC-02A-W1-PILOT-COMPLETE` |
| wave | `W1` |
| Status | `ready-for-agent` |
| 父索引 | [`spec-2a-runnable-product-floor.md`](./spec-2a-runnable-product-floor.md) |
| 前置 | [`spec-2a-w0-dev-complete.md`](./spec-2a-w0-dev-complete.md) DoD 已关闭（或书面豁免项列出）；[`spec.md`](./spec.md) 决策 16–18 有效 |
| 后继 | [`spec-2a-w2-eval-ops.md`](./spec-2a-w2-eval-ops.md) |
| 主测试接缝 | **S0** 仍为合门禁；**S2** 混合检索/真 LLM/LangSmith/OpenEval 旁路（不进默认绿） |
| 术语 | `CONTEXT.md` |

**继承：** W0 全部能力；本 SPEC **仅**定义 Pilot 增量。

---

## Problem Statement

W0 已能本地演示作业壳与规则门禁，但试点仍缺少：**语义+关键词混合检索**、**真实 LangSmith 可观测**，以及 **OpenEval 结果进入 LangSmith 实验/历史对比**。没有这些，无法向试点方证明「AI 辅助路径可追踪、可评测」，同时仍须保证轨 A 绿门与无 Key 降级。

## Solution

在 W0 之上交付 **W1 Pilot Complete**：

- **Chroma** 向量库 + 默认本地 embedding（兼支持云 embedding）  
- **混合检索（仅 AI 路径）：** 硬过滤 → 条款号短路或并行关键词+向量 → 默认权重 0.7/0.3（可配置）→ citation 三联门  
- 向量不可用 → 自动关键词降级；规则 evaluate 不依赖向量  
- **真实 LangSmith** 上报 evaluate / assist / latch 等 span  
- **OpenEval** 旁路跑通，实验结果在 LangSmith **可见且可历史对比**  
- 完工录像套餐 L（满配 + 关向量 + 关 LLM）  

## DoD Checklist（W1）

- [ ] W0 DoD 仍成立  
- [ ] Chroma 索引条款 KB（或约定子集）可重建  
- [ ] 混合检索挂在 assist 路径；规则路径零向量依赖  
- [ ] `keyword_weight`/`vector_weight` 可配置，默认 0.7/0.3  
- [ ] 条款号/clause_item 查询关键词短路  
- [ ] 提名过 doc+clause_item+version 门方可作可采纳引用  
- [ ] 向量故障降级可测  
- [ ] LangSmith Key 配置后关键操作有 trace  
- [ ] OpenEval 跑通且 LangSmith 可做实验历史对比  
- [ ] 套餐 L 录像/清单完成  
- [ ] 默认 `pytest -q` 仍不要求 LangSmith/LLM  
- [ ] `docs/user/` 标明 Pilot 配置要求（与 W0 演示降级区分）  

## User Stories

1. As an AI 辅助路径, I want 效力栈/版本硬过滤后再检索, so that 过期条款不进入提名。  
2. As an AI 辅助路径, I want 含条款号的查询走关键词短路, so that 法律定位优先。  
3. As an AI 辅助路径, I want 并行关键词与 Chroma 向量并按可配置权重融合, so that 混合检索可试点。  
4. As an AI 辅助路径, I want 提名必须过 citation 三联门, so that 检索结果不等于合法引用。  
5. As a 运维, I want 向量不可用时自动关键词降级并提示, so that Pilot 可降级。  
6. As a 规则引擎, I want evaluate 永不依赖 Chroma, so that 轨 A 稳定。  
7. As a 试点负责人, I want LangSmith 看到 evaluate/assist/latch trace, so that 行为可观测。  
8. As an Eval Owner, I want OpenEval 结果写入 LangSmith 实验并做历史对比, so that 提示/模型迭代可比较。  
9. As a Demo 讲解人, I want 按套餐 L 演示满配与双降级, so that Pilot Complete 可验收。  
10. As a 开发者, I want 本地默认 embedding 且可选云 embedding, so that 无云也能建索引。  
11. As a CI Owner, I want 混合检索/LangSmith 测试在 S2 标记下可选, so that 默认绿门不绑云。  
12. As a 内审风控, I want ledger 含 retrieval_profile 与 trace_id（若有）, so that 事后可对上 LangSmith。  
13. As a 核赔员, I want 作业壳 AI 区展示检索来源摘要（doc/条款项）, so that 辅助建议可解释。  
14. As a 文档维护者, I want USER_GUIDE 区分「演示可无 Key」与「Pilot 须 LangSmith」, so that 完工标准不混。  
15. As a coding agent, I want 先改写 RECALL/RAG-CY/EVAL-ADVISOR/OPENEVALS, so that 不从零造观测与检索。

## Reference Projects

| 能力 | ref_id / 依赖 | 外链 |
|------|---------------|------|
| 混合召回 | `REF-CASE-RECALL` | — |
| RAG 骨架 | `REF-RAG-CY` | — |
| 规则+模型 | `REF-CASE-HYBRID` | — |
| OpenEvals | `REF-CASE-OPENEVALS` | https://github.com/langchain-ai/openevals |
| LangSmith 外形 | `REF-CASE-EVAL-ADVISOR` | https://docs.smith.langchain.com/ · https://www.langchain.com/langsmith/evaluation |
| 可观测对照 | `REF-CASE-LANGFUSE` | https://github.com/langfuse/langfuse |
| 向量库 | 依赖级 | https://github.com/chroma-core/chroma |
| 中继合门禁 | `REF-MISSIONS` | — |

禁止：Dify 替门禁；OpenEval 替代 machine_check；默认 CI 调真 LLM。

## Implementation Decisions

1. **Blocked by W0：** 实现票须声明 W0 已满足或豁免列表。  
2. **检索仅 assist 路径；** evaluate 确定性逻辑不变。  
3. **融合：** 线性加权默认 0.7/0.3；配置项写入 `.env.example`；精确条款号短路优先于加权。  
4. **Chroma** 持久目录在项目数据区；提供 rebuild 命令/脚本。  
5. **LangSmith：** W0 本地 exporter 可保留作 fallback；W1 Complete **要求**真上报成功可验证。  
6. **OpenEval↔LangSmith：** 最小为数据集 run + 实验历史对比；**不含**排行榜与多人（W2）。  
7. **S2 测试：** `track_llm_optional`、可选 `langsmith_integration` 等标记；默认 addopts 排除。  

## Testing Decisions

1. S0 回归不得因 W1 依赖变红。  
2. S2：混合检索单元/API 测可用假 embedding；真 LangSmith 测需 Key 或官方 mock 策略（若用 mock须在票中写明，不得冒充 Pilot Complete）。  
3. 套餐 L 为验收清单，不强制进入默认 pytest。  
4. 好测试：断言 assist 返回的 citation 候选均能过三联门或被标记不可采纳；向量关闭时行为降级。  

## Out of Scope（本 W1）

- OpenEval 排行榜、多人协作评测台（W2）  
- ≥300 人工金标运营  
- 用 LangSmith UI 作为合门禁  
- 修改 `spec.md`；放松 I1–I8  

## Further Notes

- 切票：`Managerial System/Issues/insurance-claims-gate/phase2a-w1/`（**23–28** 已切），票首 `wave: W1`；波次门禁为 W0 关闭票 **22**。  
- Pilot Complete ≠ Eval Ops；对外宣称须带波次名。  

## Comments

- 2026-09-14：按波次拆分独立 SPEC；Status=`ready-for-agent`。
- 2026-09-14：to-tickets 批准 defaults；Issues 23–28 落盘 `phase2a-w1/`。

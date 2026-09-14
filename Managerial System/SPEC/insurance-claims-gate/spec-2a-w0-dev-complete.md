# Spec — Phase 2a · W0 Dev Complete

| 字段 | 内容 |
|------|------|
| feature_slug | `insurance-claims-gate` |
| spec_id | `SPEC-02A-W0-DEV-COMPLETE` |
| wave | `W0` |
| Status | `closed`（W0 DoD 已勾选；实现侧 Issues 14–22） |
| 父索引 | [`spec-2a-runnable-product-floor.md`](./spec-2a-runnable-product-floor.md) |
| 前置 | 同目录 [`spec.md`](./spec.md) 轨 A 门禁已落地（Issues 01–13）；**不修改** `spec.md` |
| 后继 | [`spec-2a-w1-pilot-complete.md`](./spec-2a-w1-pilot-complete.md)（W0 DoD 关闭后方可宣称开 W1 实现为主路径） |
| 主测试接缝 | **S0** HTTP + `machine_check`；**S1** 登录/RBAC/assist/adopt（同 HTTP 面） |
| 术语 | `CONTEXT.md`（作业壳、裁决草案、AI 辅助建议、人闸令牌、条款门禁） |

**继承：** `spec.md` 决策 16–18、Testing #7 全部有效。本 SPEC **仅**定义 W0 范围。

---

## Problem Statement

条款门禁已有可回归的 HTTP API 与轨 A 机检，但核赔员仍无法在浏览器里完成作业：无作业壳、无持久化、无角色差、LLM 辅助为空实现。开发者与演示受众需要一个**无云账号也能跑通**的 Dev Complete 地板——能登录、能走 SC、能看 AI 降级提示——同时不把 LLM 或 LangSmith 塞进默认绿门。

## Solution

交付 **W0 Dev Complete**：

- Vite+React+TS **作业壳**（套餐 C），只调现有/扩展后的理赔 HTTP API  
- **SQLite** 持久化案件域 + 种子 **RBAC**（viewer / adjuster / supervisor）  
- **OpenAI-compatible AI 辅助建议**（有 Key 可调用；无 Key 明确降级）；采纳须再过规则 evaluate  
- AI 路径仅用**关键词检索**提名（向量留给 W1）  
- **本地 trace** 文件；不要求真 LangSmith  
- 默认 `pytest -q` 在无 LLM / 无 LangSmith 下全绿  

## DoD Checklist（W0）

- [x] 作业壳：登录、案件列表/详情、材料与一次补件、规则评估、裁决草案、人闸、文书分态、AI 辅助建议区、本案流水  
- [x] SQLite：案件、材料、草案、人闸事件、ledger 摘要、用户与角色  
- [x] RBAC：仅 supervisor 批对外通知 / 出款就绪类人闸；adjuster 不可批；viewer 只读  
- [x] `.env.example` 含 LLM 键；无 Key 时 SC-01/02/03 规则路径可点完  
- [x] assist API：不写 `payout_ready`、不签发人闸令牌  
- [x] 关键词检索可用于 assist 提名（可选最小实现）  
- [x] 本地 trace 导出  
- [x] `pytest -q` 绿（S0；含 RBAC 负例）  
- [x] `docs/user/` 更新启动与诚实 Preview 标注  

## User Stories

1. As a 核赔主管, I want 浏览器登录作业壳, so that 无需 curl 即可作业。  
2. As a viewer, I want 只读案件与草案, so that 不能误批人闸。  
3. As an adjuster, I want 材料登记、evaluate、一次补件, so that 完成初审。  
4. As an adjuster, I want 批人闸被 API/UI 拒绝, so that 权限差可演示。  
5. As a supervisor, I want 批准/驳回人闸并获令牌, so that 应闸类型受控。  
6. As an adjuster, I want 重启后仍能看到 SQLite 中的案件, so that 演示可续。  
7. As an adjuster, I want 看到 gate_status、document_status、inference_track、payout_ready, so that 门禁态可读。  
8. As an adjuster, I want SC-01/02/03 在壳内与 machine_check 语义一致, so that UI 不另立规则。  
9. As a supervisor, I want 拒赔 DRAFT 可预览、EXTERNAL_NOTIFY 无人闸失败且 UI 不假成功, so that 文书分态成立。  
10. As an adjuster, I want 显式点「AI 辅助建议」, so that 不静默调模型。  
11. As an adjuster, I want 无 LLM Key 时看到降级提示且规则路径可用, so that W0 可演示。  
12. As an adjuster, I want 采纳辅助建议必须再过规则校验, so that AI 不能直接写裁决草案权威字段。  
13. As a 内审风控, I want AI/OCR 文本不能签发人闸或改 latch 规则, so that 注入无法提权。  
14. As a Demo 讲解人, I want 本案流水可查看, so that 操作可回放。  
15. As a 消保负责人, I want UI 标明裁决辅助非终裁, so that 无秒赔误导。  
16. As a 开发者, I want OpenAI-compatible 环境变量, so that 可接云或本地兼容端点。  
17. As a 开发者, I want 本地 trace 文件, so that 无 LangSmith 也能排障。  
18. As a CI Owner, I want 默认 pytest 不要求 LLM/LangSmith, so that 合门禁可重复。  
19. As a Validator, I want 继续用 machine_check 验收门禁, so that 前端不是合规真源。  
20. As a 文档维护者, I want USER_GUIDE/CHANGELOG 记录 W0 能力, so that 手册诚实。

## Reference Projects

| 能力 | ref_id / 依赖 | 外链 |
|------|---------------|------|
| 中继/API/machine_check | `REF-MISSIONS` | — |
| 结构化输出 / LLM 客户端外形 | `REF-COURSE-03` | https://github.com/openai/openai-python |
| 规则+模型分治 | `REF-CASE-HYBRID` | — |
| 作业流 | `REF-COURSE-04` | — |
| 关键词/检索起步 | `REF-RAG-CY`、`REF-CASE-RECALL`（可先只用关键词子集） | — |
| 本地推理（可选） | 依赖级 | https://github.com/ollama/ollama |

`Rewrote from: REF-…`；禁 Dify/Langflow 替门禁。

## Implementation Decisions

1. **范围边界：** 不含 Chroma 向量融合、真 LangSmith、OpenEval 排行榜/多人（属 W1/W2）。  
2. **S0 主缝不变；** S1 扩展登录、RBAC、`POST .../assist`、adopt→evaluate。  
3. **作业壳：** Vite+React+TS；无 BFF；错误原样展示 API 拒绝。  
4. **SQLite** 为 W0 默认存储；种子三用户。  
5. **assist：** 实现真实 OpenAI-compatible 调用；替换空 `_maybe_llm_draft`；无 Key 返回 `(None/降级, used_llm=false)`。  
6. **采纳：** 唯有过规则门后才更新裁决草案；`inference_track` 可标 `llm_optional`。  
7. **检索（W0）：** 关键词/既有 KB resolve 即可；接口预留 retrieval 画像字段以便 W1。  
8. **Trace：** 本地 JSONL/文件 span；配置位预留 LangSmith 但不强制。  
9. **代码根：** `本项目代码/claims-gate/`。  

## Testing Decisions

1. 只测 HTTP/可观察行为与壳对 API 错误的诚实展示（可选极少冒烟，不进默认绿）。  
2. S0：SC-01/02/03 + 拆轮补件 + citation + EXTERNAL 无人闸失败 + **RBAC 人闸拒绝**。  
3. S1：无 Key assist 降级；有 Key 时可测（标记隔离，默认 CI 可不跑真调用）。  
4. 默认 CI 缺 LLM/LangSmith 仍必须绿。  

## Out of Scope（本 W0）

- Chroma / 向量混合 / 云 embedding 必选  
- 真 LangSmith Key 作为完工条件  
- OpenEval 历史对比、排行榜、多人协作  
- L3 出款、真 L2、真 OCR、≥300 金标运营  
- 修改 `spec.md`  

## Further Notes

- 切票：`Managerial System/Issues/insurance-claims-gate/phase2a-w0/`（**14–22** 已切），票首 `wave: W0`。  
- 父索引与评委会：见 `spec-2a-runnable-product-floor.md`、`docs/agents/phase2a-sv-expert-panel-review.DRAFT.md`。  
- W0 关闭后方可将实现重心转到 W1 SPEC（票落入 `phase2a-w1/`）。  

## Comments

- 2026-09-14：按波次拆分独立 SPEC；Status=`ready-for-agent`。
- 2026-09-14：to-tickets 批准 defaults；Issues 14–22 落盘 `phase2a-w0/`。
- 2026-09-14：Issue 22 确认默认 `pytest -q` 绿（123 passed / 8 deselected，无 LLM/LangSmith）并同步 `docs/user/`；DoD Checklist 全部勾选；Status=`closed`。

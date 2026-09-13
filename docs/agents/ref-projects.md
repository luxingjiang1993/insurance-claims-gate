# 参考项目目录（REF_*）

供 coding agent **只读改写**，避免重复造轮子。所有路径相对于仓库根下的 `历史项目代码供参考/`。  
**禁止**把参考仓当作交付写入；交付只写入 `本项目代码/claims-gate/`。

| ref_id | 文件夹名 | 改写用途（一句话） | 对本切片优先级 |
|--------|----------|--------------------|----------------|
| `REF-MISSIONS` | `project 多agent` | Missions 中继（Orchestrator/Worker/Validator）、validation contract、`machine_check`、人闸、Mission Control、schemas、FinTech→换域样板 | **P0 主基线** |
| `REF-COURSE-03` | `03_单次模型请求与结构化输出控制` | JSON/结构化输出与 schema 约束 | P1（契约/裁决外形） |
| `REF-COURSE-04` | `04_多步流程编排与条件分支` | 多步编排与条件分支 | P1（作业流/状态机） |
| `REF-COURSE-05` | `05_实战_科技新闻简报` | 端到端实战编排参考 | P2 |
| `REF-COURSE-11` | `11_实战课：接入IM的旅游规划Agent` | 工具型 Agent 与会话编排 | P2 |
| `REF-COURSE-12` | `12_模型驱动的决策模式及复杂回路设计（上）` | 决策模式与复杂回路（Router/仲裁可参考） | P1 |
| `REF-RAG-CY` | `RAG-cy` | RAG 应用骨架（检索+生成） | P1（轨 B / KB 检索） |
| `REF-CASE-RECALL` | `CASE-高效召回` | FAISS/混合检索/召回优化 | P1 |
| `REF-CASE-RERANK` | `CASE-rerank` | 重排序 | P2 |
| `REF-CASE-KB` | `CASE-知识库处理` | 知识库切块、健康检查、版本化处理 | P1（条款 KB） |
| `REF-OPENMANUS-RAG` | `OpenManus-rag` | OpenManus + RAG 集成 | P2（非主中继） |
| `REF-OPENMANUS-CY` | `OpenManus-cy` | OpenManus 通用 Agent 框架 | P2（勿替代 Missions） |
| `REF-OPENMANUS-GUI` | `OpenManus-gui` | GUI/浏览器自动化 | P2（本期非目标） |
| `REF-CASE-FC` | `CASE-Function Calling` | Function Calling / 工具调用模式 | P1（工具 ACL 外形） |
| `REF-CASE-MCP` | `CASE-MCP` | MCP 工具接入 | P2 |
| `REF-CASE-OPENEVALS` | `CASE-openevals使用` | 评估器 / eval 模式 | P1（回归与负例） |
| `REF-CASE-LANGFUSE` | `CASE-langfuse使用` | 追踪与可观测 | P2（ledger 之外） |
| `REF-CASE-HYBRID` | `CASE-投顾AI助手（混合式）` | 混合式 Agent（规则+模型） | P1（轨 A/B 分治灵感） |
| `REF-CASE-EVAL-ADVISOR` | `CASE-投顾AI助手（效果评估）` | 效果评估与评测流水线 | P1（金标入口） |
| `REF-CASE-DELIBERATIVE` | `CASE-智能投研助手（深思熟虑）` | 深思熟虑 / 多步推理回路 | P2（轨 B） |
| `REF-CASE-REACTIVE-QA` | `CASE-私募基金运作指引问答助手（反应式）` | 反应式条款/指引问答 | P2（条款问答，非门禁主链） |
| `REF-CASE-DAYTONA` | `CASE-daytona使用` | 沙箱执行 | P2 |
| `REF-CASE-GUI-PLUS` | `CASE-gui-plus使用` | GUI-plus 自动化 | P2（本期非目标） |

## 使用规则（给 agent）

1. 实现某模块前，先查 SPEC / Issues 上的 `ref_id`，打开对应文件夹只读理解，再改写到 `本项目代码/claims-gate/`。  
2. **默认从 `REF-MISSIONS` 裁剪**；其他 REF 只补能力缺口，不要另起一套三角色剧场。  
3. 在 handoff / ticket 中写：`Rewrote from: REF-xxx`（可多选）。  
4. 文件夹名以本表为准；`ref_id` 稳定，勿用中文路径当 ID。

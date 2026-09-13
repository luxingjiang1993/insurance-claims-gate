# 参考项目目录（REF_*）

供 coding agent **只读改写**，避免重复造轮子。所有路径相对于仓库根下的 `历史项目代码供参考/`。  
**禁止**把参考仓当作交付写入；交付只写入 `本项目代码/claims-gate/`。

**扩面 / 第二阶段（草案）：** 见 [`ref-projects-phase2-supplement.md`](./ref-projects-phase2-supplement.md)。正式修宪前不得按该草案放松 I1–I8。

**评审依据：** 硅谷技术合成评委会（2026-09-13）对「当前剩余 vs 扩面」分类的终稿建议（均分 8.2）；清单一通过、清单二有条件通过。

---

## 全量目录

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
| `REF-CASE-MCP` | `CASE-MCP` | MCP 工具接入 | P2（与 FastMCP 外形二选一补缺口） |
| `REF-CASE-OPENEVALS` | `CASE-openevals使用` | 评估器 / eval 模式 | P1（回归与负例） |
| `REF-CASE-LANGFUSE` | `CASE-langfuse使用` | 追踪与可观测 | P2（ledger 之外） |
| `REF-CASE-HYBRID` | `CASE-投顾AI助手（混合式）` | 混合式 Agent（规则+模型） | P1（轨 A/B 分治灵感） |
| `REF-CASE-EVAL-ADVISOR` | `CASE-投顾AI助手（效果评估）` | 效果评估与评测流水线 | P1（金标入口） |
| `REF-CASE-DELIBERATIVE` | `CASE-智能投研助手（深思熟虑）` | 深思熟虑 / 多步推理回路 | P2（轨 B） |
| `REF-CASE-REACTIVE-QA` | `CASE-私募基金运作指引问答助手（反应式）` | 反应式条款/指引问答 | P2（条款问答，非门禁主链） |
| `REF-CASE-DAYTONA` | `CASE-daytona使用` | 沙箱执行 | P2 |
| `REF-CASE-GUI-PLUS` | `CASE-gui-plus使用` | GUI-plus 自动化 | P2（本期非目标） |

---

## Issues 01–09 已占用（勿另开重复改写票）

下列 `ref_id` 已写入 `Managerial System/Issues/insurance-claims-gate/01`–`09` 的 `ref_id:` / `Rewrote from:`。实现时跟票执行即可，**不要**再为「同一主改写路径」切平行票。

| ref_id | 占用票 |
|--------|--------|
| `REF-MISSIONS` | 01–09（主基线；各票均含或合门禁依赖） |
| `REF-COURSE-03` | 03 |
| `REF-CASE-KB` | 02、05 |
| `REF-COURSE-04` | 05 |
| `REF-COURSE-12` | 07 |
| `REF-CASE-HYBRID` | 07、09 |
| `REF-CASE-FC` | 08 |

---

## 本期仍可供改写（清单一 · 评委会通过）

**口径：** 仍属本 SPEC；现行 I1–I8 全生效；**已占用除外**。  
**入库上限（P0）：** 本期新增改写消费至多覆盖下表「允许」列；`REF-CASE-MCP` 与外部 FastMCP **外形二选一**，勿双开。

| 候选 | 状态 | 可补缺口 | 建议用法 |
|------|------|----------|----------|
| `REF-RAG-CY` | 允许 | 轨 B 检索+生成；强化 Issue 09 占位 | 只读补 09 或另开「轨 B 最小检索」；**不得进轨 A CI** |
| `REF-CASE-RECALL` | 允许 | 混合召回；检索画像质量 | 挂轨 B 或独立检索票；证明不破坏效力栈 |
| `REF-CASE-OPENEVALS` | 允许 | 评估器 / 负例入口 | 新票：机检负例与 eval 外形；不替代 `machine_check` |
| `REF-CASE-EVAL-ADVISOR` | 允许 | 金标 / Judge–human 抽检占位（P1-7） | 新票；不阻塞轨 A 绿门 |
| `REF-CASE-MCP` **或** FastMCP 外形 | 允许（二选一） | 工具协议 / 异步工具 ACL | 仅当要显式 MCP 工具面时；对照改写即可，FastMCP **不必整仓入库** |

**本期明确不要新开改写票：** `REF-OPENMANUS-*` 作主中继、Browser Use / GUI、SWE-agent / Aider 进产品域、llama.cpp / vLLM / Ollama 当业务改写源、E2B、微调栈、CrewAI / AgentScope 主编排、RAGFlow / Letta / LightRAG 整仓、Dify 主链。

---

## 协议阅读（非改写列 · 评委会降级）

下列公开项目或能力**仅作协议 / schema 阅读**，不得升为 `REF_*` 主改写源，也不得切「整仓裁剪」票：

| 名称 | 允许用途 | 禁止 |
|------|----------|------|
| Gorilla OpenFunctions | 工具描述 / 多步 API schema 外形灵感 | 入库为 REF；当本切片工具面基线 |
| ToolLLM（含数据集） | 了解工具调用数据形态 | 当合门禁或默认 CI 依赖 |
| mcp-marketplace | 发现层浏览 | 当产品依赖或改写源 |
| 公开「2026 Agent 完整栈」整表 | 选型地图 | 整表升为改写基线 |

---

## 使用规则（给 agent）

1. 实现某模块前，先查 SPEC / Issues 上的 `ref_id`，打开对应文件夹只读理解，再改写到 `本项目代码/claims-gate/`。  
2. **默认从 `REF-MISSIONS` 裁剪**；其他 REF 只补能力缺口，不要另起一套三角色剧场。  
3. 在 handoff / ticket 中写：`Rewrote from: REF-xxx`（可多选）。  
4. 文件夹名以本表为准；`ref_id` 稳定，勿用中文路径当 ID。  
5. 开「本期剩余」新票前核对上文入库上限；扩面候选与 N 标准只读补充文档，**未修宪不得执行放松**。  
6. OpenManus（`REF-OPENMANUS-*`）不得替代 Missions 中继主链。
